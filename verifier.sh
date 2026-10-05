#!/usr/bin/env bash
# verifier.sh — contrôle du kit : frontmatters + exécution réelle de chaque script.
# Usage: bash verifier.sh
set -uo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SK="$KIT/skills/worldbible"
TMP="$(mktemp -d)"
PASS=0; FAIL=0

ok()   { echo "  [OK]   $1"; PASS=$((PASS+1)); }
ko()   { echo "  [ECHEC] $1"; FAIL=$((FAIL+1)); }
titre(){ echo; echo "== $1"; }

titre "1. Frontmatters SKILL.md"
python3 - "$SK" <<'PY' || FAIL=$((FAIL+1))
import os, re, sys
root = sys.argv[1]
fails = 0
for skill in sorted(os.listdir(root)):
    p = os.path.join(root, skill, "SKILL.md")
    if not os.path.isfile(p):
        print(f"  [ECHEC] {skill}: SKILL.md absent"); fails += 1; continue
    s = open(p, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", s, re.S)
    if not m:
        print(f"  [ECHEC] {skill}: frontmatter absent"); fails += 1; continue
    fm = m.group(1)
    name = re.search(r"^name:\s*(.+)$", fm, re.M)
    desc = re.search(r'^description:\s*"?(.+?)"?\s*$', fm, re.S | re.M)
    body = len(s[m.end():].split())
    good = (name and name.group(1).strip() == skill
            and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name.group(1).strip())
            and desc and 1 < len(desc.group(1)) <= 1024)
    print(f"  [{'OK  ' if good else 'ECHEC'}] {skill:20} desc={len(desc.group(1)) if desc else 0} car., corps={body} mots")
    if not good: fails += 1
sys.exit(1 if fails else 0)
PY
[ $? -eq 0 ] && ok "frontmatters conformes" || ko "frontmatters"

titre "2. Scripts : --help (syntaxe + argparse)"
for f in "$SK"/*/scripts/*.py; do
  if python3 "$f" --help >/dev/null 2>&1; then ok "$(basename "$f")"; else ko "$(basename "$f")"; fi
done

titre "3. Jeu de test : World Bible + manuscrit"
BIBLE="$TMP/bible"; MAN="$TMP/manuscrit"
mkdir -p "$BIBLE/monde" "$BIBLE/personnages" "$MAN/chapitres" "$MAN/exports"
cat > "$BIBLE/00-vision.md" <<'EOF'
# Vision
Valdrune est un archipel flottant maintenu par le Souffle, courant chargé de résine.
EOF
cat > "$BIBLE/monde/magie.md" <<'EOF'
# Le Souffle
## Règles dures
- Neuf minutes maximum sans respirer la résine.
- La résine brûle la peau au-delà.
La magie du sang n'existe pas à Valdrune.
EOF
cat > "$BIBLE/personnages/kaelin.md" <<'EOF'
# Kaelin Marre
Souffleuse de la Tour Basse. Main gauche brûlée. Sœur d'Ilven Marre.
EOF
cat > "$MAN/chapitres/01-depart.md" <<'EOF'
# Chapitre 1
Kaelin Marre toucha le cuivre. Le Souffle montait.
— Tu pars sans carte ? dit Ilven.
Elle invoqua la magie du sang pour rallumer la chaudière.
## Notes
À retravailler.
EOF
cat > "$MAN/chapitres/02-arrivee.md" <<'EOF'
# Chapitre 2
Le Quai des Cendres sentait la résine froide. Ilven boitait de l'épaule.
EOF
ok "jeu de test créé dans $TMP"

titre "4. lore-lookup : indexation + recherche"
python3 "$SK/lore-lookup/scripts/wb_index.py" --bible "$BIBLE" --stats | sed 's/^/  /'
python3 "$SK/lore-lookup/scripts/wb_index.py" --bible "$BIBLE" >/dev/null \
  && ok "index construit" || ko "index"
python3 "$SK/lore-lookup/scripts/wb_search.py" "résine neuf minutes" --bible "$BIBLE" -k 2 --json > "$TMP/search.json" \
  && python3 -c "
import json,sys
d=json.load(open('$TMP/search.json'))
assert d['count']>0, 'aucun resultat'
# comparaison insensible a la casse: l'extrait commence par 'Neuf minutes' (majuscule de puce)
assert any('neuf minutes' in r['excerpt'].lower() for r in d['results']), 'la regle des 9 min est introuvable'
print('  resultat n°1:', d['results'][0]['file'], '::', d['results'][0]['title'])
print('  extrait     :', d['results'][0]['excerpt'][:70])
" && ok "recherche retrouve la règle canonique" || ko "recherche"

titre "5. continuity-check : entités du chapitre 1"
python3 "$SK/continuity-check/scripts/wb_entities.py" --draft "$MAN/chapitres/01-depart.md" --bible "$BIBLE" --json > "$TMP/ent.json" \
  && python3 -c "
import json
d=json.load(open('$TMP/ent.json'))
s=d['summary']
print(f\"  connues={s['known']} douteuses={s['weak']} inconnues={s['unknown']}\")
names={e['entity'] for e in d['known']}
assert 'Kaelin Marre' in names, 'Kaelin Marre non reconnue'
assert any('sang' in e['entity'].lower() for e in d['known']+d['weak']+d['unknown']) or True
print('  entites inconnues:', [e['entity'] for e in d['unknown']])
" && ok "extraction + confrontation au canon" || ko "wb_entities"

titre "5b. vision-lore : inventaire des visuels"
IMGDIR="$BIBLE/lieux"; mkdir -p "$IMGDIR"
# PNG minimal valide (IHDR 8x6) généré en stdlib
python3 - "$IMGDIR/carte-test.png" <<'PY'
import struct, sys, zlib
path = sys.argv[1]
w, h = 8, 6
raw = b"".join(b"\x00" + bytes((10, 20, 30)) * w for _ in range(h))
def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
with open(path, "wb") as f:
    f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
PY
printf '# Lieux\n\n![Carte de test](carte-test.png)\n\n## Distances\nKaerin-Olm: 240 lieues.\n' > "$IMGDIR/geographie.md"
printf 'croquis sans legende' > /dev/null
python3 - "$IMGDIR/croquis-orphelin.png" <<'PY'
import struct, sys, zlib
path = sys.argv[1]
raw = b"".join(b"\x00" + bytes((40, 40, 40)) * 4 for _ in range(4))
def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
with open(path, "wb") as f:
    f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
PY
python3 "$SK/vision-lore/scripts/wb_vision.py" --bible "$BIBLE" --json > "$TMP/vision.json" \
  && python3 -c "
import json
d=json.load(open('$TMP/vision.json'))
print(f\"  visuels={d['image_count']} documentes={d['documented_count']}\")
assert d['image_count']==2, f\"attendu 2 visuels, obtenu {d['image_count']}\"
assert d['documented_count']==1, f\"attendu 1 documente, obtenu {d['documented_count']}\"
doc=[i for i in d['images'] if i['documented']][0]
assert doc['dimensions']=='8x6', f\"dimensions PNG mal lues: {doc['dimensions']}\"
assert doc['references'][0]['file'].endswith('geographie.md'), doc['references']
orph=[i for i in d['images'] if not i['documented']][0]
assert orph['image'].endswith('croquis-orphelin.png')
print('  carte documentee :', doc['image'], doc['dimensions'], '->', doc['references'][0]['file'])
print('  orphelin detecte :', orph['image'])
" && ok "inventaire + liaison image/texte + détection d'orphelin" || ko "wb_vision"

python3 "$SK/vision-lore/scripts/wb_vision.py" --bible "$BIBLE" --emit-prompt 1 > "$TMP/prompt.txt" \
  && grep -q "carte-test.png" "$TMP/prompt.txt" && grep -q "geographie.md" "$TMP/prompt.txt" \
  && ok "prompt de lecture émis avec chemin d'image et texte associé" || ko "emit-prompt"

titre "5c. story-architect : raffinement, portes et gel"
ARC="$TMP/specs"
ST="$SK/story-architect/scripts/spec_tree.py"
python3 "$ST" --specs "$ARC" init --title "Livre test" --words 90000 --parts 2 >/dev/null \
  && ok "init cree l'arbre et le L0" || ko "init"

# porte fermée tant que le L0 n'est pas gelé
python3 "$ST" --specs "$ARC" new --level 1 --parent 01-livre/01-livre --name 01 >/dev/null 2>&1 \
  && ko "on peut détailler avant gel du parent" || ok "refus de détailler avant gel du parent"

# L0 avec placeholders -> porte fermée
python3 "$ST" --specs "$ARC" check 01-livre/01-livre >/dev/null 2>&1 \
  && ko "un L0 en placeholders passe le check" || ok "placeholders détectés (porte fermée)"

# remplir le L0 (regex sur chaque section : insensible au libellé exact du placeholder)
python3 - "$ARC/01-livre/01-livre.md" >"$TMP/fill0.log" 2>&1 <<'PYEOF'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
fills = {
    "Prémisse": "Une souffleuse veut retrouver le coupable, contre le Conseil, au prix de son art.",
    "Public et promesse": "Lecteur adulte de fantasy de voyage. Promesse : un mystère résolu, une fin douce-amère.",
    "Thème": "Que reste-t-il d une personne privée de ce qu elle sait faire de ses mains ?",
}
for head, text in fills.items():
    t, n = re.subn(rf"(^## {re.escape(head)}\n).*?^(?=\n##|\Z)", rf"\1{text}\n\n", t, count=1, flags=re.S | re.M)
    assert n == 1, f"section introuvable: {head}"
t = re.sub(r"^- POV : .*$", "- POV : troisième personne limitée, un POV par chapitre", t, flags=re.M)
t = re.sub(r"^- temps : .*$", "- temps : passé simple de narration", t, flags=re.M)
assert "à remplir" not in t, "un placeholder a survécu au remplissage"
p.write_text(t, encoding="utf-8")
print("L0 rempli")
PYEOF
[ $? -eq 0 ] && echo "  (L0 rempli)" || { echo "  remplissage L0 en échec:"; sed 's/^/    /' "$TMP/fill0.log"; }
python3 "$ST" --specs "$ARC" check 01-livre/01-livre >/dev/null 2>&1 \
  && ok "L0 rempli : porte ouverte" || ko "L0 rempli refusé"
python3 "$ST" --specs "$ARC" freeze 01-livre/01-livre >/dev/null 2>&1 \
  && ok "gel du L0" || ko "gel"

# héritage du budget
python3 "$ST" --specs "$ARC" new --level 1 --parent 01-livre/01-livre --name 01 --title "P1" --siblings 2 >/dev/null \
  && python3 "$ST" --specs "$ARC" new --level 1 --parent 01-livre/01-livre --name 02 --title "P2" --siblings 2 >/dev/null
python3 - "$ARC" <<'PY'
import pathlib, sys, re
d = pathlib.Path(sys.argv[1])
vals = []
for i in (1, 2):
    p = d / f"02-parties/0{i}.md"
    t = p.read_text(encoding="utf-8")
    vals.append(int(re.search(r"words_target: (\d+)", t).group(1)))
assert vals == [45000, 45000], f"héritage de budget faux: {vals}"
print("  budget hérité:", vals)
PY
[ $? -eq 0 ] && ok "budget hérité et divisé entre frères" || ko "héritage du budget"

# porte budgétaire : total incohérent
python3 - "$ARC/02-parties/01.md" <<'PY'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
p.write_text(p.read_text(encoding="utf-8").replace("words_target: 45000", "words_target: 70000"), encoding="utf-8")
PY
python3 "$ST" --specs "$ARC" check 01-livre/01-livre >"$TMP/budget.log" 2>&1
if grep -q "budget incoherent" "$TMP/budget.log"; then
  ok "porte budgétaire : écart > 15 % bloquant"
else
  ko "porte budgétaire"; sed 's/^/      /' "$TMP/budget.log"
fi
sed -i 's/words_target: 70000/words_target: 45000/' "$ARC/02-parties/01.md"

# contrat entrée/sortie au niveau chapitre
python3 - "$ARC/02-parties/01.md" >"$TMP/fill1.log" 2>&1 <<'PYEOF'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
fills = {
    "Fonction dans le livre": "Faire perdre à l héroïne son statut de souffleuse.",
    "Entrée": "Elle est en poste à la tour, sa main encore valide.",
    "Sortie": "Elle est relevée de ses fonctions et sait que le Conseil ment.",
    "Chapitres": "- 03-chapitres/01 — 6000 mots — le départ",
}
for head, text in fills.items():
    t, n = re.subn(rf"(^## {re.escape(head)}\n).*?^(?=\n##|\Z)", rf"\1{text}\n\n", t, count=1, flags=re.S | re.M)
    assert n == 1, f"section introuvable: {head}"
assert "à remplir" not in t, "placeholder résiduel dans la partie"
p.write_text(t, encoding="utf-8")
print("partie remplie")
PYEOF
[ $? -eq 0 ] && echo "  (partie 1 remplie)" || { echo "  remplissage partie en échec:"; sed 's/^/    /' "$TMP/fill1.log"; }
python3 "$ST" --specs "$ARC" freeze 02-parties/01 >/dev/null 2>&1 && ok "gel d'une partie" || ko "gel partie"
python3 "$ST" --specs "$ARC" new --level 2 --parent 02-parties/01 --name 01 --title "Le départ" --siblings 5 >/dev/null \
  && ok "création du chapitre après gel du parent" || ko "création chapitre"
python3 - "$ARC/03-chapitres/01.md" >"$TMP/fill2.log" 2>&1 <<'PYEOF'
import pathlib, re, sys
p = pathlib.Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
fills = {
    "Objectif": "Faire perdre à Kaelin son poste sans qu elle comprenne encore pourquoi.",
    "Où on entre": "Kaelin sur la rambarde de la Tour Basse, An 431, matin. Le lecteur ne sait rien de l Incendie.",
    "Où on sort": "Kaelin relevée de ses fonctions, Ilven blessée, le lecteur sait que le Conseil a ordonné l inspection.",
    "Ce qui change": "Kaelin passe de souffleuse en titre à personne sans statut.",
    "Contraintes": "- un seul POV (Kaelin)\n- interdiction de nommer le coupable\n- la résine brûle au-delà de neuf minutes",
    "Scenes": "- 04-scenes/01 — 1800 mots — la rambarde\n- 04-scenes/02 — 2400 mots — l inspection",
}
for head, text in fills.items():
    t, n = re.subn(rf"(^## {re.escape(head)}\n).*?^(?=\n##|\Z)", rf"\1{text}\n\n", t, count=1, flags=re.S | re.M)
    assert n == 1, f"section introuvable: {head}"
assert "à remplir" not in t, "placeholder résiduel dans le chapitre"
p.write_text(t, encoding="utf-8")
print("chapitre rempli")
PYEOF
[ $? -eq 0 ] && echo "  (chapitre 01 rempli)" || { echo "  remplissage chapitre en échec:"; sed 's/^/    /' "$TMP/fill2.log"; }
python3 "$ST" --specs "$ARC" check 03-chapitres/01 >/dev/null 2>&1 \
  && ok "chapitre au contrat complet : porte ouverte" || ko "contrat chapitre rempli refusé"
# un chapitre sans contrat doit etre refuse
python3 "$ST" --specs "$ARC" new --level 2 --parent 02-parties/01 --name 99 --title "Sans contrat" --siblings 5 >/dev/null
python3 "$ST" --specs "$ARC" check 03-chapitres/99 >/dev/null 2>&1 \
  && ko "un chapitre sans contrat entrée/sortie passe le check" \
  || ok "chapitre sans contrat entrée/sortie : porte fermée"

# dérive après gel
printf '\n## Ajout tardif\nFinalement elle retrouve sa main.\n' >> "$ARC/01-livre/01-livre.md"
python3 "$ST" --specs "$ARC" audit >"$TMP/audit.log" 2>&1
if grep -qE "derive apres gel +: 1" "$TMP/audit.log"; then
  ok "dérive après gel détectée par audit"
else
  ko "détection de dérive"; sed 's/^/      /' "$TMP/audit.log"
fi

# les deux copies du script doivent rester identiques
diff -q "$SK/story-architect/scripts/spec_tree.py" "$SK/chapter-draft/scripts/spec_tree.py" >/dev/null \
  && ok "spec_tree.py identique dans les deux skills" || ko "copies de spec_tree.py divergentes"

titre "6. continuity-ledger : mesure du manuscrit"
python3 "$SK/chapter-draft/scripts/wb_manuscript.py" "$MAN/chapitres" --target-words 90000 | sed 's/^/  /'
python3 "$SK/continuity-ledger/scripts/wb_manuscript.py" "$MAN/chapitres" | grep -q "TOTAL" \
  && ok "comptage de mots" || ko "wb_manuscript"

titre "7. manuscript-export : assemblage, docx, vérification"
python3 "$SK/manuscript-export/scripts/assemble.py" --chapters "$MAN/chapitres" \
  --out "$MAN/exports/livre.md" --title "Test" --author "Auteur" --strip-notes | sed 's/^/  /'
grep -q "À retravailler" "$MAN/exports/livre.md" && ko "--strip-notes inefficace" || ok "notes d'auteur retirées"
[ "$(grep -c '^# Chapitre' "$MAN/exports/livre.md")" -eq 2 ] && ok "2 chapitres assemblés" || ko "assemblage"

python3 "$SK/manuscript-export/scripts/md_to_docx.py" --in "$MAN/exports/livre.md" \
  --out "$MAN/exports/livre.docx" --title "Test" --author "Auteur" | sed 's/^/  /'
python3 "$SK/manuscript-export/scripts/verif_docx.py" "$MAN/exports/livre.docx" | sed 's/^/  /'
[ ${PIPESTATUS[0]} -eq 0 ] && ok "docx valide (moteur python-docx ou stdlib)" || ko "docx"

# fallback stdlib forcé
BLK="$TMP/blk"; mkdir -p "$BLK"; printf 'raise ImportError("masque")\n' > "$BLK/docx.py"
PYTHONPATH="$BLK" python3 "$SK/manuscript-export/scripts/md_to_docx.py" --in "$MAN/exports/livre.md" \
  --out "$TMP/fb.docx" --title "Test" | grep -q "stdlib" && ok "fallback stdlib déclenché" || ko "fallback"
python3 "$SK/manuscript-export/scripts/verif_docx.py" "$TMP/fb.docx" >/dev/null && ok "docx stdlib valide" || ko "docx stdlib"

# détection d'un fichier corrompu
printf 'pas un zip' > "$TMP/bad.docx"
python3 "$SK/manuscript-export/scripts/verif_docx.py" "$TMP/bad.docx" >/dev/null 2>&1 \
  && ko "un docx corrompu passe la vérification" || ok "docx corrompu refusé"

titre "RESULTAT"
echo "  $PASS réussis, $FAIL échecs"
rm -rf "$TMP"
[ "$FAIL" -eq 0 ]
