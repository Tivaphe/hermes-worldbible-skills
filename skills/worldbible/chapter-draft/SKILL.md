---
name: chapter-draft
description: "Rédige un chapitre ou une scène de fiction cohérente avec la World Bible : préparation canonique, écriture par beats, contrôle de continuité, livraison en fichier. À utiliser pour écrire un chapitre, une scène, une nouvelle, ou continuer un manuscrit. Trigger: écrire un chapitre, rédiger une scène, continuer le roman, prose, manuscrit."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [worldbible, fiction, writing, drafting]
    category: worldbible
    related_skills: [story-architect, lore-lookup, style-guide, continuity-check, story-outline]
    config:
      - key: worldbible.bible_dir
        description: "Chemin absolu du dossier racine de la World Bible"
        default: "~/worldbible"
        prompt: "Dossier de votre World Bible"
      - key: worldbible.manuscript_dir
        description: "Dossier du manuscrit en cours (chapitres, outline, registre)"
        default: "~/manuscrit"
        prompt: "Dossier de votre manuscrit"
---

# Chapter Draft — écrire un chapitre qui tient debout

Principe : **on n'écrit jamais depuis sa mémoire du monde**. On écrit depuis les faits
récupérés dans la Bible pendant la préparation, et on vérifie à la fin.

## Quand utiliser

« Écris le chapitre 4 », « continue », « rédige la scène où… », ou pour une nouvelle isolée.

## Procédure

### 1. Cadrage (avant la moindre phrase)

**Cas A — le projet est architecturé (recommandé).** Vérifier que la spec du chapitre est
**gelée** avant d'écrire :

```bash
python3 ${HERMES_SKILL_DIR}/scripts/spec_tree.py --specs <manuscrit>/specs tree
```

Si elle est gelée, le cadrage n'est pas à inventer : il se **lit** dans la spec
(`manuscrit/specs/03-chapitres/NN.md`) — `## Où on entre`, `## Où on sort`,
`## Ce qui change`, `## Contraintes`, `## Scenes`. Écrire contre un contrat gelé, c'est
exactement ce qui empêche la dérive. Si le contrat s'avère faux en cours d'écriture :
s'arrêter, le signaler, faire re-geler la spec — ne pas diverger en silence.

Si la spec n'est pas gelée, ne pas écrire : la porte est fermée (voir `story-architect`).

**Cas B — projet sans arbre de specs.** Rassembler alors, dans un bloc de préparation :
- **Objectif du chapitre** : ce qui change entre la première et la dernière ligne (si rien ne change, le chapitre est inutile → le dire).
- **POV, lieu, moment** (date ou repère chronologique de la Bible).
- **Beats** : 4 à 8 puces, une par mouvement de la scène.
- **Contraintes** : longueur cible en mots, format depuis la charte.

Vérifier si un plan plat existe : `manuscrit/outline.md` (skill `story-outline`). S'il existe, le chapitre doit y correspondre ; s'il s'en écarte, signaler l'écart avant d'écrire.

### 2. Dossier canonique du chapitre

Lister les entités impliquées, puis pour chacune récupérer le fait canonique avec `lore-lookup`
(personnages présents, lieux, règles de magie/technologie, chronologie, ce que chaque personnage
sait et ne sait pas). Écrire ce dossier en tête de fichier de travail : c'est la seule source
autorisée pendant l'écriture.

**Interdit** : utiliser un détail de l'univers qui n'est pas dans ce dossier sans le vérifier
d'abord. En cas de besoin d'un détail neuf, le créer explicitement et l'enregistrer (étape 5).

### 3. Écriture

- Charger la charte (`style-guide`) et la suivre règle par règle.
- Écrire **beat par beat**, en sauvegardant au fur et à mesure dans `manuscrit/chapitres/NN-titre.md` (nom numérique pour garder l'ordre). Ne pas produire tout le chapitre d'un bloc dans la réponse.
- Dialogue : chaque réplique doit avoir un enjeu ; supprimer les répliques purement informatives.
- Exposition : ne jamais expliquer le monde en bloc. Une information du monde entre par un geste, un conflit ou une conséquence.

### 4. Contrôle

1. Mesurer : `python3 ${HERMES_SKILL_DIR}/scripts/wb_manuscript.py manuscrit/chapitres/` → mots réels du chapitre (ne jamais annoncer une longueur estimée).
2. Continuité : exécuter le skill `continuity-check` sur le fichier produit. Traiter **toutes** les contradictions bloquantes avant de livrer.
3. Relire à voix haute (silencieusement) pour le rythme : toute phrase qui demande une relecture est réécrite.

### 5. Mise à jour du canon

Chaque élément neuf introduit (nom, objet, règle, événement) est enregistré dans le registre
du projet via le skill `continuity-ledger`. Un chapitre livré sans mise à jour du registre
produit des incohérences au chapitre suivant.

## Pièges

- **Commencer par écrire.** Sans dossier canonique, le chapitre est plein d'inventions involontaires.
- **Chapitre sans changement.** Vérifier l'objectif à la fin : si l'état final = état initial, couper ou fusionner.
- **Exposition déguisée.** Deux personnages qui se racontent ce qu'ils savent déjà : couper.
- **Longueur annoncée de tête.** Toujours la mesurer avec le script.
- **Finir sur un cliffhanger systématique.** Alterner les types de fin (résolution, révélation, question, image).
- **Oublier les conséquences.** Un personnage blessé au chapitre 3 boite au chapitre 4. Vérifier les états persistants dans le registre.

## Vérification

Un chapitre est livré si et seulement si :
0. sa spec L2 était gelée avant l'écriture, et le texte respecte `## Où on entre` / `## Où on sort` ;
1. le fichier existe dans `manuscrit/chapitres/` ;
2. le nombre de mots est mesuré et annoncé ;
3. le rapport de `continuity-check` indique `PRÊT` (0 contradiction bloquante) ;
4. les éléments neufs sont inscrits au registre.
