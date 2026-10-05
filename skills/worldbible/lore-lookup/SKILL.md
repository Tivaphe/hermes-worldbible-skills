---
name: lore-lookup
description: "Recherche des faits canoniques dans une World Bible (dossier de fichiers Markdown/txt) avec citations de sources. À utiliser dès qu'il faut répondre à une question de lore, vérifier un détail du monde (personnage, lieu, magie, chronologie, faction, objet), ou avant d'écrire quoi que ce soit qui se déroule dans cet univers. Trigger: world bible, lore, canon, univers, personnage, vérifier dans la bible."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [worldbible, lore, writing, retrieval]
    category: worldbible
    related_skills: [continuity-check, story-outline, chapter-draft]
    config:
      - key: worldbible.bible_dir
        description: "Chemin absolu du dossier racine de la World Bible"
        default: "~/worldbible"
        prompt: "Dossier de votre World Bible"
---

# Lore Lookup — interroger la World Bible avec preuves

Règle absolue : **aucune affirmation sur l'univers sans source**. Chaque réponse cite
`fichier :: titre` et reproduit la phrase exacte. Si la Bible ne contient pas l'information,
dire « absent de la Bible » — ne jamais inventer en la faisant passer pour du canon.

Pour structurer la Bible elle-même, voir la référence :
`skill_view("lore-lookup", "references/worldbible-structure.md")`

## Quand utiliser

- Question de lore : « Quel est l'âge de Kaelin ? », « Comment fonctionne la résine ? »
- Avant d'écrire une scène, un chapitre, un texte dérivé dans cet univers.
- Pour vérifier qu'un détail n'existe pas déjà (éviter de créer un doublon contradictoire).

## Prérequis : l'index

La recherche passe par un index JSON. Le construire (ou le reconstruire si la Bible a changé) :

```bash
python3 ${HERMES_SKILL_DIR}/scripts/wb_index.py --bible <DOSSIER_BIBLE>
```

L'index est écrit dans `<DOSSIER_BIBLE>/.index/index.json`. Vérifier la fraîcheur : si un
fichier de la Bible est plus récent que l'index, re-indexer.

Contrôle rapide du contenu :

```bash
python3 ${HERMES_SKILL_DIR}/scripts/wb_index.py --bible <DOSSIER_BIBLE> --stats
```

## Procédure

1. **Reformuler la question en 2 à 5 mots-clés** (pas une phrase). « règles magie résine durée » plutôt que « est-ce qu'un souffleur peut tenir longtemps ».
2. **Chercher** :

   ```bash
   python3 ${HERMES_SKILL_DIR}/scripts/wb_search.py "<mots-cles>" --bible <DOSSIER_BIBLE> -k 6 --context 400
   ```

3. **Lire les extraits renvoyés.** Si un extrait est coupé ou ambigu, ouvrir le fichier complet avec `read_file` — jamais de conclusion sur un extrait tronqué.
4. **Élargir si besoin** : au plus 3 recherches (termes plus généraux, synonymes du monde, nom propre). Au-delà, conclure « absent de la Bible ».
5. **Répondre** au format ci-dessous.

## Format de réponse

```
Réponse : <la réponse, une phrase ou deux>

Preuve canonique :
  • monde/magie.md :: Règles dures — « Un Souffleur ne peut tenir plus de neuf minutes… »

Absent de la Bible : <ce que la recherche n'a pas tranché, s'il y en a>
```

## Pièges

- **Extrait tronqué pris pour une règle.** Un tiret de liste coupé change le sens. Ouvrir le fichier.
- **Confondre deux homonymes.** Vérifier le fil d'Ariane (`crumbs`) : un même nom peut désigner un lieu et une personne.
- **Index périmé.** La Bible a été modifiée après l'index → réponses fausses mais confiantes. Re-indexer.
- **Synonymes internes.** La Bible dit « Souffle », l'utilisateur dit « mana » : relancer avec le terme de la Bible.
- **Zéro résultat ≠ absent.** Termes trop longs ou trop spécifiques : raccourcir avant de conclure.

## Vérification

Chaque affirmation de la réponse doit avoir une ligne « Preuve canonique » avec un couple
`fichier :: titre` qui existe réellement. Compter : nombre d'affirmations = nombre de preuves.
