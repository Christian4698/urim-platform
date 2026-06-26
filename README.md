# URIM — Kairos Sports Intelligence

URIM est l'application produit. Kairos est le moteur technique. Ce dépôt construit un système d'intelligence sportive probabiliste, traçable, sécurisé et explicable, sans jamais promettre un résultat garanti.

## Phase 1 — squelette applicatif

Cette phase crée uniquement la base monorepo :
- `apps/web` : dashboard Next.js + React + TypeScript.
- `apps/api` : API FastAPI limitée aux endpoints santé.
- `packages/contracts` : schémas JSON et types partagés.
- `packages/config` : configuration partagée URIM/Kairos.
- `packages/ui` : composants UI de base.
- `infra/docker` : Postgres et Redis locaux placeholder.

Aucune API sportive réelle, aucune base métier, aucun bookmaker, aucune mise réelle et aucun modèle prédictif réel ne sont connectés en Phase 1.

## Démarrage local

Prérequis recommandés : Node.js LTS, `pnpm`, Python 3.12+, `uv`, Docker Compose.

```bash
pnpm install
pnpm web:dev
```

```bash
cd apps/api
uv run uvicorn app.main:app --reload
```

```bash
docker compose -f infra/docker/docker-compose.yml up -d
```

## Vérifications utiles

```bash
pnpm contracts:validate
pnpm web:lint
pnpm web:build
pnpm api:test
```

Si l'environnement ne peut pas installer les dépendances, conserver les fichiers de configuration et exécuter ces commandes manuellement dès que `pnpm` et `uv` sont disponibles.

## Principe central

> Aucune donnée de production ne doit être inventée, extrapolée comme si elle était observée, ou remplacée silencieusement par un mock.

Les données simulées sont autorisées uniquement dans les tests, fixtures locales et environnements explicitement marqués `DEMO` ou `PLACEHOLDER`.
