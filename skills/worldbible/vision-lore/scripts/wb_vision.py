#!/usr/bin/env python3
"""
wb_vision.py — Indexe les visuels d'une World Bible (cartes, portraits, plans, croquis)
et les relie au texte qui les décrit.

Pourquoi : les modeles a vision native (ex. Qwen3.8-27B) peuvent LIRE une carte ou un
portrait. Encore faut-il savoir quel fichier image correspond a quel fait du monde.
C'est ce que fait ce script : il ne decrit pas les images, il les reference.

Usage:
    python3 wb_vision.py --bible ~/worldbible                     # indexe + affiche le tableau
    python3 wb_vision.py --bible ~/worldbible --json              # sortie JSON
    python3 wb_vision.py --bible ~/worldbible --emit-prompt 2     # prompt pret a envoyer
                                                                  # (image n°2 de l'index)
    python3 wb_vision.py --bible ~/worldbible --query "carte"     # filtre par mot-cle

Dependances: bibliotheque standard Python uniquement.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import struct
import sys
import unicodedata
import zlib
from datetime import datetime, timezone

IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
TEXT_EXT = {".md", ".markdown", ".txt", ".mdx"}
SKIP_DIRS = {".git", ".index", ".obsidian", "node_modules", "__pycache__", "exports"}

STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "et", "ou", "a", "au", "aux",
    "en", "dans", "sur", "sous", "par", "pour", "avec", "sans", "que", "qui", "ce",
    "cet", "cette", "ces", "son", "sa", "ses", "il", "elle", "est", "sont", "etre",
    "the", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are", "it", "its",
}


def fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9']{2,}", fold(text), re.UNICODE) if t not in STOPWORDS]


def png_size(path: str) -> tuple[int, int] | None:
    """Lit les dimensions d'un PNG (en-tete IHDR) sans dependance externe."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(26)
        if head[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        w, h = struct.unpack(">II", head[16:24])
        return w, h
    except OSError:
        return None


def walk(root: str, exts: set[str]):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if os.path.splitext(name)[1].lower() in exts:
                yield os.path.join(dirpath, name)


def load_texts(root: str) -> list[tuple[str, str]]:
    out = []
    for path in walk(root, TEXT_EXT):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                out.append((os.path.relpath(path, root), fh.read()))
        except OSError:
            continue
    return out


def find_references(rel_img: str, texts: list[tuple[str, str]]) -> list[dict]:
    """Cherche ou l'image est citee/explicitee dans les fichiers texte."""
    stem = os.path.splitext(os.path.basename(rel_img))[0]
    base = os.path.basename(rel_img)
    refs = []
    for rel_md, body in texts:
        lines = body.splitlines()
        for i, line in enumerate(lines):
            hit = False
            alt = ""
            m = re.search(rf"!\[([^\]]*)\]\(([^)]+)\)", line)
            if m:
                alt = m.group(1).strip()
                target = m.group(2).strip()
                if base in target or os.path.basename(target) == base:
                    hit = True
            if not hit and (base in line or (len(stem) > 3 and stem in line)):
                hit = True
            if not hit:
                continue
            heading = ""
            for prev in lines[:i][::-1]:
                hm = re.match(r"^(#{1,6})\s+(.*)$", prev)
                if hm:
                    heading = hm.group(2).strip()
                    break
            refs.append({"file": rel_md, "heading": heading, "line": i + 1, "alt": alt})
    return refs


def describe_from_name(stem: str) -> str:
    """Hypothese de contenu a partir du nom de fichier, toujours a confirmer par le modele."""
    hints = {
        "carte": "carte / geographie", "map": "carte / geographie",
        "portrait": "portrait de personnage", "perso": "portrait de personnage",
        "plan": "plan / architecture", "blason": "blason / heraldique",
        "arbre": "arbre genealogique", "genealog": "arbre genealogique",
        "chrono": "frise chronologique", "timeline": "frise chronologique",
        "schema": "schema / diagramme", "croquis": "croquis", "sketch": "croquis",
        "cover": "couverture", "illustration": "illustration",
    }
    low = stem.lower()
    for key, label in hints.items():
        if key in low:
            return label
    return "visuel non qualifie (a decrire)"


def build_index(bible_dir: str) -> dict:
    bible_dir = os.path.abspath(os.path.expanduser(bible_dir))
    if not os.path.isdir(bible_dir):
        raise SystemExit(f"ERREUR: dossier World Bible introuvable: {bible_dir}")
    texts = load_texts(bible_dir)
    items = []
    for path in walk(bible_dir, IMG_EXT):
        rel = os.path.relpath(path, bible_dir)
        stem = os.path.splitext(os.path.basename(rel))[0]
        size = png_size(path)
        refs = find_references(rel, texts)
        items.append(
            {
                "image": rel,
                "abs_path": path,
                "bytes": os.path.getsize(path),
                "dimensions": f"{size[0]}x{size[1]}" if size else None,
                "guess": describe_from_name(stem),
                "tokens": sorted(set(tokenize(stem))),
                "references": refs,
                "documented": bool(refs),
            }
        )
    return {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bible_dir": bible_dir,
        "image_count": len(items),
        "documented_count": sum(1 for i in items if i["documented"]),
        "images": items,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Indexe les visuels d'une World Bible.")
    ap.add_argument("--bible", required=True, help="Dossier de la World Bible")
    ap.add_argument("--out", default=None, help="JSON de sortie (defaut: <bible>/.index/vision.json)")
    ap.add_argument("--json", action="store_true", help="Affiche l'index en JSON")
    ap.add_argument("--query", default=None, help="Ne garder que les visuels correspondant a ce mot-cle")
    ap.add_argument("--emit-prompt", type=int, default=0, metavar="N", help="Emet un prompt pret a envoyer pour le visuel n°N (1-based)")
    args = ap.parse_args()

    index = build_index(args.bible)

    if args.query:
        q = set(tokenize(args.query))
        index["images"] = [
            i for i in index["images"]
            if q & set(i["tokens"]) or fold(args.query) in fold(" ".join(r["alt"] + " " + r["heading"] for r in i["references"]))
        ]

    out = args.out or os.path.join(index["bible_dir"], ".index", "vision.json")

    if args.emit_prompt:
        if not 1 <= args.emit_prompt <= len(index["images"]):
            raise SystemExit(f"ERREUR: visuel n°{args.emit_prompt} inexistant (index de {len(index['images'])} visuels)")
        item = index["images"][args.emit_prompt - 1]
        print(f"[Image a joindre : {item['abs_path']}]")
        print()
        print(f"Voici un visuel de la World Bible ({item['guess']}, {item['dimensions'] or 'dimensions inconnues'}).")
        if item["references"]:
            print("\nLe texte qui l'accompagne dans la Bible :")
            for r in item["references"]:
                where = f"{r['file']} :: {r['heading']}" if r["heading"] else r["file"]
                print(f"  - {where}" + (f" (legende : « {r['alt']} »)" if r["alt"] else ""))
        else:
            print("\nAucun texte de la Bible ne reference ce fichier : son contenu n'est pas documente.")
        print()
        print("Decris ce que tu vois, puis :")
        print("1. liste les faits du monde que ce visuel etablit ou confirme ;")
        print("2. signale toute contradiction avec le texte cite ci-dessus ;")
        print("3. precise ce que le visuel montre et que le texte ne dit pas (a trancher avec l'auteur).")
        print("N'affirme rien qui ne soit visible dans l'image ou present dans le texte.")
        return 0

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=1)

    if args.json:
        print(json.dumps(index, ensure_ascii=False, indent=1))
        return 0

    print(f"=== VISUELS DE LA WORLD BIBLE : {index['bible_dir']} ===")
    print(f"{index['image_count']} image(s), dont {index['documented_count']} documentee(s) par le texte")
    if not index["images"]:
        print("Aucun visuel trouve. Formats reconnus: " + ", ".join(sorted(IMG_EXT)))
        return 0
    print(f"index ecrit: {out}\n")
    for n, item in enumerate(index["images"], 1):
        flag = "documente" if item["documented"] else "NON DOCUMENTE"
        print(f"[{n}] {item['image']}")
        print(f"    {item['guess']} | {item['dimensions'] or '?'} | {item['bytes']} octets | {flag}")
        for r in item["references"][:3]:
            where = f"{r['file']} :: {r['heading']}" if r["heading"] else r["file"]
            print(f"    -> {where}" + (f" (legende: {r['alt']})" if r["alt"] else ""))
    print("\nPour obtenir un prompt pret a envoyer au modele avec l'image :")
    print(f"  python3 {os.path.basename(__file__)} --bible {args.bible} --emit-prompt <N>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
