# Structure recommandée d'une World Bible

Référence du skill `lore-lookup`. À lire quand la Bible est désordonnée, quand l'index donne
des résultats médiocres, ou quand l'utilisateur veut réorganiser.

## Pourquoi la structure change tout

L'index découpe les fichiers **sur les titres Markdown**. Une Bible en longs paragraphes sans
titres produit des blocs énormes et des réponses floues. Une Bible bien titrée produit des
réponses précises et sourçables. La règle d'or : **un fait par bloc, un titre qui nomme le fait**.

## Arborescence conseillée

```
worldbible/
├── 00-vision.md              # ton, thèmes, promesses, ce que le monde N'EST PAS
├── 00-glossaire.md           # orthographe officielle des noms et termes
├── monde/
│   ├── geographie.md         # régions, distances, climat, voyages
│   ├── magie.md              # règles DURES (limites, coûts) puis applications
│   ├── technologie.md
│   ├── societe.md            # pouvoirs, lois, classes, économie
│   └── croyances.md
├── personnages/
│   └── <prenom-nom>.md       # un fichier par personnage important
├── factions/
│   └── <faction>.md
├── lieux/
│   └── <lieu>.md
├── objets/
│   └── <objet>.md
├── histoire/
│   └── chronologie.md        # dates absolues + événements
└── regles-du-recit.md        # ce que l'histoire ne fera jamais, POV autorisé, etc.
```

Les noms numériques (`00-`) forcent l'ordre de lecture. Les sous-dossiers thématiques aident
l'agent à deviner où chercher.

## Conventions d'écriture

1. **Un titre = un fait vérifiable.**
   - Mal : `## Notes sur la magie`
   - Bien : `## Règles dures du Souffle`
2. **Puces pour les règles, prose pour le contexte.** Les règles en liste à puces se citent
   proprement et se contrôlent en continuité.
3. **Noms officiels en gras à la première occurrence** d'un bloc : `**Kaelin Marre**`.
4. **Dates absolues** (`An 431`) plutôt que relatives (« trois ans après »).
5. **Un seul endroit par fait.** Si un fait est répété dans trois fichiers, il finira par
   diverger. Choisir le fichier de référence et écrire ailleurs : `→ voir monde/magie.md`.
6. **Marquer l'incertain** : `<!-- à trancher : … -->` ou une section `## Lacunes`.
7. **Écrire ce que le monde n'est pas** autant que ce qu'il est : c'est ce qui empêche
   l'agent d'inventer des incohérences séduisantes.

## Sections utiles dans chaque fichier d'entité

`personnages/kaelin.md` :

```
# Kaelin Marre
## Identité (âge, origine, apparence distinctive)
## Capacités et limites
## Relations
## Ce qu'elle sait / ignore     ← crucial pour la continuité
## Arc prévu (si connu)
## Lacunes
```

La section « Ce qu'elle sait / ignore » est la plus rentable de toute la Bible : c'est elle
qui évite les personnages qui apprennent trop tôt une révélation.

## Diagnostic rapide

```bash
python3 scripts/wb_index.py --bible <DOSSIER_BIBLE> --stats
```

Signes d'alerte :
- blocs moyens > 900 mots → découper avec des titres ;
- un fichier avec 1 seul bloc → fichier sans titre, à titrer ;
- fichier > 3 000 mots → le scinder par thème.

## Réorganisation

Ne jamais réécrire la Bible sans accord. Procédure sûre : copier dans `worldbible-old/`,
réorganiser la copie, diff, puis faire valider fichier par fichier. Après toute modification :
reconstruire l'index.
