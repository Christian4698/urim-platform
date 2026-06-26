# Calibration et évaluation

Une sortie à 80 % doit réussir environ 80 fois sur 100 cas comparables, avec volume suffisant.

## Techniques
Platt scaling, isotonic regression, temperature scaling, calibration par marché/compétition si le volume le permet.

## Calibration HALF_GOAL_DOMINANCE
Le marché principal `HALF_GOAL_DOMINANCE` exige une calibration multiclasses dédiée aux trois classes :
- `FIRST_HALF_MORE_GOALS` (`1H > 2H`)
- `SECOND_HALF_MORE_GOALS` (`2H > 1H`)
- `EQUAL_HALF_GOALS` (`1H = 2H`)

Les trois probabilités sont évaluées ensemble après normalisation à 100 %. Les rapports doivent inclure Brier multiclasses, log loss multiclasses, ECE/MCE par classe, reliability diagram par classe, taille des buckets et intervalles de confiance.

La calibration doit être segmentée par compétition, saison, marché, domicile/extérieur, couverture historique et niveau de confiance. Une classe mal calibrée peut déclencher `WATCH`, `NO_BET` ou `INSUFFICIENT_DATA`, même si la calibration globale semble acceptable.

`confidence_score` ne remplace jamais la probabilité : il mesure la fiabilité de l'analyse selon qualité, fraîcheur, couverture, stabilité, calibration et séparation entre scénarios.

## Rapports
Reliability diagram, Brier decomposition, ECE/MCE, taille des buckets, intervalles, comparaison baseline/bookmaker, avant/après calibration.

## Interdit
Revendiquer « 80 % » sans marché, période, nombre de prédictions, cotes moyennes, couverture, méthode et intervalle de confiance.
