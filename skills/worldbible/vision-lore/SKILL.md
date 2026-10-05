---
name: vision-lore
description: "Exploite les visuels d'une World Bible (cartes, portraits, blasons, plans, arbres généalogiques, frises) avec un modèle à vision native : référence chaque image au texte qui la décrit, fait lire l'image, puis confronte ce qu'elle montre au canon écrit. À utiliser quand la Bible contient des images, quand il faut vérifier qu'une carte colle au texte, ou extraire des faits d'une illustration. Trigger: carte, plan, portrait, illustration, image, visuel, voir la carte, lire l'image."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [worldbible, vision, multimodal, lore]
    category: worldbible
    related_skills: [lore-lookup, continuity-check]
    config:
      - key: worldbible.bible_dir
        description: "Chemin absolu du dossier racine de la World Bible"
        default: "~/worldbible"
        prompt: "Dossier de votre World Bible"
---

# Vision Lore — lire les images de la Bible

**Prérequis modèle** : ce skill exige un modèle à **vision native** (image et vidéo).
Qwen3.8-27B l'a : c'est un modèle de langage causal avec encodeur visuel, 27B paramètres,
262 144 tokens de contexte natif. Avec un modèle texte seul, ce skill est inopérant — le dire
à l'utilisateur plutôt que de décrire une image qu'on ne voit pas.

Règle absolue, identique à `lore-lookup` : **aucune affirmation sur l'univers sans source**.
Ici la source est soit le texte cité, soit ce qui est réellement visible dans l'image.

## Quand utiliser

- La Bible contient des cartes, portraits, blasons, plans, schémas, frises.
- « Est-ce que la carte colle au texte ? », « que montre cette illustration ? »
- Pour extraire des faits d'un visuel jamais transcrits dans le texte.

## Procédure

### 1. Inventorier les visuels

```bash
python3 ${HERMES_SKILL_DIR}/scripts/wb_vision.py --bible <DOSSIER_BIBLE>
```

Sortie : la liste des images avec dimensions, une hypothèse de contenu d'après le nom, et
surtout le statut **documenté / NON DOCUMENTÉ** — c'est-à-dire si un fichier texte de la Bible
référence l'image (lien Markdown `![...](...)` ou mention du nom).

L'index est écrit dans `<DOSSIER_BIBLE>/.index/vision.json`.

### 2. Choisir la cible

Filtrer si la Bible contient beaucoup de visuels :

```bash
python3 ${HERMES_SKILL_DIR}/scripts/wb_vision.py --bible <DOSSIER_BIBLE> --query "carte"
```

### 3. Générer le prompt de lecture

```bash
python3 ${HERMES_SKILL_DIR}/scripts/wb_vision.py --bible <DOSSIER_BIBLE> --emit-prompt <N>
```

Le script émet le chemin absolu de l'image à joindre, le texte de la Bible qui l'accompagne
(fichier, titre de section, légende), et la consigne en trois points. **Joindre réellement
l'image au message** — sans elle, aucune lecture n'est possible.

### 4. Lire, puis confronter

Une fois l'image sous les yeux :

1. **Décrire** ce qui est visible, sans interpréter.
2. **Établir les faits** : ce que l'image affirme sur l'univers (distances, hiérarchie,
   apparence, emblèmes).
3. **Confronter au texte** cité par le script. Toute divergence est une contradiction
   potentielle : la signaler avec les deux sources (image + `fichier :: titre`).
4. **Isoler l'apport** : ce que l'image montre et que le texte ne dit pas. C'est du canon
   candidat, pas du canon établi → à faire trancher par l'utilisateur.

### 5. Enregistrer

Les faits neufs confirmés par l'auteur vont dans le registre (skill `continuity-ledger`), avec
la mention « source : visuel `chemin/image.png` ». Un fait issu d'une image sans cette mention
devient invérifiable plus tard.

## Pièges

- **Décrire une image qu'on n'a pas.** Le modèle à vision ne voit que ce qui est joint au
  message. Pas d'image jointe = pas de description. Ne jamais inventer.
- **Prendre le nom de fichier pour le contenu.** `carte-nord.png` peut contenir le sud.
  L'hypothèse du script (`guess`) est une piste, jamais une conclusion.
- **Faire confiance à une image non documentée.** Sans texte associé, rien n'atteste que le
  visuel est à jour avec le canon. Le signaler.
- **Oublier l'échelle.** Une carte sans échelle ni légende ne donne pas de distances. Dire
  « proportionnel, échelle inconnue » plutôt que convertir en lieues.
- **Écrire dans la Bible.** Les faits issus d'un visuel sont des propositions tant que
  l'auteur ne les a pas validées.

## Vérification

Chaque fait tiré d'une image est accompagné de l'une des deux sources : ce qui est visible
(cité précisément) ou un `fichier :: titre`. Les divergences image/texte sont listées, pas
tranchées silencieusement. Les visuels « NON DOCUMENTÉ » signalés par le script ont été
remontés à l'utilisateur.
