# Intégrité temporelle — règle suprême

## Invariant
Pour une prédiction à l’heure `T`, aucune entrée avec `available_at > T` ne peut être utilisée.

## Horodatages
- `event_time`
- `provider_observed_at`
- `available_at`
- `fetched_at`
- `processed_at`
- `prediction_time`

## Garde-fous
- Features obligatoirement `AS OF prediction_time`.
- Split chronologique.
- Normalisation apprise uniquement sur le train.
- Sélection de variables sans regarder le test.
- Dernière cote disponible avant la décision.
- Lineup officielle seulement après publication.
- Statistiques cumulées excluant le match cible.
- Tests temporels adversariaux.

## Test bloquant
Le build échoue si une feature peut lire une ligne future.

Chaque prédiction stocke les observations exactes et leurs hashes.
