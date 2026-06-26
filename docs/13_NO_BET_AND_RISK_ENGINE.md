# Kairos Stake Guard & NO_BET Engine

## Décisions
- `ADVICE`
- `WATCH`
- `NO_BET`
- `INSUFFICIENT_DATA`
- `SUSPENDED`

## Déclencheurs
Données anciennes, composition critique inconnue, divergence majeure, calibration faible, absence d’edge, cote stale, compétition hors domaine, changement de régime, incident live ou drift.

`Kairos Stake Guard` peut bloquer `Kairos`. `Kairos` ne peut jamais le contourner.

## Règles HALF_GOAL_DOMINANCE
Pour `HALF_GOAL_DOMINANCE`, retourner `NO_BET` ou `INSUFFICIENT_DATA` si :
- les scores mi-temps, scores finaux ou minutes de buts nécessaires sont absents ;
- la couverture historique par mi-temps est insuffisante pour la compétition ou les équipes ;
- une divergence fournisseur critique touche le score HT/FT ou les minutes de buts ;
- les trois classes sont trop proches pour produire une décision fiable ;
- la calibration est faible sur `FIRST_HALF_MORE_GOALS`, `SECOND_HALF_MORE_GOALS` ou `EQUAL_HALF_GOALS` ;
- le `confidence_score` est inférieur au seuil validé ;
- une feature dépend d'une observation avec `available_at > prediction_time` ;
- les cotes sont stale ou manquantes lorsque la décision dépend du prix ;
- le match est hors domaine : format atypique, prolongations probables, compétition non couverte, changement de régime majeur.

La décision doit inclure des reason codes stables, par exemple `LOW_SCENARIO_SEPARATION`, `INSUFFICIENT_HALF_TIME_HISTORY`, `STALE_HALF_GOAL_DATA`, `MISSING_HALF_TIME_SCORE`, `POOR_CLASS_CALIBRATION` ou `TEMPORAL_GUARD_BLOCKED`.
