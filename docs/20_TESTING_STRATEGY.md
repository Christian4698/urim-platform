# Stratégie de tests

## Pyramide
Unitaires, contrats, normalisation, intégration, temporalité, property-based, end-to-end, charge, sécurité et régression modèle.

## Tests obligatoires
- Futur exclu d’un snapshot passé.
- Lineup et cote postérieures à T exclues.
- Réponse vide reste `missing`.
- Idempotence.
- Divergence critique bloque.
- Aucun secret dans les logs.
- Prédiction publiée immuable.
- Production refuse les fixtures.
- Live suspendu si latence excessive.
