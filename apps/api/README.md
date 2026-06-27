# URIM API

FastAPI backend for the URIM Kairos engine.

This package currently covers Phase 4 API/security hardening work:

- SQLAlchemy metadata for the PostgreSQL foundation schema.
- Alembic migrations for local and future controlled environments.
- Versioned FastAPI routes under `/api/v1`.
- API-first security headers, including a restrictive Content-Security-Policy.
- Thread-safe SQLAlchemy engine/session-factory reuse keyed by `DATABASE_URL`.
- Safety overrides that keep live prediction, production mocks, provider connectors, API-Football, bookmakers, prediction creation, and real betting disabled.

It does not connect API-Football, train ML models, execute bets, create real predictions, create production sports results, or seed production data. The Bet Center remains virtual/internal only.

The Phase 4 CSP is intentionally strict for an API surface:
`default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`.
It may restrict interactive documentation rendering; an auth/docs portal is out of scope for Phase 4.

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
