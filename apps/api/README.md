# URIM API

FastAPI backend for the URIM Kairos engine.

This package currently covers Phase 2 database foundation work only:

- SQLAlchemy metadata for the PostgreSQL foundation schema.
- Alembic migrations for local and future controlled environments.
- Safety defaults that keep live prediction, production mocks, provider connectors, bookmakers, and real betting disabled.

It does not connect API-Football, train ML models, execute bets, or seed production data.
