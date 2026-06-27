# URIM API

FastAPI backend for the URIM Kairos engine.

This package currently covers Phase 3 API foundation work:

- SQLAlchemy metadata for the PostgreSQL foundation schema.
- Alembic migrations for local and future controlled environments.
- Versioned FastAPI routes under `/api/v1`.
- Safety defaults that keep live prediction, production mocks, provider connectors, bookmakers, prediction creation, and real betting disabled.

It does not connect API-Football, train ML models, execute bets, or seed production data.

## Validation

From `apps/api`:

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

With local PostgreSQL available:

```bash
$env:DATABASE_URL="postgresql+psycopg://urim:urim_local_only@localhost:5432/urim_local"
alembic check
```

Future Post-Match Learning may learn only from verified `post_match_outcomes`, never from `tickets.user_declared_result` or `tickets.user_declared_profit_loss`.
