#!/usr/bin/env python3
"""
wb_search.py — Recherche plein-texte classee dans l'index d'une World Bible.

Usage:
    python3 wb_search.py "magie du sang" --bible ~/worldbible
    python3 wb_search.py "magie du sang" --bible ~/worldbible -k 5 --context 400
    python3 wb_search.py "magie du sang" --index ~/worldbible/.index/index.json --json

Note de recherche: titre = x4, fil d'Ariane = x2, corps = x1.
Un terme absent du index fait chuter le score (recherche ET logique souple).

Dependances: bibliotheque standard uniquement.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unicodedata  # noqa: E402

from wb_index import STOPWORDS, tokenize  # noqa: E402


def fold(text: str) -> str:
    """Minuscule + suppression des accents, pour comparer extrait et requete."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def default_index(bible_dir: str) -> str:
    return os.path.join(os.path.abspath(os.path.expanduser(bible_dir)), ".index", "index.json")


def load_index(path: str) -> dict:
    if not os.path.isfile(path):
        raise SystemExit(
            f"ERREUR: index introuvable: {path}\n"
            "Construisez-le d'abord:\n"
            "  python3 wb_index.py --bible <dossier-world-bible>"
        )
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def snippet(text: str, terms: list[str], width: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    low = fold(text)
    terms = [fold(t) for t in terms]
    best_pos = 0
    best_hits = -1
    step = max(1, len(text) // 12)
    for start in range(0, max(1, len(text) - width), step):
        window = low[start : start + width]
        hits = sum(window.count(t) for t in terms)
        if hits > best_hits:
            best_hits, best_pos = hits, start
    out = text[best_pos : best_pos + width]
    prefix = "…" if best_pos > 0 else ""
    suffix = "…" if best_pos + width < len(text) else ""
    return f"{prefix}{out}{suffix}"


def score_chunk(chunk: dict, terms: list[str]) -> tuple[float, int]:
    title_toks = set(tokenize(chunk.get("title", "")))
    crumb_toks = set(tokenize(" ".join(chunk.get("crumbs", []))))
    body_toks = set(chunk.get("tokens", []))

    score = 0.0
    matched = 0
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
        # bonus mot compose / prefixe
        if not hit:
            for bt in body_toks:
                if bt.startswith(t) or t.startswith(bt) and len(t) > 4:
                    score += 0.5
                    hit = True
                    break
        if hit:
            matched += 1
    # penalite si des termes manquent (recherche quasi-ET)
    if terms:
        score *= (0.35 + 0.65 * (matched / len(terms)))
    # leger bonus aux blocs courts et denses
    words = chunk.get("words", 0) or 1
    score *= 1.0 + min(0.3, 120.0 / words)
    return score, matched


def main() -> int:
    ap = argparse.ArgumentParser(description="Recherche classee dans une World Bible indexee.")
    ap.add_argument("query", help="Requete (mots-cles)")
    ap.add_argument("--bible", default=None, help="Dossier de la World Bible")
    ap.add_argument("--index", default=None, help="Chemin direct vers index.json")
    ap.add_argument("-k", "--top", type=int, default=6, help="Nombre de resultats (defaut 6)")
    ap.add_argument("--context", type=int, default=320, help="Longueur de l'extrait (defaut 320)")
    ap.add_argument("--min-words", type=int, default=0, help="Filtre: blocs d'au moins N mots")
    ap.add_argument("--json", action="store_true", help="Sortie JSON (pour traitement ulterieur)")
    args = ap.parse_args()

    if not args.index:
        if not args.bible:
            raise SystemExit("ERREUR: donnez --bible <dossier> ou --index <index.json>")
        args.index = default_index(args.bible)

    index = load_index(args.index)
    terms = [t for t in tokenize(args.query)] or [args.query.lower()]

    scored = []
    for chunk in index["chunks"]:
        if chunk.get("words", 0) < args.min_words:
            continue
        sc, matched = score_chunk(chunk, terms)
        if matched:
            scored.append((sc, matched, chunk))
    scored.sort(key=lambda x: (-x[0], x[2]["file"]))

    results = scored[: args.top]
    if args.json:
        payload = [
            {
                "rank": i + 1,
                "score": round(sc, 3),
                "file": c["file"],
                "title": c["title"],
                "crumbs": c["crumbs"],
                "words": c["words"],
                "excerpt": snippet(c["text"], terms, args.context),
            }
            for i, (sc, _m, c) in enumerate(results)
        ]
        print(json.dumps({"query": args.query, "count": len(payload), "results": payload}, ensure_ascii=False, indent=1))
        return 0

    if not results:
        print(f"Aucun resultat pour « {args.query} » dans {index['bible_dir']}")
        print("Pistes: verifier que l'index est a jour (wb_index.py), ou utiliser des termes plus courts/genériques.")
        return 1

    print(f"« {args.query} » — {len(scored)} bloc(s) pertinent(s), {len(results)} affiche(s)")
    print(f"World Bible: {index['bible_dir']}\n")
    for i, (sc, matched, c) in enumerate(results, 1):
        crumbs = " > ".join(x for x in c["crumbs"] if x)
        print(f"[{i}] score {sc:.1f} | {c['file']}")
        print(f"    titre: {c['title'] or '(sans titre)'}" + (f"  [{crumbs}]" if crumbs else ""))
        print(f"    extrait: {snippet(c['text'], terms, args.context)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
