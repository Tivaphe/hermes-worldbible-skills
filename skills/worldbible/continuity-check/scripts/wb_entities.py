#!/usr/bin/env python3
"""
wb_entities.py — Verifie les entites nommees d'un texte (chapitre) contre la World Bible.
Script AUTONOME : aucune dependance externe, ni envers les autres skills.

Usage:
    python3 wb_entities.py --draft manuscrit/chapitres/03.md --bible ~/worldbible
    python3 wb_entities.py --draft 03.md --bible ~/worldbible --min-occurrences 2 --json
    python3 wb_entities.py --draft 03.md --index ~/worldbible/.index/index.json

Ce que fait le script (deterministe):
  1. extrait les candidats-entites du brouillon (majuscules, noms composes, guillemets),
  2. pour chacun, cherche dans l'index de la World Bible,
  3. classe: CONNU (trouve, avec preuve) / FAIBLE (mention legere) / INCONNU (absent).

Ce que le script ne fait PAS: juger des contradictions. C'est le role du modele,
a partir des extraits cites en sortie. Ne jamais valider une entite sans preuve citee.

Dependances: bibliotheque standard Python uniquement.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata

STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "et", "ou", "a", "au", "aux",
    "en", "dans", "sur", "sous", "par", "pour", "avec", "sans", "que", "qui", "quoi", "dont",
    "ce", "cet", "cette", "ces", "son", "sa", "ses", "leur", "leurs", "il", "elle", "ils",
    "elles", "on", "nous", "vous", "je", "tu", "est", "sont", "etait", "etaient", "etre",
    "avoir", "fait", "comme", "mais", "donc", "car", "ni", "si", "plus", "moins", "tres",
    "tout", "tous", "toute", "toutes", "aussi", "ainsi", "alors", "puis", "apres", "avant",
    "the", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are",
    "was", "were", "be", "been", "it", "its", "this", "that", "these", "those", "as",
}

NOT_ENTITY = {
    "Je", "Tu", "Il", "Elle", "Nous", "Vous", "Ils", "Elles", "On", "Mais", "Et", "Ou",
    "Donc", "Or", "Ni", "Car", "Si", "Non", "Oui", "Ah", "Oh", "Eh", "Bon", "Alors",
    "Aussi", "Ainsi", "Puis", "Après", "Avant", "Quand", "Comme", "Pourquoi", "Peut",
    "Peut-être", "The", "And", "But", "So", "If", "When", "What", "Why", "How", "Then",
    "Cependant", "Néanmoins", "Pourtant", "Enfin", "Soudain", "Ensuite", "Voici",
    "Voilà", "Merci", "Bonjour", "Salut", "Seigneur", "Madame", "Monsieur", "Chapitre",
    "Partie", "Prologue", "Épilogue", "Livre", "Tome",
}

CAP_WORD = r"[A-ZÀ-Ý][\w'’\-À-ÿ]+"
LEADING_ARTICLES = ("le ", "la ", "les ", "l'", "les ", "the ", "a ", "an ", "du ", "de la ", "des ")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    for a, b in (("\u2019", "'"), ("\u2018", "'"), ("\u02bc", "'"),
                 ("\u00ab", '"'), ("\u00bb", '"'), ("\u201c", '"'), ("\u201d", '"')):
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text)


def chunk_haystack(chunk: dict) -> str:
    if "haystack" in chunk:
        return chunk["haystack"]
    return normalize(" ".join([chunk.get("title", ""), " > ".join(chunk.get("crumbs", [])), chunk.get("text", "")]))


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    return [t for t in re.findall(r"[a-z0-9']{2,}", text, re.UNICODE) if t not in STOPWORDS]


def load_index(path: str) -> dict:
    if not os.path.isfile(path):
        raise SystemExit(
            f"ERREUR: index introuvable: {path}\n"
            "Construisez-le d'abord avec le skill lore-lookup:\n"
            "  python3 wb_index.py --bible <dossier-world-bible>"
        )
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def snippet(text: str, terms: list[str], width: int = 240) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    low = text.lower()
    best_pos, best_hits = 0, -1
    step = max(1, len(text) // 12)
    for start in range(0, max(1, len(text) - width), step):
        window = low[start : start + width]
        hits = sum(window.count(t) for t in terms)
        if hits > best_hits:
            best_hits, best_pos = hits, start
    out = text[best_pos : best_pos + width]
    return ("…" if best_pos > 0 else "") + out + ("…" if best_pos + width < len(text) else "")


def score_chunk(chunk: dict, terms: list[str]) -> tuple[float, int]:
    title_toks = set(tokenize(chunk.get("title", "")))
    crumb_toks = set(tokenize(" ".join(chunk.get("crumbs", []))))
    body_toks = set(chunk.get("tokens", []))
    score, matched = 0.0, 0
    for t in terms:
        hit = False
        if t in title_toks:
            score += 4.0
            hit = True
        if t in crumb_toks:
            score += 2.0
            hit = True
        if t in body_toks:
            score += 1.0
            hit = True
        if hit:
            matched += 1
    if terms:
        score *= 0.35 + 0.65 * (matched / len(terms))
    return score, matched


def strip_code_and_meta(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    # les titres et listes Markdown sont de la structure, pas du recit:
    # sinon "## Notes" ou "- Regles" remontent comme entites inventees
    text = re.sub(r"^\s*#{1,6}\s+.*$", " ", text, flags=re.M)
    text = re.sub(r"^\s*[-*+]\s+", " ", text, flags=re.M)
    return text


def extract_candidates(text: str) -> dict[str, int]:
    text = strip_code_and_meta(text)
    counts: dict[str, int] = {}

    for m in re.finditer(rf"(?:{CAP_WORD} ){{1,3}}{CAP_WORD}", text):
        cand = m.group(0).strip(" ,.;:!?'’\"")
        if len(cand.split()) >= 2:
            counts[cand] = counts.get(cand, 0) + 1

    for m in re.finditer(rf"(?<![\w.!?…\n]){CAP_WORD}", text):
        prev = text[: m.start()].rstrip()
        if prev and prev[-1] in ".!?…:":
            continue
        word = m.group(0).strip(" ,.;:!?'’\"")
        if word in NOT_ENTITY or word.upper() == word or len(word) < 3:
            continue
        counts[word] = counts.get(word, 0) + 1

    for m in re.finditer(r"[«\"“']([^«»\"”']{3,40})[»\"”']", text):
        cand = re.sub(r"\s+", " ", m.group(1)).strip()
        if not cand or cand.endswith((".", ",", "!", "?")):
            continue
        # un nom propre entre guillemets ne contient pas de mot en minuscule
        # (evite de capturer des bribes de dialogue comme « Olm n'en saura rien »)
        if " " in cand and any(w[:1].islower() for w in cand.split() if w):
            continue
        counts[cand] = counts.get(cand, 0) + 1

    for m in re.finditer(r"\b[a-zà-ÿ]+-[a-zà-ÿ]+(?:-[a-zà-ÿ]+)?\b", text):
        counts.setdefault(m.group(0), 0)
        counts[m.group(0)] += 1

    cleaned: dict[str, int] = {}
    multi = [c for c in counts if len(c.split()) >= 2]
    for cand, n in counts.items():
        toks = tokenize(cand)
        if not toks or all(t in STOPWORDS for t in toks) or cand in NOT_ENTITY:
            continue
        # un mot simple deja porte par un nom compose complet -> on garde le nom compose
        if " " not in cand and any(cand in m and m != cand for m in multi):
            continue
        cleaned[cand] = n
    return cleaned


def exact_pattern(cand: str) -> str:
    c = normalize(cand).strip()
    for art in LEADING_ARTICLES:
        if c.startswith(art):
            c = c[len(art) :]
            break
    return re.escape(c)


def lookup(cand: str, index: dict) -> list[dict]:
    terms = tokenize(cand)
    if not terms:
        return []
    pat = re.compile(rf"(?<![\w]){exact_pattern(cand)}(?![\w])")
    hits = []
    for chunk in index["chunks"]:
        exact = bool(pat.search(chunk_haystack(chunk)))
        sc, matched = score_chunk(chunk, terms)
        if exact:
            sc += 3.0
            matched = max(matched, 1)
        if matched:
            hits.append({"score": sc, "matched": matched, "exact": exact, "chunk": chunk})
    hits.sort(key=lambda h: (-h["exact"], -h["score"], h["chunk"]["file"]))
    return hits[:3]


def main() -> int:
    ap = argparse.ArgumentParser(description="Controle de continuite: entites d'un brouillon vs World Bible.")
    ap.add_argument("--draft", required=True, help="Fichier du chapitre / brouillon a controler")
    ap.add_argument("--bible", default=None, help="Dossier de la World Bible")
    ap.add_argument("--index", default=None, help="index.json (defaut: <bible>/.index/index.json)")
    ap.add_argument("--min-occurrences", type=int, default=1, help="Ne verifier que les entites vues au moins N fois")
    ap.add_argument("--top", type=int, default=40, help="Nombre max d'entites traitees (defaut 40)")
    ap.add_argument("--json", action="store_true", help="Sortie JSON")
    args = ap.parse_args()

    if args.index:
        idx_path = os.path.expanduser(args.index)
    elif args.bible:
        idx_path = os.path.join(os.path.abspath(os.path.expanduser(args.bible)), ".index", "index.json")
    else:
        raise SystemExit("ERREUR: donnez --bible <dossier> ou --index <index.json>")

    index = load_index(idx_path)
    with open(os.path.expanduser(args.draft), "r", encoding="utf-8", errors="replace") as fh:
        draft = fh.read()

    candidates = extract_candidates(draft)
    ranked = [(c, n) for c, n in sorted(candidates.items(), key=lambda kv: (-kv[1], kv[0])) if n >= args.min_occurrences][: args.top]

    known, weak, unknown = [], [], []
    for cand, occ in ranked:
        hits = lookup(cand, index)
        entry = {"entity": cand, "occurrences": occ}
        if not hits:
            entry["verdict"] = "INCONNU"
            unknown.append(entry)
            continue
        best = hits[0]
        entry["verdict"] = "CONNU" if (best["exact"] or best["score"] >= 2.0) else "FAIBLE"
        entry["evidence"] = [
            {
                "file": h["chunk"]["file"],
                "title": h["chunk"]["title"],
                "crumbs": h["chunk"]["crumbs"],
                "score": round(h["score"], 2),
                "exact": h["exact"],
                "quote": snippet(h["chunk"]["text"], tokenize(cand)),
            }
            for h in hits
        ]
        (known if entry["verdict"] == "CONNU" else weak).append(entry)

    summary = {
        "draft": os.path.abspath(os.path.expanduser(args.draft)),
        "bible_dir": index["bible_dir"],
        "candidates": len(candidates),
        "checked": len(ranked),
        "known": len(known),
        "weak": len(weak),
        "unknown": len(unknown),
    }

    if args.json:
        print(json.dumps({"summary": summary, "known": known, "weak": weak, "unknown": unknown}, ensure_ascii=False, indent=1))
        return 0

    print("=== CONTROLE DE CONTINUITE (entites nommees) ===")
    print(f"brouillon : {summary['draft']}")
    print(f"bible     : {summary['bible_dir']}")
    print(f"candidats : {summary['candidates']} entites extraites, {summary['checked']} verifiees")
    print(f"connues   : {summary['known']} | douteuses : {summary['weak']} | inconnues : {summary['unknown']}\n")

    if unknown:
        print("--- A VERIFIER : absentes de la World Bible (invention ou faute d'orthographe ?) ---")
        for e in unknown:
            print(f"  ? {e['entity']}  (x{e['occurrences']})")
        print()
    if weak:
        print("--- MENTIONS FAIBLES : trouvees, mais source legere ---")
        for e in weak:
            ev = e["evidence"][0]
            print(f"  ~ {e['entity']}  (x{e['occurrences']}) -> {ev['file']} :: {ev['title']}")
        print()
    if known:
        print("--- CONFIRMEES (preuve canonique) ---")
        for e in known[:15]:
            ev = e["evidence"][0]
            print(f"  + {e['entity']}  (x{e['occurrences']}) -> {ev['file']} :: {ev['title']}")
        if len(known) > 15:
            print(f"  ... et {len(known) - 15} autres")
    print()
    print("Etape suivante obligatoire (modele): lire les extraits ci-dessus et juger des")
    print("CONTRADICTIONS. Le script ne detecte que la presence, jamais le sens.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
