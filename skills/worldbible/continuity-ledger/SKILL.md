---
name: continuity-ledger
description: "Tient le registre de continuité d'un projet d'écriture : faits canoniques figés, nouveaux éléments créés en cours d'écriture, chronologie des événements du récit, états persistants des personnages et objets. À utiliser pour enregistrer un fait nouveau, suivre qui sait quoi, mesurer l'avancement d'un manuscrit. Trigger: registre, canon, journal, ajouter au canon, avancement, mots écrits."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [worldbible, canon, tracking, writing]
    category: worldbible
    related_skills: [continuity-check, chapter-draft, lore-lookup]
    config:
      - key: worldbible.manuscript_dir
        description: "Dossier du manuscrit en cours"
        default: "~/manuscrit"
        prompt: "Dossier de votre manuscrit"
---

# Continuity Ledger — la mémoire du récit

La World Bible décrit le monde **avant** l'histoire. Le registre décrit ce que l'histoire
**a déjà fait**. Sans lui, le chapitre 12 contredit le chapitre 3.

## Fichiers du registre

Dans le dossier du manuscrit :

```
manuscrit/
├── LEDGER.md        # faits figés + nouveautés du récit (source de vérité)
├── TIMELINE.md      # chronologie des événements du récit, par chapitre
└── outline.md       # plan (skill story-outline)
```

## Format de LEDGER.md

```
# Registre de continuité — <titre>

## 1. Faits figés (ne plus modifier sans décision explicite)
- [PERSO] Kaelin Marre — main gauche brûlée. (chap. 1, canon: personnages/kaelin.md)
- [REGLE] Neuf minutes max sans respirer la résine. (canon: monde/magie.md)

## 2. Nouveautés créées par le récit (à répercuter dans la Bible)
- [LIEU] Le Quai des Cendres — créé chap. 2, absent de la Bible. → à intégrer
- [OBJET] La boussole de Kaerin — créée chap. 5.

## 3. États persistants (vérifier à chaque chapitre)
- Ilven : blessure à l'épaule depuis chap. 4 — guérison prévue chap. 11.
- Le Conseil d'Olm : ignore la fuite (chap. 1–6). L'apprend au chap. 7.

## 4. Qui sait quoi
| Information | Détenteurs | Chap. où ils l'apprennent |
| --- | --- | --- |
| Origine de l'Incendie | Kaelin | 1 |
| Origine de l'Incendie | Ilven | 9 |

## 5. Décisions d'auteur (entorses assumées)
- chap. 6 : la résine ne brûle pas Kaelin — entorse assumée, justifiée par …
```

## Procédure

### Enregistrer après chaque chapitre

1. Relire le chapitre terminé et extraire : faits nouveaux, changements d'état, informations
   révélées à un personnage, événements datables.
2. Ajouter chaque ligne au bon endroit de `LEDGER.md`, avec le numéro de chapitre et, si le
   fait vient de la Bible, sa source.
3. Ajouter l'événement datable à `TIMELINE.md`.
4. Repérer dans « Nouveautés » ce qui devrait rejoindre la World Bible, et le proposer à
   l'utilisateur (ne jamais écrire dans la Bible sans accord : c'est son canon).

### Vérifier avant d'écrire un chapitre

1. Lire « États persistants » et « Qui sait quoi » : c'est la liste des choses que le chapitre
   ne doit pas violer.
2. Passer cette liste au chapitre en cours d'écriture (elle alimente le dossier canonique du
   skill `chapter-draft`).

### Mesurer l'avancement

```bash
python3 ${HERMES_SKILL_DIR}/scripts/wb_manuscript.py <manuscrit>/chapitres --target-words 90000
```

Annoncer les chiffres **tels que mesurés** (fichiers, total, moyenne par chapitre, % de
l'objectif). Ne jamais estimer une longueur de mémoire.

## Pièges

- **Registre écrit une fois puis oublié.** Il ne vaut que mis à jour à chaque chapitre.
- **Confondre Bible et registre.** Le registre suit le récit ; la Bible décrit le monde. Les nouveautés migrent vers la Bible **après accord**.
- **Fait figé sans source.** Toute ligne doit porter un chapitre ou une source de Bible, sinon on ne peut plus trancher un conflit.
- **Oublier les états persistants.** Blessures, objets, dettes, secrets : c'est là que naissent les incohérences les plus visibles.
- **Longueur inventée.** Toujours mesurer avec le script.

## Vérification

Après mise à jour : chaque chapitre écrit apparaît dans `LEDGER.md` (au moins une ligne),
chaque événement datable apparaît dans `TIMELINE.md`, et la section « Nouveautés » ne contient
plus d'élément non signalé à l'utilisateur.
