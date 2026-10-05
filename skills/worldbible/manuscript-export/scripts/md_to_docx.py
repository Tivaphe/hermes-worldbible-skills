#!/usr/bin/env python3
"""
md_to_docx.py — Convertit un Markdown simple (manuscrit) en .docx.

Usage:
    python3 md_to_docx.py --in livre.md --out livre.docx --title "Titre" --author "Auteur"

Utilise python-docx s'il est disponible (mise en forme correcte), sinon un ecrivain
OOXML minimal en bibliotheque standard. Dans les deux cas le fichier produit est un
.docx valide (paquet OOXML + word/document.xml).

Gere: titres #..######, paragraphes, listes a puces (-, *), listes numerotees,
separateurs ---, gras **x** et italique *x* (via python-docx uniquement).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile

INLINE_BOLD = re.compile(r"\*\*(.+?)\*\*")
INLINE_ITAL = re.compile(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)")


def parse_blocks(md: str) -> list[tuple[str, str]]:
    """Retourne [(type, texte)] avec type dans {h1..h6, p, li, ol, hr}."""
    md = re.sub(r"\A---\n.*?\n---\n", "", md, flags=re.S)  # frontmatter
    blocks: list[tuple[str, str]] = []
    for raw in md.split("\n"):
        line = raw.rstrip()
        if not line.strip():
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            blocks.append((f"h{len(m.group(1))}", m.group(2).strip()))
            continue
        if re.match(r"^\s*[-*_]{3,}\s*$", line):
            blocks.append(("hr", ""))
            continue
        m = re.match(r"^\s*[-*+]\s+(.*)$", line)
        if m:
            blocks.append(("li", m.group(1).strip()))
            continue
        m = re.match(r"^\s*\d+[.)]\s+(.*)$", line)
        if m:
            blocks.append(("ol", m.group(1).strip()))
            continue
        if blocks and blocks[-1][0] == "p":
            blocks[-1] = ("p", blocks[-1][1] + " " + line.strip())
        else:
            blocks.append(("p", line.strip()))
    return blocks


# ---------------------------------------------------------------- python-docx
def build_with_python_docx(blocks, out, title, author) -> str:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()
    if title:
        p = doc.add_heading(title, level=0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if author:
        p = doc.add_paragraph(author)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def add_runs(par, text):
        pos = 0
        tokens = []
        for m in INLINE_BOLD.finditer(text):
            tokens.append((text[pos : m.start()], False, False))
            tokens.append((m.group(1), True, False))
            pos = m.end()
        tokens.append((text[pos:], False, False))
        for chunk, bold, _ital in tokens:
            if not chunk:
                continue
            run = par.add_run(chunk)
            run.bold = bold

    for kind, text in blocks:
        if kind == "hr":
            continue
        if kind.startswith("h"):
            doc.add_heading(re.sub(r"[*_]", "", text), level=min(int(kind[1]), 4))
        elif kind == "li":
            add_runs(doc.add_paragraph(style="List Bullet"), text)
        elif kind == "ol":
            add_runs(doc.add_paragraph(style="List Number"), text)
        else:
            par = doc.add_paragraph()
            par.paragraph_format.first_line_indent = None
            add_runs(par, text)
    doc.save(out)
    return "python-docx"


# ---------------------------------------------------------------- fallback stdlib
def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def para_xml(text: str, style: str | None = None) -> str:
    runs = ""
    pos = 0
    for m in INLINE_BOLD.finditer(text):
        runs += f'<w:r><w:t xml:space="preserve">{esc(text[pos:m.start()])}</w:t></w:r>'
        runs += f'<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">{esc(m.group(1))}</w:t></w:r>'
        pos = m.end()
    runs += f'<w:r><w:t xml:space="preserve">{esc(text[pos:])}</w:t></w:r>'
    ppr = f"<w:pPr><w:pStyle w:val=\"{style}\"/></w:pPr>" if style else ""
    return f"<w:p>{ppr}{runs}</w:p>"


def build_stdlib(blocks, out, title, author) -> str:
    body = []
    if title:
        body.append(para_xml(title, "Title"))
    if author:
        body.append(para_xml(author, "Subtitle"))
    for kind, text in blocks:
        if kind == "hr":
            continue
        if kind.startswith("h"):
            body.append(para_xml(re.sub(r"[*_]", "", text), f"Heading{min(int(kind[1]), 4)}"))
        elif kind == "li":
            body.append(para_xml("• " + text))
        elif kind == "ol":
            body.append(para_xml(text))
        else:
            body.append(para_xml(text))

    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'<w:body>{"".join(body)}<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1417" w:right="1417" w:bottom="1417" w:left="1417"/></w:sectPr>'
        "</w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)
    return "stdlib-fallback"


def main() -> int:
    ap = argparse.ArgumentParser(description="Markdown -> DOCX pour manuscrit.")
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default=None)
    ap.add_argument("--author", default=None)
    args = ap.parse_args()

    src = os.path.abspath(os.path.expanduser(args.src))
    out = os.path.abspath(os.path.expanduser(args.out))
    with open(src, "r", encoding="utf-8", errors="replace") as fh:
        md = fh.read()
    blocks = parse_blocks(md)
    if not blocks:
        print("Rien a convertir: aucun bloc trouve.")
        return 1

    try:
        engine = build_with_python_docx(blocks, out, args.title, args.author)
    except Exception as exc:  # python-docx absent ou cassé
        print(f"python-docx indisponible ({exc.__class__.__name__}) -> ecrivain OOXML stdlib")
        engine = build_stdlib(blocks, out, args.title, args.author)

    size = os.path.getsize(out)
    print(f"docx ecrit: {out}")
    print(f"  moteur  : {engine}")
    print(f"  blocs   : {len(blocks)} | taille: {size} octets")
    if size < 1000:
        print("  ATTENTION: fichier anormalement petit, verifier le contenu source")
    return 0


if __name__ == "__main__":
    sys.exit(main())
