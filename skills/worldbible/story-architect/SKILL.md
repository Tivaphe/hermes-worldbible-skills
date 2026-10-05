---
name: story-architect
description: "Architecte un récit par raffinement hiérarchique : livre → partie → chapitre → scène, chaque niveau produisant un contrat (où on entre, où on sort, ce qui change, budget de mots) qui s'impose au niveau suivant, avec gel par empreinte et portes bloquantes. À utiliser pour structurer un livre avant d'écrire, empêcher la dérive sur un long manuscrit, ou reprendre un plan qui part dans tous les sens. Trigger: architecte, structure, plan hiérarchique, raffinement, squelette, contrat de chapitre, où on entre où on sort, anti-dérive."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [worldbible, architecture, plotting, structure]
    category: worldbible
    related_skills: [story-outline, chapter-draft, continuity-ledger]
    config:
      - key: worldbible.manuscript_dir
        description: "Dossier du manuscrit en cours"
        default: "~/manuscrit"
        prompt: "Dossier de votre manuscrit"
---

# Story Architect — la structure porteuse avant la peau

Un écrivain professionnel n'écrit pas, il **architecte** : il sait quoi construire, pose les
fondations, dessine la structure porteuse, puis ne taille une pièce qu'avec ses cotes —
**où on entre, où on sort** — et ne pose la prose qu'à la fin, dans une pièce finie.

Ce skill **interdit de sauter les étages**. C'est la garantie anti-dérive : pas de chapitres
enchaînés dans le vide, pas de personnage qui change de couleur à mi-livre, pas de suite qui
oublie son début.

## Raffinement, pas diffusion

À ne pas confondre. Une **diffusion** part d'un brouillon global et l'affine itérativement,
tout d'un coup, jusqu'à convergence. Sur de la prose générée par un modèle auto-régressif,
cela veut dire réécrire un chapitre entier à chaque passe : cher, et le modèle casse ce qui
marchait.

Ici c'est un **raffinement descendant** : chaque niveau est terminé et **gelé** avant que le
suivant n'existe. Le brouillon n'est jamais global, il est local et court.

La diffusion garde un usage légitime, au **niveau plan** seulement : réordonner des scènes,
rééquilibrer des budgets de mots, déplacer une révélation. Ce sont des objets discrets, peu
coûteux à réitérer. La porte budgétaire du script rend ces rééquilibrages visibles.

## Les quatre niveaux

| N | Objet | Fichiers | Ce que le niveau fixe |
| --- | --- | --- | --- |
| L0 | livre | 1 | prémisse, public, promesse, thème, format, blocs |
| L1 | partie / acte | 3 à 6 | fonction narrative, entrée, sortie, chapitres |
| L2 | chapitre | 1 par chapitre | **contrat** : où on entre, où on sort, ce qui change, contraintes |
| L3 | scène | 1 à 4 par chapitre | beats, entrée, sortie |

La prose n'est **pas** un niveau : c'est la réalisation d'une spec L3, faite par `chapter-draft`.

## Procédure

### 1. Initialiser

```bash
python3 ${HERMES_SKILL_DIR}/scripts/spec_tree.py --specs <manuscrit>/specs init \
  --title "<Titre>" --words 90000 --parts 3
```

### 2. Écrire le niveau, puis le geler

Écrire la spec (sections imposées, aucune laissée en `à remplir`), puis :

```bash
python3 ${HERMES_SKILL_DIR}/scripts/spec_tree.py --specs <manuscrit>/specs check 01-livre/01-livre
python3 ${HERMES_SKILL_DIR}/scripts/spec_tree.py --specs <manuscrit>/specs freeze 01-livre/01-livre
```

`check` répond **PORTE OUVERTE** ou **PORTE FERMEE** avec la liste des points bloquants.
`freeze` refuse de geler une spec dont la porte est fermée. Le gel enregistre une empreinte
SHA-256 du corps : toute modification ultérieure est détectée.

### 3. Descendre d'un niveau

```bash
python3 ${HERMES_SKILL_DIR}/scripts/spec_tree.py --specs <manuscrit>/specs \
  new --level 1 --parent 01-livre/01-livre --name 01 --title "La descente" --siblings 3
```

`new` **refuse** si le parent n'est pas gelé (code de retour 2) : c'est l'interdiction de
sauter les étages, appliquée par le script et non par la bonne volonté du modèle.
Le budget de mots est hérité du parent et divisé par `--siblings`.

### 4. Se repérer

```bash
python3 ${HERMES_SKILL_DIR}/scripts/spec_tree.py --specs <manuscrit>/specs tree   # état de l'arbre
python3 ${HERMES_SKILL_DIR}/scripts/spec_tree.py --specs <manuscrit>/specs next   # quoi faire maintenant
python3 ${HERMES_SKILL_DIR}/scripts/spec_tree.py --specs <manuscrit>/specs audit  # dérives et orphelins
```

### 5. Passer à l'écriture

Un chapitre ne s'écrit que si sa spec L2 est **gelée**. `chapter-draft` lit alors le contrat
(`## Où on entre`, `## Où on sort`, `## Ce qui change`, `## Contraintes`) au lieu d'improviser
son cadrage.

## Les portes (ce qui est bloquant)

1. **Parent non gelé** → niveau suivant interdit.
2. **Parent modifié après gel** → l'empreinte ne correspond plus ; re-geler le parent puis
   revérifier les enfants.
3. **Section vide ou placeholder** (`à remplir`, `TODO`, `TBD`).
4. **`words_target` absent ou non numérique.**
5. **Budget incohérent** : la somme des budgets enfants s'écarte du budget du parent de plus
   de 15 % (`--tolerance` pour ajuster).

## Le contrat de chapitre, en détail

C'est la pièce maîtresse. Une spec L2 sans ces quatre sections ne vaut rien :

```
## Où on entre    état exact au premier mot : qui, où, quand, ce que le lecteur sait déjà
## Où on sort     état exact au dernier mot : ce qui a changé, ce que le lecteur sait de plus
## Ce qui change  une ligne vérifiable — si rien ne change, le chapitre ne sert à rien
## Contraintes    ce que ce chapitre a l'interdiction de faire (hérité du parent + canon)
```

Les contraintes héritent : ce que le livre interdit vaut pour chaque partie, ce que la partie
interdit vaut pour chaque chapitre. C'est ce qui empêche le personnage de changer de couleur
à mi-livre — l'interdiction est écrite au niveau où la décision a été prise, et redescend.

## Pièges

- **Sur-planifier.** Le piège principal. La règle : **un niveau n'est détaillé que juste assez
  pour contraindre le niveau suivant**. Un L0 tient en une page. Si le L0 fait dix pages, ce
  n'est plus un plan, c'est un autre livre.
- **Geler trop tôt.** Un gel sur une prémisse fausse verrouille l'erreur pour tout le livre.
  Faire valider L0 et L1 par l'auteur avant de descendre.
- **Confondre `next` et permission.** `next` dit quoi faire ; `check` seul autorise. Ne jamais
  écrire un niveau dont la porte est fermée.
- **Contourner par `--force`.** Possible, mais alors l'arbre ment. Préférer re-geler le parent.
- **Modifier un parent gelé en silence.** `audit` le détecte, mais seulement si on le lance :
  le lancer avant chaque session d'écriture.
- **Écrire la prose comme un niveau.** Non : la prose réalise une spec L3 gelée.

## Vérification

```bash
python3 ${HERMES_SKILL_DIR}/scripts/spec_tree.py --specs <manuscrit>/specs audit
```

L'arbre est sain si `audit` renvoie `COHERENT` : zéro dérive après gel, zéro parent absent,
zéro parent non gelé. Aucun chapitre ne part en écriture tant que sa spec L2 n'est pas gelée.
