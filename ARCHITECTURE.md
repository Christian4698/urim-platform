# Architecture — Vue d’ensemble URIM

```text
Fournisseurs réels
  ├─ Matchs / classements / effectifs
  ├─ Événements et statistiques
  ├─ Compositions / blessures
  ├─ Cotes horodatées
  └─ Météo / contexte vérifié
          │
          ▼
Connector Gateway
  ├─ Auth serveur
  ├─ Rate limiting
  ├─ Retry + backoff
  ├─ Circuit breaker
  ├─ Raw payload archive
  └─ Provider health score
          │
          ▼
Canonical Data Layer
  ├─ Entity resolution
  ├─ Validation
  ├─ Reconciliation multi-source
  ├─ Provenance par champ
  └─ Temporal availability guard
          │
          ▼
PostgreSQL / Timescale + Object Storage + Redis
          │
          ├───────────────┐
          ▼               ▼
Feature Store        Live Event Stream
          │               │
          └──────┬────────┘
                 ▼
Kairos
  ├─ Pré-match
  ├─ Live
  ├─ Calibration
  ├─ Scenario simulation
  ├─ Kairos Stake Guard / NO_BET Engine
  └─ Explanation
                 │
                 ▼
Immutable Prediction Ledger
                 │
          ┌──────┴─────────┐
          ▼                ▼
API utilisateur      Messagerie des agents
          │                │
          ▼                ▼
URIM Dashboard / Bet Center     Audit / alertes / décisions
```

## Nomenclature officielle
- Application : `URIM`
- Cerveau analytique : `Kairos`
- Dashboard : `URIM Dashboard`
- Centre de mise : `Bet Center`
- Moteur prudent : `Kairos Stake Guard`

## Modules nommés
- `Half Goals Intelligence Engine`
- `Post-Match Learning Engine`
- `Corners Intelligence Engine`
- `Fouls & Cards Intelligence Engine`
- `NO_BET Engine`

## Découpage recommandé
- `apps/web` : interface Next.js.
- `apps/api` : FastAPI ou API backend équivalente.
- `services/ingestion` : connecteurs fournisseurs.
- `services/prediction` : modèles et calibration.
- `services/live-engine` : mise à jour temps réel.
- `services/messaging` : orchestration des agents et messages.
- `packages/contracts` : schémas partagés.
- `packages/provider-sdk` : interface des connecteurs.
- `infra` : Docker, migrations, observabilité et déploiement.

## Principes
1. Les modèles ne lisent jamais directement le JSON d’un fournisseur.
2. Distinguer `event_time`, `observed_at`, `available_at`, `fetched_at`.
3. Conserver le brut et la représentation canonique.
4. Une correction crée une nouvelle version, jamais un écrasement.
5. Dégrader les fonctionnalités au lieu de fabriquer des données.
6. Toute décision doit être reproductible.
