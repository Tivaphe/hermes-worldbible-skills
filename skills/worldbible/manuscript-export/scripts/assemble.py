#!/usr/bin/env python3
"""
assemble.py — Assemble les chapitres d'un manuscrit en un seul fichier Markdown.

Usage:
    python3 assemble.py --chapters <manuscrit>/chapitres --out <manuscrit>/exports/livre.md \
        --title "Titre" --author "Auteur" [--strip-notes]

- ordre = tri alphabetique des noms de fichiers (d'ou les noms 01-, 02-, ... 10-)
- --title/--author sont enregistres comme metadonnees du projet (voir exports/meta.txt),
  ils ne sont PAS ecrits dans le Markdown: c'est l'etape d'export qui pose la page de titre
- --strip-notes retire les sections "## Notes", "## TODO", "## Idées" et le frontmatter
Dependances: bibliotheque standard uniquement.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

TEXT_EXT = {".md", ".markdown", ".txt", ".mdx"}
NOTE_HEAD = re.compile(r"^##\s+(notes?|todo|a faire|id[ée]es|brouillon)\b.*$", re.I | re.M)


def clean(text: str, strip_notes: bool) -> str:
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    if strip_notes:
        m = NOTE_HEAD.search(text)
        if m:
            text = text[: m.start()].rstrip() + "\n"
    return text.rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Assemble un manuscrit en un seul Markdown.")
    ap.add_argument("--chapters", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default=None)
    ap.add_argument("--author", default=None)
    ap.add_argument("--strip-notes", action="store_true")
    args = ap.parse_args()

    src = os.path.abspath(os.path.expanduser(args.chapters))
    files = [f for f in sorted(os.listdir(src)) if os.path.splitext(f)[1].lower() in TEXT_EXT]
    if not files:
        print(f"Aucun fichier chapitre dans {src}")
        return 1

    # NB: on n'ajoute PAS de page de titre ici: le fichier assemble reste du manuscrit brut.
    # Le titre et l'auteur sont passes a l'etape d'export (md_to_docx.py --title/--author,
    # ou --metadata avec pandoc). Les ajouter ici produirait un titre duplique.

    parts = []
    words = 0
    print("assemblage:")
    for f in files:
        with open(os.path.join(src, f), "r", encoding="utf-8", errors="replace") as fh:
            body = clean(fh.read(), args.strip_notes)
        n = len(re.findall(r"[\w'’À-ÿ\-]+", body))
        words += n
        print(f"  {n:>7} mots  {f}")
        parts.append(body)

    out = os.path.abspath(os.path.expanduser(args.out))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n\n---\n\n".join(parts) + "\n")

    meta = os.path.join(os.path.dirname(out), "meta.txt")
    with open(meta, "w", encoding="utf-8") as fh:
        fh.write(f"title: {args.title or ''}\nauthor: {args.author or ''}\nchapters: {len(files)}\nwords: {words}\n")

    print(f"\nfichier : {out}")
    print(f"meta    : {meta}")
    print(f"chapitres: {len(files)} | mots: {words}")
    if any(not re.match(r"^\d{2,}", f) for f in files):
        print("attention: des noms de fichiers ne commencent pas par 2 chiffres -> ordre risqué")
    return 0


if __name__ == "__main__":
    sys.exit(main())
