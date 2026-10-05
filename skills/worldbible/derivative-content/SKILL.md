---
name: derivative-content
description: "Produit des contenus dérivés d'une World Bible autres que le roman : fiches et codex de wiki, encyclopédie du monde, nouvelles et contes, documents in-universe (journaux, lettres, rapports), aides de jeu (JDR), scripts vidéo ou podcast, posts et fils de vulgarisation de l'univers. À utiliser pour décliner le monde dans un autre format. Trigger: wiki, codex, encyclopédie, document in-universe, journal de bord, aide de jeu, JDR, script vidéo, post sur l'univers, nouvelle dérivée."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [worldbible, transmedia, wiki, writing]
    category: worldbible
    related_skills: [lore-lookup, continuity-check, style-guide]
    config:
      - key: worldbible.bible_dir
        description: "Chemin absolu du dossier racine de la World Bible"
        default: "~/worldbible"
        prompt: "Dossier de votre World Bible"
---

# Derivative Content — décliner l'univers dans d'autres formats

Chaque format a ses règles propres, mais une seule loi commune : **le canon d'abord**.
Un contenu dérivé qui invente sans le dire devient une contradiction.

## Quand utiliser

Pour tout ce qui n'est pas le récit principal : wiki/codex, encyclopédie, nouvelles,
documents in-universe, aides de jeu, scripts, posts.

## Procédure commune (tout format)

1. **Choisir le statut du texte** — décision explicite, à écrire en tête de fichier :
   - `CANON` : fait partie de l'univers officiel. Rien d'inventé sans enregistrement.
   - `IN-UNIVERSE NON CANON` : écrit « depuis l'intérieur » (un personnage se trompe, ment,
     ignore). La contradiction est un effet voulu — l'annoter.
   - `HORS-CANON` : fanfiction, variante, brouillon. Le marquer visiblement.
2. **Dossier canonique** : récupérer avec `lore-lookup` tous les faits nécessaires. Interdiction
   d'écrire un détail du monde absent du dossier sans le vérifier.
3. **Écrire** dans le format (spécifications ci-dessous).
4. **Contrôler** avec `continuity-check`, puis enregistrer les nouveautés dans la Bible ou le
   registre (avec accord de l'utilisateur si c'est la Bible).

## Spécifications par format

### Wiki / codex (fiches d'entités)
Une fiche = une entité. Structure fixe :
`Infobox (type, localisation, époque, statuts) → Définition en 2 phrases → Description → Histoire → Relations → Sources (fichiers de la Bible) → Lacunes`.
La section **Lacunes** est obligatoire : elle liste ce que la Bible ne dit pas. C'est ce qui
empêche d'inventer en silence. Une fiche sans source est refusée.

### Encyclopédie / livre du monde
Ordre thématique, pas alphabétique. Chaque entrée se termine par sa source. Longueur homogène
entre entrées d'un même niveau (définir : entrée courte 200-400 mots, longue 800-1200).
Signaler les entrées qui se contredisent entre fichiers de la Bible plutôt que de trancher seul.

### Nouvelle / conte dérivé
Même procédure que `chapter-draft` (cadrage, dossier canonique, écriture, contrôle), en plus
court : un seul POV, une seule idée, une fin. 1 500 à 6 000 mots, mesurés.

### Document in-universe (journal, lettre, rapport, inscription)
C'est le format le plus riche et le plus piégeux. Le scripteur **doit** avoir un point de vue
limité et des biais : il ne sait pas tout, il ment parfois. Écrire d'abord *qui écrit, à qui,
quand, dans quel but, et ce qu'il ignore*. Annoter le fichier avec les erreurs volontaires,
sinon un futur passage les prendra pour des contradictions.

### Aide de jeu (JDR)
Séparer explicitement : ce que savent les personnages / ce que sait le meneur. Chaque règle
doit renvoyer à sa justification dans la Bible. Les chiffres (difficultés, distances, durées)
doivent respecter les contraintes canoniques (si la Bible dit « neuf minutes », la règle ne
peut pas en donner vingt).

### Script vidéo / podcast / post
Adapter, ne pas résumer. Choisir **un** angle par contenu (une question, un mystère, une
entité). Indiquer les repères de temps et les intentions de voix. Pour un post : accroche en
une phrase, trois informations maximum, chute. Longueur calibrée : ~130-150 mots/minute de
voix parlée.

## Pièges

- **Statut non déclaré.** Sans `CANON` / `NON CANON` / `HORS-CANON`, une erreur devient un conflit insoluble.
- **Fiche de wiki sans lacunes.** Elle pousse à inventer pour combler les vides.
- **Résumé plat en script.** Une vidéo qui récite la Bible endort ; il faut une question et une révélation.
- **Document in-universe omniscient.** Un journal intime qui explique tout le monde n'est crédible pour personne.
- **Nouveautés non répercutées.** Le contenu dérivé crée du canon : il doit être enregistré, sinon le roman suivant le contredit.

## Vérification

Chaque fichier livré porte en tête son **statut** et sa **date** ; chaque fiche de codex a une
section `Sources` non vide et une section `Lacunes` ; le rapport `continuity-check` est joint
ou son verdict cité.
