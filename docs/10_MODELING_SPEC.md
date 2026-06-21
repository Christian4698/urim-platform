# Spécification de modélisation

## Modèles séparés
- Résultat 1X2
- Totaux de buts
- Both Teams To Score
- Score exact comme distribution secondaire seulement
- Live distinct du pré-match

## Baselines obligatoires
Fréquences historiques, Poisson simple, régression logistique et probabilités implicites du marché corrigées de la marge.

## Candidats
Gradient boosting, modèles hiérarchiques bayésiens, Poisson/Dixon-Coles selon usage, réseaux temporels après preuve de gain, ensembles calibrés.

## Sortie
Distribution complète, incertitude, version, domaine de validité, variables principales, drapeaux de données, calibration bucket et décision du Risk Engine.

Le modèle complexe n’est retenu que s’il améliore les métriques hors échantillon et reste stable par saison, ligue et marché.
