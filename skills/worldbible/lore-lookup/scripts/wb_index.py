#!/usr/bin/env python3
"""
wb_index.py — Construit un index JSON d'une World Bible (dossier de fichiers Markdown/txt).

Usage:
    python3 wb_index.py --bible ~/worldbible --out ~/worldbible/.index/index.json
    python3 wb_index.py --bible ~/worldbible                 # index par défaut: <bible>/.index/index.json
    python3 wb_index.py --bible ~/worldbible --stats          # n'imprime que des statistiques

Sortie: un JSON avec, par bloc de texte (découpé sur les titres Markdown),
le chemin du fichier, le fil d'Ariane des titres, le texte et les mots-clés.
Cet index sert ensuite a wb_search.py et wb_entities.py.

Dependances: uniquement la bibliotheque standard Python (3.8+).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone

TEXT_EXT = {".md", ".markdown", ".txt", ".mdx", ".org", ".rst"}
SKIP_DIRS = {".git", ".index", ".obsidian", "node_modules", "__pycache__", ".trash", "exports", "drafts"}

# Mots vides generiques (fr + en) — volontairement court, on garde les termes rares.
STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "et", "ou", "a", "au", "aux",
    "en", "dans", "sur", "sous", "par", "pour", "avec", "sans", "que", "qui", "quoi", "dont",
    "ce", "cet", "cette", "ces", "son", "sa", "ses", "leur", "leurs", "il", "elle", "ils",
    "elles", "on", "nous", "vous", "je", "tu", "est", "sont", "etait", "etaient", "etre",
    "avoir", "fait", "comme", "mais", "donc", "car", "ni", "si", "plus", "moins", "tres",
    "tout", "tous", "toute", "toutes", "aussi", "ainsi", "alors", "puis", "apres", "avant",
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are",
    "was", "were", "be", "been", "it", "its", "this", "that", "these", "those", "as",
}


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def normalize(text: str) -> str:
    """Minuscule + apostrophes/guillemets unifies + espaces compactes (comparaison exacte)."""
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.replace("\u2019", "'").replace("\u2018", "'").replace("\u02bc", "'")
    text = text.replace("\u00ab", '"').replace("\u00bb", '"')
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", text)


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    # re.UNICODE: sans ce drapeau, "minutes" issu de "résine" serait coupe en "min"
    return [t for t in re.findall(r"[a-z0-9']{2,}", text, re.UNICODE) if t not in STOPWORDS]


def iter_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if os.path.splitext(name)[1].lower() in TEXT_EXT:
                yield os.path.join(dirpath, name)


def split_blocks(rel_path: str, text: str) -> list[dict]:
    """Decoupe un fichier en blocs delimites par les titres Markdown (#..######)."""
    lines = text.splitlines()
    blocks: list[dict] = []
    heading_stack: list[str] = []          # fil d'Ariane des titres ouverts
    current: list[str] = []
    current_title = ""
    current_level = 0

    def flush():
        if current_title or current:
            body = "\n".join(current).strip()
            if body or current_title:
                blocks.append(
                    {
                        "file": rel_path,
                        "title": current_title,
                        "crumbs": list(heading_stack),
                        "level": current_level,
                        "text": body,
                    }
                )

    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            flush()
            level = len(m.group(1))
            title = m.group(2).strip()
            heading_stack[:] = heading_stack[: level - 1]
            while len(heading_stack) < level - 1:
                heading_stack.append("")
            heading_stack.append(title)
            current = []
            current_title = title
            current_level = level
        else:
            current.append(line)
    flush()

    # Fichier sans titre : un seul bloc portant le nom du fichier.
    if not blocks:
        body = text.strip()
        blocks.append(
            {
                "file": rel_path,
                "title": os.path.splitext(os.path.basename(rel_path))[0],
                "crumbs": [],
                "level": 0,
                "text": body,
            }
        )
    return blocks


def build(bible_dir: str) -> dict:
    bible_dir = os.path.abspath(os.path.expanduser(bible_dir))
    if not os.path.isdir(bible_dir):
        raise SystemExit(f"ERREUR: dossier World Bible introuvable: {bible_dir}")

    chunks: list[dict] = []
    files_seen = 0
    for path in iter_files(bible_dir):
        rel = os.path.relpath(path, bible_dir)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError as exc:
            print(f"avertissement: lecture impossible de {rel}: {exc}", file=sys.stderr)
            continue
        files_seen += 1
        for blk in split_blocks(rel, text):
            haystack = " ".join([blk["title"], " > ".join(blk["crumbs"]), blk["text"]])
            toks = tokenize(haystack)
            blk["tokens"] = sorted(set(toks))
            blk["haystack"] = normalize(haystack)
            blk["slug"] = slugify(f"{rel}::{blk['title'] or 'root'}")
            blk["words"] = len(blk["text"].split())
            chunks.append(blk)

    return {
        "version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bible_dir": bible_dir,
        "file_count": files_seen,
        "chunk_count": len(chunks),
        "chunks": chunks,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Indexe une World Bible en JSON.")
    ap.add_argument("--bible", required=True, help="Dossier racine de la World Bible")
    ap.add_argument("--out", default=None, help="Chemin du JSON d'index (defaut: <bible>/.index/index.json)")
    ap.add_argument("--stats", action="store_true", help="N'ecrit rien, affiche les statistiques")
    args = ap.parse_args()

    index = build(args.bible)
    out = args.out or os.path.join(index["bible_dir"], ".index", "index.json")

    if args.stats:
        per_file: dict[str, int] = {}
        for c in index["chunks"]:
            per_file[c["file"]] = per_file.get(c["file"], 0) + 1
        print(f"dossier      : {index['bible_dir']}")
        print(f"fichiers     : {index['file_count']}")
        print(f"blocs        : {index['chunk_count']}")
        print(f"mots         : {sum(c['words'] for c in index['chunks'])}")
        for f in sorted(per_file):
            print(f"  {per_file[f]:>4} blocs  {f}")
        return 0

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=1)
    print(f"index ecrit: {out}")
    print(f"  {index['file_count']} fichiers, {index['chunk_count']} blocs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
