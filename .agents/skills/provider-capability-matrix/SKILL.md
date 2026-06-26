---
name: provider-capability-matrix
description: Specifier, auditer ou mettre a jour la matrice de capacites fournisseurs URIM, incluant statuts provider, couverture, limites, quality flags, activation MVP et interdiction de fallback mock silencieux.
---

# provider-capability-matrix

1. Lire `docs/38_PROVIDER_CAPABILITY_MATRIX.md`, `docs/04_REAL_DATA_SOURCES.md`, `docs/05_PROVIDER_CONNECTOR_CONTRACT.md` et `docs/28_PROVIDER_ONBOARDING_CHECKLIST.md`.
2. Classer les providers avec `PRIMARY_MVP`, `SECONDARY_MVP`, `VALIDATION_ONLY`, `ODDS_ONLY`, `RESEARCH_ONLY` ou `ENTERPRISE_LATER`.
3. Classer chaque capacite avec `SUPPORTED`, `PARTIAL`, `MISSING`, `UNKNOWN` ou `FUTURE`.
4. Ne jamais transformer une capacite `PARTIAL`, `MISSING` ou `UNKNOWN` en donnee utilisable sans `quality_flags`.
5. Bloquer toute activation production sans documentation officielle, licence, couverture, secrets serveur, tests de contrat et data quality gate.
6. Ne jamais coder de connecteur reel pendant une phase documentaire.
7. Ne jamais accepter de fallback mock silencieux en production.

## Sortie attendue
- Resume
- Fichiers modifies
- Tests executes
- Risques restants
- IDs E001-E084 concernes
