# Half Goals Intelligence Engine

Le `Half Goals Intelligence Engine` est le module principal de `Kairos` pour analyser la distribution des buts par mi-temps. Il ne produit pas un pronostic garanti : il estime une distribution probabiliste, explique ses limites et peut retourner `NO_BET` ou `INSUFFICIENT_DATA`.

## Marché HALF_GOAL_DOMINANCE
`HALF_GOAL_DOMINANCE` compare le nombre total de buts en première mi-temps et en deuxième mi-temps.

Les trois classes sont toujours calculées ensemble :
- `FIRST_HALF_MORE_GOALS` : la première mi-temps a plus de buts que la deuxième.
- `SECOND_HALF_MORE_GOALS` : la deuxième mi-temps a plus de buts que la première.
- `EQUAL_HALF_GOALS` : les deux mi-temps ont le même nombre de buts.

Après normalisation, la somme des trois probabilités doit être égale à 100 %.

## Sorties attendues
- Probabilités complètes des trois classes.
- Classe la plus probable, sans garantie de résultat.
- `confidence_score` séparé des probabilités.
- Intervalle ou bande d'incertitude lorsque le volume le permet.
- Calibration bucket spécifique au marché.
- Reason codes stables.
- Décision `ADVICE`, `WATCH`, `NO_BET` ou `INSUFFICIENT_DATA`.
- Provenance, fraîcheur, version modèle et snapshot de features.

## Probabilité vs confiance
La probabilité estime la chance qu'un scénario arrive selon le modèle.

La confiance estime la fiabilité de l'analyse selon :
- qualité et complétude des données ;
- fraîcheur des observations ;
- profondeur historique comparable ;
- stabilité de la calibration ;
- écart entre les trois scénarios ;
- cohérence multi-source ;
- domaine de validité du modèle.

Une classe peut avoir la probabilité la plus élevée avec une confiance faible. Dans ce cas, `Kairos Stake Guard` peut bloquer la recommandation.

## Données nécessaires
- Score final et score à la mi-temps.
- Minute des buts, temps additionnel et corrections officielles.
- Statut du match, reports, prolongations et annulations.
- Compétition, saison, équipe domicile, équipe extérieure et lieu.
- Historique par mi-temps des équipes et adversaires.
- Cotes horodatées du marché si disponibles, uniquement `as_of prediction_time`.
- Lineups, blessures, suspensions et contexte tactique seulement si disponibles avant `prediction_time`.
- Météo, repos, calendrier et déplacement lorsque couverts par des sources réelles.
- Provenance complète : `provider`, `provider_event_id`, `observed_at`, `fetched_at`, `available_at`, `source_version`, `quality_flags`, `raw_hash`.

## Features spécifiques
- Moyenne de buts 1H et 2H par équipe, domicile/extérieur.
- Ratio buts 1H / buts totaux et buts 2H / buts totaux.
- Tendance récente par mi-temps avec fenêtres datées.
- Force offensive et défensive ajustée à l'opposition par mi-temps.
- Fréquence de score nul à la mi-temps.
- Variance et surdispersion des buts par mi-temps.
- Écart de rythme entre 1H et 2H.
- Impact du calendrier, repos, déplacement et rotation attendue.
- Mouvement de cote horodaté avant décision, si couvert.
- Indicateurs de missing explicites, jamais remplacés silencieusement par zéro.

Toutes les features doivent être calculées `AS OF prediction_time`.

## Méthode statistique
Le modèle de base estime deux distributions de buts :
- `G1H` : buts attendus en première mi-temps ;
- `G2H` : buts attendus en deuxième mi-temps.

Approche de départ :
1. Estimer `lambda_1h` et `lambda_2h` par équipe, compétition et contexte.
2. Ajuster par force d'opposition, domicile/extérieur et forme temporelle.
3. Produire deux distributions discrètes pour `G1H` et `G2H`.
4. Calculer la distribution de différence `D = G1H - G2H`.
5. Agréger :
   - `P(FIRST_HALF_MORE_GOALS) = P(D > 0)`
   - `P(SECOND_HALF_MORE_GOALS) = P(D < 0)`
   - `P(EQUAL_HALF_GOALS) = P(D = 0)`
6. Normaliser les trois probabilités ensemble.

## Poisson ou Negative Binomial
Le modèle Poisson par mi-temps est la baseline minimale.

La Negative Binomial est autorisée si la surdispersion est démontrée hors échantillon, par compétition ou segment. Elle ne doit être retenue que si elle améliore Brier, log loss, calibration et stabilité walk-forward.

Les variantes plus complexes doivent rester secondaires tant qu'elles ne battent pas les baselines.

## Distribution de différence de buts
La distribution de `D = G1H - G2H` est le cœur du marché.

Elle peut être calculée par convolution des distributions discrètes :
- combiner chaque score possible `(g1h, g2h)` ;
- additionner les masses où `g1h > g2h` ;
- additionner les masses où `g1h < g2h` ;
- additionner les masses où `g1h = g2h`.

Les queues de distribution doivent être tronquées explicitement avec une masse résiduelle documentée.

## Permutations possibles
Pour chaque match, le moteur évalue les couples `(g1h, g2h)` plausibles :
- `(0, 0)`, `(1, 0)`, `(0, 1)`, `(1, 1)` ;
- scores supérieurs jusqu'au seuil de troncature ;
- regroupement des queues rares si le volume est faible.

Chaque permutation conserve sa probabilité, sa contribution à la classe finale et les hypothèses utilisées.

## Simulation Monte Carlo
La simulation Monte Carlo peut compléter le calcul exact :
1. Tirer `G1H` et `G2H` depuis les distributions calibrées.
2. Répéter avec un nombre d'itérations documenté.
3. Estimer les fréquences des trois classes.
4. Comparer la simulation au calcul analytique.
5. Échouer ou dégrader en `WATCH`/`NO_BET` si l'écart dépasse le seuil validé.

La simulation ne doit pas masquer une mauvaise calibration.

## Calibration
La calibration est spécifique à `HALF_GOAL_DOMINANCE` et aux trois classes :
- `1H > 2H`
- `2H > 1H`
- `1H = 2H`

Rapports requis :
- Brier multiclasses ;
- log loss multiclasses ;
- ECE/MCE par classe ;
- reliability diagram par classe ;
- taille des buckets et intervalles ;
- segmentation par compétition, saison, marché, domicile/extérieur et confiance.

Une calibration globale ne suffit pas si une classe est mal calibrée.

## Confidence score
`confidence_score` est un score de fiabilité, pas une probabilité de victoire du scénario.

Facteurs recommandés :
- `data_quality_score`
- `freshness_score`
- `coverage_score`
- `calibration_score`
- `scenario_separation_score`
- `market_consistency_score`
- `model_stability_score`

Une faible séparation entre les trois classes réduit la confiance, même si les probabilités sont normalisées.

## Reason codes
Reason codes recommandés :
- `HALF_GOAL_DOMINANCE_PRIMARY_MARKET`
- `FIRST_HALF_PRESSURE_PROFILE`
- `SECOND_HALF_SCORING_TREND`
- `EQUAL_HALVES_HIGH_TIE_MASS`
- `LOW_SCENARIO_SEPARATION`
- `INSUFFICIENT_HALF_TIME_HISTORY`
- `STALE_HALF_GOAL_DATA`
- `MISSING_HALF_TIME_SCORE`
- `POOR_CLASS_CALIBRATION`
- `OUT_OF_DOMAIN_COMPETITION`
- `LINEUP_CONTEXT_UNAVAILABLE`
- `ODDS_STALE_OR_MISSING`
- `TEMPORAL_GUARD_BLOCKED`

Les reason codes doivent refléter le calcul réel et ne jamais être inventés après coup.

## Règles NO_BET
Retourner `NO_BET` ou `INSUFFICIENT_DATA` si :
- score mi-temps ou minute des buts absent pour l'historique requis ;
- données de mi-temps trop anciennes ou couverture insuffisante ;
- compétition hors domaine ;
- divergence critique entre fournisseurs sur score HT/FT ou minutes de buts ;
- calibration faible sur l'une des trois classes ;
- séparation trop faible entre les scénarios ;
- `confidence_score` sous le seuil validé ;
- observation utilisée avec `available_at > prediction_time` ;
- cotes manquantes ou stale lorsque la décision dépend du prix ;
- changement de régime non couvert : entraîneur, effectif, format de compétition ou règle de match.

## Exemple JSON
```json
{
  "prediction_id": "pred_01HGDRAFT",
  "market": "HALF_GOAL_DOMINANCE",
  "model_version": "kairos-half-goals-0.1.0",
  "feature_snapshot_id": "fs_half_goals_2026_0001",
  "prediction_time": "2026-06-26T12:00:00Z",
  "probabilities": {
    "FIRST_HALF_MORE_GOALS": 31.4,
    "SECOND_HALF_MORE_GOALS": 42.8,
    "EQUAL_HALF_GOALS": 25.8
  },
  "probability_sum": 100.0,
  "top_class": "SECOND_HALF_MORE_GOALS",
  "confidence_score": 0.62,
  "calibration_bucket": "half_goal_dominance:p40_p50",
  "decision": "WATCH",
  "reasons": [
    "SECOND_HALF_SCORING_TREND",
    "LOW_SCENARIO_SEPARATION"
  ],
  "data_freshness": {
    "half_time_scores": "P2D",
    "odds_snapshot": "PT15M"
  },
  "odds_snapshot_id": "odds_01HGDRAFT",
  "immutable_hash": "sha256:example-not-production"
}
```

Cet exemple est illustratif et ne doit jamais être présenté comme une prédiction réelle.

## Limites du modèle
- Les buts sont rares, donc les classes peuvent rester proches.
- Les effets tactiques par mi-temps sont difficiles à mesurer sans données riches.
- Les compétitions avec faible couverture peuvent produire beaucoup de `NO_BET`.
- Les changements d'entraîneur, règles, calendrier ou effectif peuvent casser les tendances.
- Le marché peut être utile analytiquement sans être exploitable financièrement.
- Une probabilité élevée ne garantit pas le résultat.
- La confiance dépend de la qualité des données et de la calibration observée.
