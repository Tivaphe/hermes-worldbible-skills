---
name: continuity-check
description: "Contrôle de cohérence d'un texte (chapitre, nouvelle, article) contre la World Bible : entités inconnues, contradictions de faits, erreurs de chronologie. À utiliser après chaque écriture de texte se déroulant dans l'univers, avant toute validation ou export. Trigger: vérifier cohérence, continuité, canon, relire, contradiction, bible."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [worldbible, continuity, qa, writing]
    category: worldbible
    related_skills: [lore-lookup, continuity-ledger]
    config:
      - key: worldbible.bible_dir
        description: "Chemin absolu du dossier racine de la World Bible"
        default: "~/worldbible"
        prompt: "Dossier de votre World Bible"
---

# Continuity Check — confronter un texte au canon

Le script détecte la **présence**. Le modèle juge le **sens**. Les deux sont obligatoires :
un rapport de script seul n'est pas un contrôle de continuité.

## Quand utiliser

- Après la rédaction d'un chapitre ou de tout texte dans l'univers.
- Avant de considérer un texte comme « terminé » ou de l'exporter.
- Quand l'utilisateur dit « vérifie », « c'est cohérent ? », « ça colle à la bible ? ».

## Procédure

1. **Contrôle automatique des entités** (index à jour requis, sinon le reconstruire via le skill `lore-lookup`) :

   ```bash
   python3 ${HERMES_SKILL_DIR}/scripts/wb_entities.py --draft <FICHIER> --bible <DOSSIER_BIBLE>
   ```

   Sortie : trois listes — `CONFIRMEES` (avec preuve), `MENTIONS FAIBLES`, `A VERIFIER` (absentes de la Bible).

2. **Traiter chaque entité « A VERIFIER »** : chercher dans la Bible avec `lore-lookup`. Trois issues possibles, à trancher explicitement :
   - orthographe différente d'une entité existante → corriger le texte ;
   - invention volontaire → la déclarer dans le registre (skill `continuity-ledger`) ;
   - invention accidentelle → supprimer ou remplacer.

3. **Contrôle sémantique.** Extraire du texte 5 à 15 affirmations factuelles (âges, distances, durées, hiérarchies, qui sait quoi, qui est vivant, état d'un objet) et pour chacune vérifier dans la Bible avec `lore-lookup`. C'est ici que se trouvent les vraies contradictions — le script ne les voit jamais.

4. **Contrôle chronologique** : dates, saisons, durées de voyage, âge des personnages au moment de la scène. Comparer à la chronologie de la Bible.

5. **Produire le rapport** (format ci-dessous) et **ne pas corriger sans accord** quand le correctif change l'intrigue.

## Format du rapport

```
CONTRÔLE — <fichier> — <date>

1. Contradictions (bloquant)
   • <fait du texte>  ✗  <fait canonique>  [fichier :: titre]
   → correction proposée : …

2. Entités inconnues (à trancher)
   • <entité> (x3) → invention / faute / à supprimer ?

3. Chronologie
   • <incohérence ou « rien à signaler »>

4. Verdict : PRÊT / À CORRIGER (N points bloquants)
```

## Pièges

- **Ne signaler que les entités.** Le plus grave — une contradiction de fait — est invisible au script. L'étape 3 n'est pas optionnelle.
- **Corriger le texte pour le faire coller au script.** Le script a des faux positifs (« Soufflerie » absent parce que la Bible écrit « Souffleries »). Juger avant d'éditer.
- **Valider sans preuve citée.** Toute ligne « contradiction » doit porter `fichier :: titre`.
- **Ignorer les mentions faibles.** Une seule source légère, c'est souvent un détail jamais fixé : à trancher, pas à ignorer.

## Vérification

Le rapport doit comporter un verdict chiffré et au moins une preuve `[fichier :: titre]` par
contradiction signalée. Relancer le script après correction : le compteur `inconnues` doit baisser.
