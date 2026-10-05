#!/usr/bin/env python3
"""
wb_manuscript.py — Mesures factuelles d'un manuscrit : mots, chapitres, progression.

Usage:
    python3 wb_manuscript.py manuscrit/chapitres/
    python3 wb_manuscript.py manuscrit/chapitres/ --target-words 90000 --by-part
    python3 wb_manuscript.py manuscrit/chapitres/03.md

Sert a ne JAMAIS estimer une longueur "de tete". Les chiffres affiches viennent
du decompte reel des fichiers.

Dependances: bibliotheque standard uniquement.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime, timezone

TEXT_EXT = {".md", ".markdown", ".txt", ".mdx"}


def clean(text: str) -> str:
    """Retire ce qui n'est pas du texte de narration : frontmatter, commentaires, meta."""
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    # lignes de notes d'auteur en fin de fichier (convention "## Notes")
    text = re.split(r"^##\s+(notes|todo|a faire|idées|idees)\b", text, flags=re.M | re.I)[0]
    return text


def count_words(text: str) -> int:
    return len(re.findall(r"[\w'’À-ÿ\-]+", clean(text)))


def iter_files(target: str) -> list[str]:
    target = os.path.abspath(os.path.expanduser(target))
    if os.path.isfile(target):
        return [target]
    out = []
    for dirpath, dirnames, filenames in os.walk(target):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in sorted(filenames):
            if os.path.splitext(name)[1].lower() in TEXT_EXT:
                out.append(os.path.join(dirpath, name))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Statistiques de manuscrit (mots, chapitres).")
    ap.add_argument("target", help="Dossier de chapitres ou fichier unique")
    ap.add_argument("--target-words", type=int, default=0, help="Objectif de mots (optionnel)")
    ap.add_argument("--by-part", action="store_true", help="Grouper par prefixe de nom (partie/acte)")
    args = ap.parse_args()

    files = iter_files(args.target)
    if not files:
        print(f"Aucun fichier texte trouve dans {args.target}")
        return 1

    rows = []
    for path in files:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        rel = os.path.relpath(path, os.path.dirname(files[0]) or ".")
        title = ""
        m = re.search(r"^#\s+(.+)$", text, flags=re.M)
        if m:
            title = m.group(1).strip()
        rows.append({"file": rel, "title": title, "words": count_words(text)})

    total = sum(r["words"] for r in rows)
    print(f"=== MANUSCRIT : {os.path.abspath(os.path.expanduser(args.target))} ===")
    for r in rows:
        print(f"  {r['words']:>7} mots  {r['file']}" + (f"  — {r['title']}" if r["title"] else ""))
    print(f"\n  fichiers  : {len(rows)}")
    print(f"  TOTAL     : {total} mots")
    print(f"  moyenne   : {total // max(1, len(rows))} mots / chapitre")

    if args.by_part:
        parts: dict[str, int] = {}
        for r in rows:
            key = re.match(r"(\d+)", os.path.basename(r["file"]))
            parts[key.group(1) if key else "?"] = parts.get(key.group(1) if key else "?", 0) + r["words"]
        print("\n  par groupe de fichiers (prefixe numerique):")
        for k in sorted(parts):
            print(f"    {k}: {parts[k]} mots")

    if args.target_words:
        pct = 100.0 * total / args.target_words
        reste = args.target_words - total
        print(f"\n  objectif  : {args.target_words} mots -> {pct:.1f}% atteint, reste {reste} mots")
    print(f"\n  mesure le : {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
