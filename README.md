# Hermes World Bible Skills

Dix skills [agentskills.io](https://agentskills.io) pour [Hermes Agent](https://hermes-agent.nousresearch.com/)
qui transforment une **World Bible** en contenus écrits : roman, nouvelles, wiki, documents
in-universe, aides de jeu.

Le catalogue officiel bundled de Hermes ne contient aucun skill de fiction ou de world
building. Ce dépôt comble ce vide.

**Ce que le kit garantit** : aucune affirmation sur l'univers sans source citée, aucun
chapitre livré sans contrôle de continuité, aucune longueur annoncée sans mesure réelle.

---

## Pourquoi des scripts et pas seulement des prompts

Un modèle seul oublie, invente et estime mal. Le kit délègue donc le travail fiable à des
scripts Python (bibliothèque standard uniquement, Python 3.8+) et ne laisse au modèle que ce
qu'il fait bien : juger, écrire, trancher.

| Tâche | Qui la fait |
| --- | --- |
| Indexer la Bible, retrouver un fait | script (`wb_index.py`, `wb_search.py`) |
| Détecter les entités inconnues d'un chapitre | script (`wb_entities.py`) |
| Compter les mots, mesurer l'avancement | script (`wb_manuscript.py`) |
| Assembler et exporter en DOCX | script (`assemble.py`, `md_to_docx.py`) |
| Vérifier qu'un fichier produit est valide | script (`verif_docx.py`) |
| **Juger une contradiction de sens** | **modèle** |
| **Écrire la prose** | **modèle** |

Le kit reste utilisable avec des modèles plus petits : seuls `lore-lookup`,
`continuity-check` et `continuity-ledger` n'exigent que du texte. En revanche
`vision-lore` impose un modèle à vision native.

## Réglages recommandés selon le modèle

Testé avec **Qwen3.8-27B** (Apache 2.0, 27B dense, 262 144 tokens de contexte natif
extensible à 1M, encodeur visuel natif, mode thinking actif par défaut avec
`reasoning_effort` réglable sur `xhigh` / `medium` / `low`).

Le réglage qui change tout : **le mode thinking n'est pas bon pour la prose**. Il est utile
pour planifier et contrôler, nuisible pour écrire — une chaîne de raisonnement avant chaque
phrase durcit la voix narrative. Le modèle pense aussi volontiers trop long.

| Étape | Mode | `reasoning_effort` | Échantillonnage |
| --- | --- | --- | --- |
| `story-outline` | thinking | `xhigh` | `temp=1.0`, `top_p=0.95`, `top_k=20` |
| `continuity-check` | thinking | `xhigh` | idem |
| `lore-lookup` | thinking | `medium` | idem |
| `chapter-draft` | **instruct** (thinking off) | — | `temp=0.7`, `top_p=0.80`, `top_k=20`, `presence_penalty=1.5` |
| `style-guide` | instruct | — | idem prose |
| `manuscript-export` | instruct | `low` | idem prose |
| `vision-lore` | thinking | `medium` | idem thinking |

Les valeurs d'échantillonnage sont celles recommandées par la fiche modèle officielle, qui
distingue explicitement les deux jeux de paramètres.

Le contexte de 262 144 tokens permet de charger de gros blocs de la Bible d'un coup : les
skills préfèrent malgré tout la recherche ciblée, parce qu'un fait retrouvé avec sa source
reste vérifiable là où un gros contexte noyé ne l'est pas.

## Les 10 skills

| Skill | Rôle | Commande |
| --- | --- | --- |
| [`lore-lookup`](skills/worldbible/lore-lookup/SKILL.md) | Interroger la Bible avec preuves `fichier :: titre` | `/lore-lookup` |
| [`vision-lore`](skills/worldbible/vision-lore/SKILL.md) | Lire cartes, portraits et plans (modèle à vision native requis) | `/vision-lore` |
| [`story-outline`](skills/worldbible/story-outline/SKILL.md) | Plan plat pour explorer une structure | `/story-outline` |
| [`story-architect`](skills/worldbible/story-architect/SKILL.md) | Raffinement par niveaux, contrats entrée/sortie, gel et portes | `/story-architect` |
| [`style-guide`](skills/worldbible/style-guide/SKILL.md) | Charte stylistique mesurable (voix, rythme, interdits) | `/style-guide` |
| [`chapter-draft`](skills/worldbible/chapter-draft/SKILL.md) | Écrire un chapitre depuis le canon, pas depuis la mémoire | `/chapter-draft` |
| [`continuity-check`](skills/worldbible/continuity-check/SKILL.md) | Contrôler un texte contre la Bible (entités + contradictions) | `/continuity-check` |
| [`continuity-ledger`](skills/worldbible/continuity-ledger/SKILL.md) | Registre : faits figés, nouveautés, états persistants | `/continuity-ledger` |
| [`derivative-content`](skills/worldbible/derivative-content/SKILL.md) | Wiki, encyclopédie, nouvelles, in-universe, JDR, scripts | `/derivative-content` |
| [`manuscript-export`](skills/worldbible/manuscript-export/SKILL.md) | Assembler et exporter en DOCX / EPUB / PDF | `/manuscript-export` |

## Installation

```bash
git clone https://github.com/<votre-compte>/hermes-worldbible-skills.git
cd hermes-worldbible-skills

# 1. copier les skills dans l'arbre Hermes
mkdir -p ~/.hermes/skills
cp -r skills/worldbible ~/.hermes/skills/

# 2. vérifier le chargement
hermes skills list | grep -E 'lore-lookup|chapter-draft|continuity'

# 3. déclarer les chemins (une fois)
hermes config set skills.config.worldbible.bible_dir ~/worldbible
hermes config set skills.config.worldbible.manuscript_dir ~/manuscrit

# 4. indexer la Bible (écrit <bible>/.index/index.json)
python3 ~/.hermes/skills/worldbible/lore-lookup/scripts/wb_index.py --bible ~/worldbible

# optionnel : aperçu du contenu indexé, n'écrit rien
python3 ~/.hermes/skills/worldbible/lore-lookup/scripts/wb_index.py --bible ~/worldbible --stats
```

Les skills installés prennent effet dans une **nouvelle** session (`/reset`).

Installation skill par skill, sans cloner :

```bash
/skills install https://raw.githubusercontent.com/<votre-compte>/hermes-worldbible-skills/main/skills/worldbible/lore-lookup/SKILL.md --name lore-lookup
```

## Dépendances

- **Python 3.8+** — requis. Tous les scripts n'utilisent que la bibliothèque standard.
- **python-docx** — optionnel, export DOCX plus soigné. Absent → bascule automatique sur un
  écrivain OOXML standard, le fichier reste valide.
- **pandoc** — optionnel, pour EPUB. **xelatex** — optionnel, pour PDF.

## Chaîne de production d'un livre

```
1 /lore-lookup        → indexer la Bible, répondre aux questions de canon
2 /story-outline      → explorer la structure (plan plat, jetable)
3 /story-architect    → manuscrit/specs/  L0 livre → L1 parties → L2 chapitres → L3 scènes
                        chaque niveau est GELÉ avant que le suivant n'existe
4 /style-guide        → manuscrit/STYLE.md (charte mesurable)
5 /continuity-ledger  → manuscrit/LEDGER.md + TIMELINE.md
6 /chapter-draft      → manuscrit/chapitres/NN-titre.md   ← boucle par chapitre
      ↳ part de la spec L2 gelée (où on entre / où on sort / ce qui change / contraintes)
      ↳ intègre /lore-lookup (dossier canonique), /style-guide (voix),
        /continuity-check (contrôle), /continuity-ledger (mise à jour)
7 /manuscript-export  → exports/livre.md → livre.docx / .epub / .pdf

/vision-lore intervient en transversal, dès que la Bible contient des cartes ou des portraits.
```

### Pourquoi des niveaux gelés

C'est la garantie anti-dérive sur un long manuscrit. Un niveau n'est détaillé que **juste
assez pour contraindre le suivant**, et il est gelé par empreinte SHA-256 avant que le suivant
n'existe. Le script refuse de créer un enfant dont le parent n'est pas gelé, refuse de geler
une spec contenant encore `à remplir`, bloque si la somme des budgets de mots s'écarte de
plus de 15 % du budget du parent, et `audit` signale toute modification d'un niveau gelé.

Ce n'est **pas** une diffusion : une diffusion affinerait un brouillon global itérativement,
ce qui sur de la prose auto-régressive veut dire réécrire tout un chapitre à chaque passe.
Ici le brouillon est toujours local et court. La diffusion garde un usage au niveau plan
seulement (réordonner des scènes, rééquilibrer des budgets) — et la porte budgétaire rend
ces rééquilibrages visibles.

L'étape 5 se répète. C'est là que le kit sert le plus : chaque chapitre repart du canon et
repasse au contrôle, donc les incohérences ne s'accumulent pas sur 300 pages.

## Exemple jouable

Le dossier [`examples/`](examples/) contient une mini World Bible (*Valdrune*) et deux
chapitres. De quoi tester la chaîne complète sans toucher à votre projet :

```bash
# indexer (écrit examples/worldbible/.index/index.json)
python3 skills/worldbible/lore-lookup/scripts/wb_index.py --bible examples/worldbible

# optionnel : statistiques seulement, n'écrit rien
python3 skills/worldbible/lore-lookup/scripts/wb_index.py --bible examples/worldbible --stats

# retrouver une règle canonique
python3 skills/worldbible/lore-lookup/scripts/wb_search.py "résine neuf minutes" --bible examples/worldbible

# contrôler un chapitre contre le canon
python3 skills/worldbible/continuity-check/scripts/wb_entities.py \
  --draft examples/manuscrit/chapitres/01-le-depart.md --bible examples/worldbible

# inventorier les visuels et préparer leur lecture (modèle à vision requis)
python3 skills/worldbible/vision-lore/scripts/wb_vision.py --bible examples/worldbible
python3 skills/worldbible/vision-lore/scripts/wb_vision.py --bible examples/worldbible --emit-prompt 1
```

La Bible d'exemple contient deux visuels : une carte **documentée** par
`lieux/geographie.md`, et un croquis **non documenté**. Le second sert à montrer le cas que
`vision-lore` doit faire remonter plutôt que d'inventer.

Le chapitre 1 invoque volontairement « la magie du sang », que la Bible déclare inexistante :
c'est le cas de contradiction que `continuity-check` doit faire remonter au modèle.

## Structure d'une World Bible

L'index découpe les fichiers **sur les titres Markdown**. Une Bible en longs paragraphes sans
titres donne des réponses floues ; une Bible bien titrée donne des réponses sourçables.
Conventions détaillées : [`lore-lookup/references/worldbible-structure.md`](skills/worldbible/lore-lookup/references/worldbible-structure.md).

## Tests

```bash
bash verifier.sh
```

Contrôle les frontmatters (nom = dossier, `description` < 1024 caractères) puis **exécute
chaque script** sur un jeu de test temporaire : indexation, recherche d'une règle canonique,
extraction et confrontation des entités, comptage de mots, assemblage, export DOCX, bascule
du moteur d'export, et refus d'un `.docx` corrompu (test négatif).

Dernier passage : **20 réussis, 0 échec**.

## Arborescence

```
hermes-worldbible-skills/
├── skills/worldbible/          # les 10 skills (à copier dans ~/.hermes/skills/)
│   └── <skill>/SKILL.md + scripts/ + references/
├── examples/                   # World Bible et manuscrit de démonstration
├── verifier.sh                 # suite de tests
├── LICENSE                     # MIT
└── README.md
```

## Portabilité

Les `SKILL.md` suivent le standard ouvert agentskills.io : ils se chargent aussi dans les
runtimes compatibles (Claude Code, OpenCode, etc.). Les scripts sont autonomes — chaque skill
peut être installé seul.

## Licence

MIT — voir [LICENSE](LICENSE).
