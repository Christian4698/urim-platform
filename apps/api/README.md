# URIM API

Backend FastAPI du Programme B1.

## Capacités actives

- sondes publiques `/health` et `/readiness`;
- PostgreSQL via SQLAlchemy 2 et Alembic;
- client API-Football backend-only avec timeout, retry borné, rate limiting,
  budget par run, quotas et validation de réponse;
- normalisation traçable des compétitions, saisons, équipes, matchs,
  classements, statistiques, événements, compositions et blessures;
- stockage append-only et idempotent;
- journal des synchronisations et erreurs neutralisées;
- routes read-only sous `/api/v1/sports`;
- commandes manuelles `urim-sports-sync`.

Le client est désactivé par défaut et sans clé. Les prédictions, probabilités,
bookmakers, live automatique, authentification et paris réels restent
désactivés.

## Installation et validation

```powershell
python -m pip install -e ".[dev]"
ruff check .
pytest
```

Avec une base PostgreSQL jetable :

```powershell
$env:DATABASE_URL="<URL PostgreSQL de test>"
alembic upgrade head
alembic current
alembic check

$env:B1_TEST_DATABASE_URL=$env:DATABASE_URL
pytest tests/test_program_b1_postgres_integration.py
```

La configuration complète, le schéma, les routes et le runbook Render sont dans
`docs/72_PROGRAM_B1_REAL_SPORTS_DATA.md`.
