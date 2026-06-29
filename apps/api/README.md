# URIM API

FastAPI backend for the URIM Kairos engine.

This package currently covers Phase 7 provider QA contract hardening work:

- SQLAlchemy metadata for the PostgreSQL foundation schema.
- Alembic migrations for local and future controlled environments.
- Versioned FastAPI routes under `/api/v1`.
- API-first security headers, including a restrictive Content-Security-Policy.
- Thread-safe SQLAlchemy 2.0-style engine/session-factory reuse keyed by `DATABASE_URL`.
- Safety overrides that keep live prediction, production mocks, provider connectors, API-Football, bookmakers, prediction creation, and real betting disabled.
- Read-only provider readiness contracts under `/api/v1/providers/readiness`.
- Provider QA helpers for contract-only golden payload checks and payload redaction.

It does not connect API-Football, train ML models, execute bets, create real predictions, create production sports results, or seed production data. The Bet Center remains virtual/internal only.

The Phase 7 CSP remains intentionally strict for an API surface:
`default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`.
It may restrict Swagger UI or ReDoc interactive rendering; an auth/docs portal is out of scope for Phase 7.

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
