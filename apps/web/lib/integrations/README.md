# integrations/ (structure préparée, non branchée)

Scaffolding en attente — aucune API tierce n'est câblée ici.

- `providers/` : futurs wrappers typés côté client, pointant uniquement vers nos propres endpoints backend (`apps/api`). Jamais d'appel direct à une API tierce depuis ce dossier (clé API interdite côté frontend, voir `AGENTS.md`).
- `mocks/` : implémentations mock/demo à activer par défaut.
- `types/` : types TypeScript reflétant les contrats de données, pas les réponses brutes des fournisseurs.

Toute intégration réelle de fournisseur tiers (API-Football, odds, etc.) reste gérée côté backend dans `apps/api/app/modules/providers/`, conformément à `docs/05_PROVIDER_CONNECTOR_CONTRACT.md`. Voir `docs/api-catalog.md` et `docs/codex-api-integration-instructions.md` avant toute activation.
