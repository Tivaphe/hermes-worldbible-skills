---
name: story-outline
description: "Construit la structure d'un récit long (roman, novella, cycle) à partir d'une World Bible : prémisse, arcs de personnages, plan par parties et chapitres, gestion des révélations et de la tension. À utiliser pour planifier un livre, découper une histoire, créer un plan détaillé, ou restructurer un manuscrit existant. Trigger: plan, outline, structure, arc narratif, synopsis, découper en chapitres."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [worldbible, outline, plotting, writing]
    category: worldbible
    related_skills: [story-architect, lore-lookup, chapter-draft, continuity-ledger]
    config:
      - key: worldbible.bible_dir
        description: "Chemin absolu du dossier racine de la World Bible"
        default: "~/worldbible"
        prompt: "Dossier de votre World Bible"
      - key: worldbible.manuscript_dir
        description: "Dossier du manuscrit en cours"
        default: "~/manuscrit"
        prompt: "Dossier de votre manuscrit"
---

# Story Outline — un plan qui tient sur la durée

Un plan sert à trois choses : savoir quoi écrire chaque jour, repérer les trous avant
d'écrire, et ne pas perdre les fils sur 300 pages.

**Ce skill produit un plan plat, en un seul fichier.** C'est l'outil d'exploration : on y
essaie des structures, on compare des découpages, on cherche la prémisse.

Pour **construire** le livre et empêcher la dérive sur la durée, passer à `story-architect` :
raffinement par niveaux (livre → partie → chapitre → scène), contrat entrée/sortie par
chapitre, gel par empreinte et portes bloquantes. Règle pratique : `story-outline` pour
trouver la structure, `story-architect` pour la faire respecter.

## Quand utiliser

- Avant de démarrer un livre ou une longue nouvelle.
- Quand le manuscrit patine : restructurer, identifier les chapitres morts.
- Quand l'utilisateur demande un synopsis, un plan, un découpage.

## Procédure

### 1. Socle narratif (1 page max)

- **Prémisse** en une phrase : qui veut quoi, contre quoi, à quel prix.
- **Ce que le monde impose à l'histoire** : interroger la Bible avec `lore-lookup` sur les
  contraintes du monde (règles, pouvoirs, géographie, politique). Le conflit doit naître
  d'au moins une de ces contraintes, sinon le monde est du décor.
- **Promesse au lecteur** : quelle émotion, quel type de fin.
- **Format** : longueur cible en mots, nombre de parties et de chapitres, longueur moyenne
  d'un chapitre. Fixer ces nombres maintenant — ils structurent tout le plan.

### 2. Arcs de personnages

Pour chaque personnage principal (3 à 5 maximum) :
- désir conscient / besoin réel ;
- état initial → état final (mesurable, pas « il grandit ») ;
- ce qu'il croit au départ et qui est faux ;
- le personnage ou la force qui s'y oppose.

Vérifier chaque personnage dans la Bible : l'arc doit partir de qui il est **canoniquement**,
y compris de ses défauts déjà écrits.

### 3. Plan en trois passes

**Passe A — jalons** (5 à 9 lignes) : ouverture, premier basculement, milieu, point bas,
climax, résolution. Chaque jalon = un changement irréversible.

**Passe B — chapitres** : pour chaque chapitre, une ligne au format :

```
NN | POV | lieu/moment | ce qui change | révélation au lecteur | mots visés
```

« Ce qui change » est obligatoire : un chapitre où rien ne change est supprimé ou fusionné.

**Passe C — fils** : lister les intrigues secondaires et les mystères, puis noter pour chacun
le chapitre d'ouverture, les rappels intermédiaires, le chapitre de résolution. Un fil sans
résolution planifiée = dette narrative à signaler à l'utilisateur.

### 4. Carte des révélations

Tableau : information | qui la détient | qui l'apprend | chapitre | mode (dialogue, découverte,
conséquence). Sert à éviter les personnages qui savent des choses trop tôt ou trop tard —
la cause numéro un des incohérences de continuité.

### 5. Livrable

Écrire `manuscrit/outline.md` avec les sections 1 à 4. Chaque chapitre du plan doit pouvoir
être confié à `chapter-draft` sans nouvelle question.

## Pièges

- **Plan d'événements sans conséquences.** Chaque jalon doit laisser une trace vérifiable (état, objet, relation, savoir).
- **Chapitres uniformes.** Alterner longueurs et rythmes ; un plan où tous les chapitres font 3 000 mots produit un livre monotone.
- **Monde en décor.** Si aucune contrainte de la Bible ne crée de conflit, reprendre la prémisse.
- **Arcs non mesurables.** « Elle devient plus courageuse » ne se vérifie pas ; « elle refuse puis accepte de mentir au Conseil » se vérifie.
- **Tout révéler trop tôt.** Vérifier dans la carte des révélations qu'aucune information majeure ne fuite avant son chapitre.
- **Plan rigide.** Le plan se met à jour quand l'écriture découvre mieux : noter la modification dans outline.md, ne pas diverger en silence.

## Vérification

- Chaque chapitre du plan a un « ce qui change » non vide.
- Total des mots visés ≈ longueur cible annoncée (écart < 15 %).
- Chaque intrigue secondaire a un chapitre de résolution.
- Aucune contradiction avec la Bible : les lieux, époques et capacités cités dans le plan existent dans la Bible (vérification par `lore-lookup`).
