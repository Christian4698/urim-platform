# Spécification de modélisation — Kairos

`Kairos` est le cerveau analytique de `URIM`. Il produit des probabilités calibrées, mais ne contourne jamais les garde-fous de risque.

## Modèles séparés
- `HALF_GOAL_DOMINANCE` comme marché principal du produit via `Half Goals Intelligence Engine`
- Résultat 1X2
- Totaux de buts
- Both Teams To Score
- Score exact comme distribution secondaire seulement
- Live distinct du pré-match

Les autres marchés restent supportés comme marchés secondaires. Ils ne doivent pas diluer le cœur produit : l'analyse avancée de la distribution des buts par mi-temps.

## Marché principal HALF_GOAL_DOMINANCE
Le marché `HALF_GOAL_DOMINANCE` produit toujours trois probabilités normalisées ensemble :
- `FIRST_HALF_MORE_GOALS`
- `SECOND_HALF_MORE_GOALS`
- `EQUAL_HALF_GOALS`

La somme des trois probabilités doit être égale à 100 % après normalisation. Le modèle doit distinguer la probabilité d'un scénario et le `confidence_score`, qui mesure la fiabilité de l'analyse selon la qualité des données, la fraîcheur, la calibration, la couverture historique et l'écart entre les scénarios.

## Baselines obligatoires
Fréquences historiques, Poisson simple, régression logistique et probabilités implicites du marché corrigées de la marge.

## Candidats
Poisson ou Negative Binomial par mi-temps pour `HALF_GOAL_DOMINANCE`, puis gradient boosting, modèles hiérarchiques bayésiens, Poisson/Dixon-Coles selon usage, réseaux temporels après preuve de gain, ensembles calibrés.

## Sortie
Distribution complète, incertitude, version, domaine de validité, variables principales, drapeaux de données, calibration bucket et décision de `Kairos Stake Guard`.

Le modèle complexe n’est retenu que s’il améliore les métriques hors échantillon et reste stable par saison, ligue et marché.

Voir `docs/29_HALF_GOALS_INTELLIGENCE_ENGINE.md` pour la spécification détaillée du moteur principal.
