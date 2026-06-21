# Moteur live

## Entrées
Score, minute, événements, cartons, remplacements, statistiques live, composition, cotes live et qualité/latence du flux.

## Contraintes
- Modèle distinct du pré-match.
- Flux ordonné, dédupliqué et corrigible.
- Seuil de latence par marché.
- Suspension sur incohérence.
- Chaque recalcul crée une nouvelle version.

## Sortie
Probabilité actuelle, delta, événement déclencheur, fraîcheur, risque et décision.
