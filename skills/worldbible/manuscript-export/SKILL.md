---
name: manuscript-export
description: "Assemble un manuscrit en fichiers Markdown et l'exporte en DOCX, EPUB ou PDF de qualité éditoriale (page de titre, chapitres, pagination, métadonnées). À utiliser pour compiler un livre, produire un fichier lisible/partageable, préparer un envoi à un éditeur ou une auto-publication. Trigger: exporter, compiler le livre, docx, epub, pdf, manuscrit final."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [worldbible, export, publishing, writing]
    category: worldbible
    related_skills: [continuity-check, continuity-ledger]
    config:
      - key: worldbible.manuscript_dir
        description: "Dossier du manuscrit en cours"
        default: "~/manuscrit"
        prompt: "Dossier de votre manuscrit"
---

# Manuscript Export — du dossier Markdown au livre

Ordre imposé : **contrôler → assembler → exporter → vérifier le fichier produit**.
Exporter un manuscrit non contrôlé diffuse les incohérences.

## Quand utiliser

« Compile le livre », « sors-moi un PDF », « je veux un EPUB », « prépare le fichier pour
l'éditeur ».

## Procédure

### 1. Contrôle préalable (bloquant)

1. Mesurer : `python3 ../continuity-ledger/scripts/wb_manuscript.py <manuscrit>/chapitres --target-words <objectif>`
2. Continuité : exécuter `continuity-check` sur **chaque** chapitre. Annoncer le résultat
   avant d'exporter. S'il reste des contradictions bloquantes, demander à l'utilisateur s'il
   veut exporter quand même (fichier marqué « version de travail »).

### 2. Assembler

Script fourni (ordre garanti, notes d'auteur retirées) :

```bash
python3 ${HERMES_SKILL_DIR}/scripts/assemble.py \
  --chapters <manuscrit>/chapitres \
  --out <manuscrit>/exports/livre.md \
  --title "<Titre>" --author "<Auteur>" --strip-notes
```

Le script affiche le nombre de mots **par fichier** et le total : c'est la mesure de référence.
Il écrit aussi `exports/meta.txt` (titre, auteur, nb de chapitres, mots) pour l'étape suivante.

### 3. Exporter

**DOCX — chemin principal, sans dépendance externe :**

```bash
python3 ${HERMES_SKILL_DIR}/scripts/md_to_docx.py \
  --in <manuscrit>/exports/livre.md \
  --out <manuscrit>/exports/livre.docx \
  --title "<Titre>" --author "<Auteur>"
```

Utilise `python-docx` s'il est installé, sinon bascule automatiquement sur un écrivain OOXML
en bibliothèque standard. Le `.docx` obtenu est valide dans les deux cas (le moteur employé
est affiché en sortie).

**Si pandoc est présent (`command -v pandoc`), préférer pandoc pour EPUB et PDF :**

```bash
pandoc <manuscrit>/exports/livre.md -o <manuscrit>/exports/livre.epub \
  --toc --epub-chapter-level=1 \
  --metadata title="<Titre>" --metadata author="<Auteur>" --metadata lang=fr

pandoc <manuscrit>/exports/livre.md -o <manuscrit>/exports/livre.pdf \
  --pdf-engine=xelatex -V lang=fr -V geometry:margin=2.5cm -V fontsize=11pt --toc
```

Le PDF exige un moteur LaTeX : vérifier `command -v xelatex` **avant** de promettre un PDF.
S'il manque, livrer `.md` + `.docx` et donner la commande d'installation manquante — ne pas
bricoler une conversion approximative.

### 4. Vérifier le fichier produit

Obligatoire, pas décoratif :

```bash
ls -lh <manuscrit>/exports/
python3 verif_docx.py <manuscrit>/exports/livre.docx   # ou le bloc ci-dessous
```

Bloc de vérification équivalent :

```python
import zipfile, re
p = "<manuscrit>/exports/livre.docx"
z = zipfile.ZipFile(p)
assert z.testzip() is None, "paquet corrompu"
xml = z.read("word/document.xml").decode("utf-8", errors="replace")
texte = re.sub(r"<[^>]+>", "", xml)
print("paragraphes :", len(re.findall(r"<w:p[ >]", xml)))
print("mots        :", len(texte.split()))
print("tete        :", texte[:80].strip())
print("queue       :", texte[-80:].strip())
```

Trois contrôles obligatoires : le paquet est intègre (`testzip()`), le nombre de mots du
`.docx` est du même ordre que celui annoncé par `assemble.py`, et la tête/queue du document
correspondent au premier et au dernier chapitre. Un `.docx` de quelques centaines d'octets
est un échec, pas un succès.

## Pièges

- **Exporter avant de contrôler.** Le fichier circule, les fautes de canon aussi.
- **Ordre de chapitres faux.** `ls | sort` impose des noms numériques à deux chiffres (`01-`, `02-`, … `10-`) : `1-`, `10-`, `2-` s'ordonnent mal.
- **Notes d'auteur publiées.** Filtrer les sections `## Notes`, `## TODO` avant l'export.
- **PDF annoncé sans moteur LaTeX.** Vérifier `xelatex` **avant** de promettre un PDF.
- **Titre dupliqué.** Ne pas remettre le titre dans le Markdown assemblé : `assemble.py` ne l'écrit pas, c'est `md_to_docx.py`/pandoc qui posent la page de titre.
- **Casse des caractères accentués.** Toujours `--metadata lang=fr` (et `xelatex`, jamais `pdflatex` par défaut, pour les accents).

## Vérification

Le livrable est valide si : le fichier existe avec une taille > 0, il s'ouvre (test `zipfile`
pour docx/epub), et le nombre de chapitres dans le fichier = nombre de fichiers source.
