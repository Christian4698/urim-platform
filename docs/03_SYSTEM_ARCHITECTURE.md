# Architecture système — URIM

## Vue d'ensemble

```text
Fournisseurs réels
  ├─ Matchs / classements / effectifs
  ├─ Événements et statistiques
  ├─ Compositions / blessures
  ├─ Cotes horodatées
  └─ Météo / contexte vérifié
          │
          ▼
Connector Gateway  (services/ingestion)
  ├─ Auth serveur uniquement (secret manager)
  ├─ Rate limiting + quotas
  ├─ Retry ciblé + backoff exponentiel + jitter
  ├─ Circuit breaker par fournisseur
  ├─ Raw payload archivé (raw_hash + payload_location)
  └─ Provider health score
          │
          ▼
Canonical Data Layer  (services/ingestion)
  ├─ Entity resolution (équipe, compétition, joueur)
  ├─ Validation stricte (schémas Pydantic)
  ├─ Réconciliation multi-source
  ├─ Provenance par champ (provider, observed_at, available_at)
  └─ Temporal availability guard (available_at <= prediction_time)
          │
          ▼
PostgreSQL 16 + TimescaleDB / Redis 7 / Object Storage
          │
          ├──────────────────────────┐
          ▼                          ▼
Feature Store                 Live Event Stream
  (services/prediction)        (services/live-engine)
          │                          │
          └──────────┬───────────────┘
                     ▼
Kairos  (services/prediction)
  ├─ Pré-match : Half Goals Intelligence Engine (marché principal)
  ├─ Marchés secondaires : 1X2, TOTAL_GOALS, BTTS
  ├─ Calibration multiclasses (Brier, log loss, ECE/MCE)
  ├─ Simulation Monte Carlo
  ├─ Kairos Stake Guard / NO_BET Engine (autorité bloquante)
  └─ Explanation + reason codes
                     │
                     ▼
Immutable Prediction Ledger  (append-only, immutable_hash)
                     │
          ┌──────────┴──────────────┐
          ▼                          ▼
   apps/api (FastAPI)          services/messaging
          │                    (Messagerie agents)
          ▼                          │
   apps/web (Next.js)          Audit / alertes
          │
          ▼
URIM Dashboard + Bet Center
```

## Stack technique

| Composant | Technologie | Version cible |
|---|---|---|
| Backend API | FastAPI | 0.111+ |
| Runtime Python | Python | 3.12+ |
| Frontend | Next.js (App Router) | 14+ |
| Base de données principale | PostgreSQL | 16 |
| Extension séries temporelles | TimescaleDB | 2.x |
| Cache et broker | Redis | 7+ |
| Worker asynchrone | Celery | 5.x |
| Migrations | Alembic | 1.x |
| Validation des données | Pydantic v2 | 2.x |
| Tests | pytest + pytest-asyncio | latest |
| Linting / types | ruff + mypy | latest |
| Conteneurisation | Docker + Docker Compose | v25+ |
| CI | GitHub Actions | — |
| Secret manager | GCP Secret Manager ou HashiCorp Vault | — |

## Découpage en packages

```text
URIM/
├── apps/
│   ├── web/                  # Next.js — URIM Dashboard + Bet Center
│   └── api/                  # FastAPI — point d'entrée client unique
├── services/
│   ├── ingestion/            # Connectors, normalisation, provenance
│   ├── prediction/           # Kairos, features, modèles, calibration
│   ├── live-engine/          # Flux live, latence, suspension
│   └── messaging/            # Orchestration agents, alertes
├── packages/
│   ├── contracts/            # Schémas Pydantic partagés, types
│   └── provider-sdk/         # Interface générique des connecteurs
├── infra/
│   ├── docker/               # Dockerfiles, docker-compose.yml
│   ├── migrations/           # Alembic migrations (append-only)
│   └── observability/        # Prometheus, Grafana, OpenTelemetry
├── schemas/                  # JSON Schema canoniques
└── tests/                    # Pyramide de tests (voir docs/20)
```

## Nomenclature officielle

| Composant | Nom |
|---|---|
| Application | `URIM` |
| Cerveau analytique | `Kairos` |
| Dashboard | `URIM Dashboard` |
| Centre de mise | `Bet Center` |
| Moteur prudent | `Kairos Stake Guard` |
| Moteur d'apprentissage | `Post-Match Learning Engine` |
| Marché principal | `HALF_GOAL_DOMINANCE` |

## Contrats inter-modules

### Connector → Canonical Data Layer
- Entrée : payload brut fournisseur (JSON)
- Sortie : `ProviderObservation` avec `provider`, `provider_event_id`, `observed_at`, `available_at`, `fetched_at`, `source_version`, `quality_flags`, `raw_hash`
- Garantie : `raw_hash` reproductible, payload archivé avant normalisation

### Canonical Data Layer → Feature Store
- Entrée : observations canoniques horodatées
- Sortie : feature vectors `AS OF snapshot_time`
- Garantie : `available_at <= snapshot_time` pour chaque observation

### Feature Store → Kairos
- Entrée : `feature_snapshot_id` + `prediction_time`
- Sortie : distributions probabilistes + `confidence_score`
- Garantie : aucune feature avec `available_at > prediction_time`

### Kairos → Kairos Stake Guard
- Entrée : probabilités normalisées, `confidence_score`, `calibration_bucket`
- Sortie : `decision` (ADVICE/WATCH/NO_BET/INSUFFICIENT_DATA/SUSPENDED) + `stake_interval_cdf`
- Garantie : Stake Guard peut bloquer, Kairos ne contourne jamais

### Kairos Stake Guard → Prediction Ledger
- Entrée : décision finale + reason codes
- Sortie : `PredictionEnvelope` avec `immutable_hash`
- Garantie : append-only, jamais d'écrasement

### API → Frontend
- Le frontend ne détient aucun secret fournisseur
- Toutes les clés restent dans `services/ingestion` via secret manager
- L'API expose uniquement des données calculées, jamais des payloads bruts fournisseurs

## Variables d'environnement par couche

### services/ingestion
```
PROVIDER_X_API_KEY=<depuis secret manager — jamais en clair>
RAW_PAYLOAD_STORAGE_BUCKET=<bucket object storage>
DB_URL=postgresql+asyncpg://user:pass@host/urim
REDIS_URL=redis://localhost:6379/0
TEMPORAL_GUARD_STRICT=true
```

### services/prediction
```
DB_URL=postgresql+asyncpg://user:pass@host/urim
REDIS_URL=redis://localhost:6379/0
ALLOW_PRODUCTION_MOCKS=false
ALLOW_TEST_FIXTURES=false
MODEL_ARTIFACT_PATH=/artifacts/models
```

### apps/api
```
DB_URL=postgresql+asyncpg://user:pass@host/urim
JWT_SECRET=<depuis secret manager>
ALLOWED_ORIGINS=https://urim.example.com
LOG_LEVEL=INFO
REDACT_LOGS=true
```

### apps/web
```
NEXT_PUBLIC_API_URL=https://api.urim.example.com
# Aucune clé fournisseur ici — interdit par architecture
```

## Principes non négociables

1. Les modèles ne lisent jamais directement un payload JSON fournisseur.
2. Distinguer `event_time`, `observed_at`, `available_at`, `fetched_at`, `prediction_time`.
3. Conserver le payload brut (`raw_hash`) avant toute normalisation.
4. Une correction crée une nouvelle version, jamais un écrasement.
5. Dégrader gracieusement plutôt que fabriquer des données (`missing` ≠ `0`).
6. Toute décision est reproductible depuis `prediction_id`.
7. `Kairos Stake Guard` a l'autorité absolue — `Kairos` ne le contourne jamais.
8. `ALLOW_PRODUCTION_MOCKS=false` et `ALLOW_TEST_FIXTURES=false` en production.

## Invariants de sécurité

- Aucune clé API dans le frontend, les logs ou Git.
- Toutes les clés via secret manager (jamais dans `.env` commité).
- API : AuthN JWT, RBAC par rôle, rate limiting, audit logs.
- Logs redactés : pas de payloads bruts, pas de clés, pas de PII.
- CORS strict : uniquement les origines autorisées.
- CSP sur le frontend.

## Références

- `docs/05_PROVIDER_CONNECTOR_CONTRACT.md` — contrat SDK connecteur
- `docs/06_DATA_PROVENANCE.md` — provenance par champ
- `docs/07_TEMPORAL_INTEGRITY.md` — garde-fous temporels
- `docs/13_NO_BET_AND_RISK_ENGINE.md` — NO_BET Engine
- `docs/17_SECURITY.md` — politique de sécurité
- `docs/20_TESTING_STRATEGY.md` — pyramide de tests
- `docs/21_API_AND_DATABASE_SPEC.md` — API + schéma DB
- `docs/45_DEV_SETUP.md` — mise en place locale
