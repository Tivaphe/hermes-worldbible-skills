#!/usr/bin/env python3
"""
verif_docx.py — Verifie qu'un .docx produit est reellement exploitable.

Usage:
    python3 verif_docx.py <fichier.docx>

Controles: paquet ZIP integre, partie word/document.xml presente et XML analysable,
nombre de paragraphes et de mots, extrait de tete et de queue.
Code de retour 0 si tout passe, 1 sinon.

Dependances: bibliotheque standard uniquement.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Verifie qu'un .docx produit est exploitable.")
    ap.add_argument("docx", help="Fichier .docx a verifier")
    args = ap.parse_args()
    path = os.path.abspath(os.path.expanduser(args.docx))
    ok = True

    if not os.path.isfile(path):
        print(f"ECHEC: fichier absent: {path}")
        return 1
    size = os.path.getsize(path)
    print(f"fichier : {path}")
    print(f"taille  : {size} octets")
    if size < 800:
        # seuil bas: un paquet OOXML minimal (ecrivain stdlib) est tres compact
        print("  -> ECHEC: taille anormalement faible pour un paquet OOXML")
        ok = False

    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        print("ECHEC: ce n'est pas un paquet ZIP/OOXML valide")
        return 1
    if z.testzip() is not None:
        print("ECHEC: paquet corrompu")
        return 1
    names = z.namelist()
    print(f"parties : {len(names)}")
    if "word/document.xml" not in names:
        print("ECHEC: partie word/document.xml absente")
        return 1

    xml_bytes = z.read("word/document.xml")
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        print(f"ECHEC: XML invalide: {exc}")
        return 1

    paragraphs = root.iter(f"{W}p")
    n_par = 0
    words = 0
    first = last = ""
    for par in paragraphs:
        text = "".join(t.text or "" for t in par.iter(f"{W}t"))
        n_par += 1
        if text.strip():
            words += len(text.split())
            if not first:
                first = text.strip()
            last = text.strip()

    print(f"paragraphes: {n_par}")
    print(f"mots       : {words}")
    print(f"tete       : {first[:90]}")
    print(f"queue      : {last[-90:]}")

    if n_par < 2:
        print("  -> ECHEC: moins de 2 paragraphes, document probablement vide")
        ok = False
    if words < 10:
        print("  -> ECHEC: moins de 10 mots, export probablement rate")
        ok = False

    print("verdict  :", "OK" if ok else "A VERIFIER")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
