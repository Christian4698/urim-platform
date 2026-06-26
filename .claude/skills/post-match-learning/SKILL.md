---
name: post-match-learning
description: Spécifier, auditer ou implémenter le Post-Match Learning Engine de URIM, incluant la comparaison prédiction vs résultat officiel, la séparation entre déclarations utilisateur et vérité officielle, le journal immuable, la recalibration, l'amélioration du NO_BET et l'identification des marchés et championnats fiables.
---

# post-match-learning

1. Lire `docs/37_POST_MATCH_LEARNING_ENGINE.md`, `docs/23_FAILURE_CATALOG_84.md`, `docs/11_BACKTESTING_PROTOCOL.md`, `docs/07_TEMPORAL_INTEGRITY.md` et `docs/13_NO_BET_AND_RISK_ENGINE.md`.
2. Traiter les résultats officiels vérifiés comme seule base d'apprentissage.
3. Ne jamais apprendre directement depuis une déclaration utilisateur non vérifiée.
4. Préserver le journal immuable des prédictions `Kairos`.
5. Comparer systématiquement prédiction, décision, confiance et résultat officiel.
6. Segmenter les rapports par marché, championnat, confiance et comportement `NO_BET`.
7. Alimenter recalibration, fiabilité des marchés et amélioration du `NO_BET` sans réécrire l'historique.
8. Bloquer toute utilisation d'une donnée postérieure à `prediction_time`.
9. Produire des reason codes de vérification et d'erreur du modèle.
10. Ne jamais transformer un gain utilisateur déclaré en vérité d'entraînement sans vérification officielle.

## Sortie attendue
- Résumé
- Fichiers modifiés
- Tests exécutés
- Risques restants
- IDs E001–E084 concernés
