---
name: half-goals-intelligence
description: Spécifier, auditer ou implémenter le Half Goals Intelligence Engine et le marché HALF_GOAL_DOMINANCE, incluant les probabilités FIRST_HALF_MORE_GOALS, SECOND_HALF_MORE_GOALS, EQUAL_HALF_GOALS, la calibration multiclasses, les features par mi-temps, le confidence score et les règles NO_BET associées.
---

# half-goals-intelligence

1. Lire `docs/29_HALF_GOALS_INTELLIGENCE_ENGINE.md`, `docs/10_MODELING_SPEC.md`, `docs/12_CALIBRATION_AND_EVALUATION.md`, `docs/13_NO_BET_AND_RISK_ENGINE.md` et `docs/07_TEMPORAL_INTEGRITY.md`.
2. Traiter `HALF_GOAL_DOMINANCE` comme marché principal de `Kairos`.
3. Calculer toujours ensemble `FIRST_HALF_MORE_GOALS`, `SECOND_HALF_MORE_GOALS` et `EQUAL_HALF_GOALS`.
4. Normaliser les trois probabilités pour obtenir 100 % après normalisation.
5. Séparer `probability` et `confidence_score`.
6. Utiliser des features `AS OF prediction_time`, avec missing explicite et provenance vérifiable.
7. Commencer par des baselines Poisson ou Negative Binomial par mi-temps avant toute complexité.
8. Évaluer Brier multiclasses, log loss, ECE/MCE par classe, calibration par segment et stabilité walk-forward.
9. Retourner `NO_BET` ou `INSUFFICIENT_DATA` si les données de mi-temps, la fraîcheur, la calibration, la couverture ou la séparation des scénarios sont insuffisantes.
10. Ne jamais présenter une probabilité élevée comme une garantie.

## Sortie attendue
- Résumé
- Fichiers modifiés
- Tests exécutés
- Risques restants
- IDs E001–E084 concernés
