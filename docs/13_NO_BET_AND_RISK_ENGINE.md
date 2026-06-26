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

## États Kairos Stake Guard
- `KAIROS_DORMANT` : pas de signal exploitable, mise `0 CDF`.
- `KAIROS_ATTENTIVE` : signal à surveiller, décision `WATCH`, mise `0 CDF`.
- `KAIROS_AWAKENED` : autorise l'affichage `Kairos éveillé` et une fourchette prudente si tous les seuils sont respectés.
- `KAIROS_LOCKED` : garde-fou activé, décision `NO_BET` ou `SUSPENDED`, mise `0 CDF`.
- `NO_BET` : refus explicite, aucune fourchette de mise.

## Règles de mise prudente
Retourner `NO_BET`, `INSUFFICIENT_DATA` ou `SUSPENDED` si :
- `bankroll_cdf` est absent alors qu'une fourchette est demandée ;
- la mise proposée dépasserait `0.5 %` du bankroll par match ;
- l'exposition journalière dépasserait `1.0 %` du bankroll ;
- plus de 3 rencontres sont déjà retenues pour la journée ;
- la fourchette dépend seulement de la probabilité sans cote, confiance, calibration, qualité des données et risque global ;
- une stratégie de martingale, de récupération des pertes ou de surmise est détectée ;
- la cote est stale ou absente lorsque la décision dépend du prix ;
- `confidence_score < 0.70`, `calibration_score < 0.70`, `data_quality_score < 0.75` ou `adjusted_edge < 0.03` pour un statut `KAIROS_AWAKENED`.

Les montants doivent rester des intervalles `stake_interval_cdf`, jamais des ordres fixes.

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

Voir `docs/35_KAIROS_STAKE_GUARD.md` pour les seuils, expositions et sorties attendues.
