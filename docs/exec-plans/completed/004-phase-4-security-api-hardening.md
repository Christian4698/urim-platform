# Phase 4 URIM Security/API Hardening

## Objective
Harden the existing Phase 3 FastAPI foundation for API/security safety without adding business logic, auth/RBAC build-out, provider connectors, bookmakers, ML, real betting, real predictions, production seeds, production sports results, or schema migrations.

## Files To Modify Or Create
- `docs/exec-plans/active/004-phase-4-security-api-hardening.md`
- `apps/api/app/core/security.py`
- `apps/api/app/core/constants.py`
- `apps/api/app/db/session.py`
- `apps/api/app/main.py`
- `apps/api/app/api/v1/routes/*.py`
- `apps/api/app/schemas/system.py`
- `apps/api/pyproject.toml`
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_api_foundation.py`
- `apps/api/tests/test_db_session.py`
- `apps/api/tests/test_security_hardening.py`
- `apps/api/README.md`
- `docs/17_SECURITY.md`
- `docs/21_API_AND_DATABASE_SPEC.md`

## Out Of Scope
- No Phase 5 or Phase 6 work.
- No API-Football connector or outbound provider integration.
- No bookmaker integration.
- No real stake, wager execution, payout, bankroll, or payment flow.
- No ML model, real prediction creation, calibration engine, or post-match learning engine.
- No production seed data, production mock sports results, or fake real-world sports data.
- No full auth/RBAC, sessions, cookies, CORS expansion, docs portal, or deployment process change.
- No new migration and no edits to existing migrations unless validation proves it is unavoidable.

## Phase 4 Changes
- M1: Add an API-first Content-Security-Policy to security headers while preserving existing security headers.
- M2: Protect the SQLAlchemy singleton engine/session-factory lifecycle with a module-level lock.
- M3: Replace mutable `SessionLocal.configure(bind=...)` and `db.bind` patterns with URL-keyed engine and session factory singletons.
- M4: Keep `/version` and capabilities safety flags as explicit Phase 4 overrides: live and real betting remain disabled even if settings are monkeypatched true.

## Expected Tests
- Security headers, including CSP, are present on public GET endpoints.
- Public response bodies do not expose `DATABASE_URL`, the local password, API keys, secrets, provider credentials, or password fields.
- Dangerous POST routes for fixtures, predictions, tickets, providers, post-match outcomes, and capabilities return 405.
- Capabilities and `/version` still report providers, API-Football, bookmakers, ML, live, real betting, prediction creation, production mocks, and production seeds disabled.
- Bet Center remains virtual/internal only.
- SQLAlchemy engine and session factory are reused for the same URL, recreated safely for URL changes, reset safely, and created once under concurrent access.
- Missing `DATABASE_URL` raises only when a real engine/session is requested.
- Phase 2 append-only and temporal integrity tests remain intact.
- Phase 3 skeleton collection tests remain read-only and empty.

## Risks E001-E084
Phase 4 mainly controls or avoids regressions for:
- E001-E005: no provider data is ingested or fabricated; temporal protections remain untouched.
- E026: no forced betting advice or prediction creation is introduced.
- E049: pre-match/live remain separated; live stays disabled.
- E066-E074: API/session/security hardening, UTC/immutability/versioning safety, missing-data discipline, provider/API key protection.
- E079: no retroactive result or prediction mutation path is added.
- E083: no loss-recovery or real betting behavior is introduced.
- E084: disabled/internal status and security limits remain explicit.

## Validation Strategy
Run from `apps/api`:
- `pip install -e ".[dev]"`
- `ruff check .`
- `pytest`
- `DATABASE_URL=postgresql+psycopg://urim:urim_local_only@localhost:5432/urim_local alembic check`
- `git status --short --branch`

Docker/PostgreSQL may be started only if needed for `alembic check`. The expected path is metadata-only hardening with no migration changes.
