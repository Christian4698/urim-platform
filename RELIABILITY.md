# RELIABILITY.md

- Aucun fournisseur unique ne constitue toute la vérité.
- Tout connecteur possède timeout, retry exponentiel, jitter, circuit breaker et quota budget.
- Une donnée stale ne doit pas être réutilisée silencieusement.
- États : `HEALTHY`, `DEGRADED`, `STALE`, `UNAVAILABLE`.
- Les prédictions live cessent si la fraîcheur dépasse le seuil autorisé.
- Les divergences multi-sources sont conservées et expliquées.
- Les événements sont idempotents.
- Les prédictions publiées sont immuables et versionnées.
