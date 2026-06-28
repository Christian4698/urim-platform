# Phase 5 URIM API Runtime Cleanup

## Objective
Clean up Phase 4 runtime/API details before any business logic, provider integration, auth/RBAC, ML, real prediction, real betting, production seed, or schema migration work.

## Files To Modify Or Create
- `docs/exec-plans/active/005-phase-5-api-runtime-cleanup.md`
- `apps/api/app/core/constants.py`
- `apps/api/app/core/security.py`
- `apps/api/app/db/session.py`
- `apps/api/app/main.py`
- `apps/api/app/schemas/common.py`
- `apps/api/app/schemas/system.py`
- `apps/api/app/api/v1/routes/*.py`
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_api_foundation.py`
- `apps/api/tests/test_db_session.py`
- `apps/api/tests/test_security_hardening.py`
- `apps/api/README.md`
- `apps/api/pyproject.toml`
- `docs/17_SECURITY.md`
- `docs/21_API_AND_DATABASE_SPEC.md`

## Out Of Scope
- No API-Football connector or provider integration.
- No bookmaker integration.
- No real stake, wager, payout, bankroll automation, or payment flow.
- No ML model, calibration engine, real prediction creation, or post-match learning engine.
- No production seed data, fake production sports result, or production mock.
- No full auth/RBAC, sessions, cookies, CORS expansion, docs portal, or deployment process change.
- No new migration and no edits to existing migrations unless validation proves it is unavoidable.

## Runtime Cleanup
- Update API metadata to `phase-5-api-runtime-cleanup`.
- Replace phase-tied response statuses with stable values: `read_only_skeleton`, `virtual_internal`, `disabled`, and `not_required`.
- Keep CSP strict and API-first; document that Swagger/ReDoc may not render interactively under this CSP.
- Keep `/version`, `/readiness`, and `/api/v1/system/capabilities` coherent: providers, API-Football, bookmakers, ML, live, real betting, prediction creation, production mocks, and production seeds remain disabled.
- Keep the SQLAlchemy engine/session-factory singleton keyed by `settings.database_url`, guarded by `RLock`, and reset/dispose safe.
- Replace the audited `sessionmaker(bind=...)` pattern with SQLAlchemy 2.0-style construction that avoids the `bind=` keyword.

## Expected Tests
- Health, version, readiness, capabilities, and skeleton tests expect Phase 5 metadata and stable statuses.
- DB session tests cover same-URL reuse, URL-change recreation, reset, missing `DATABASE_URL`, concurrent `get_engine()`, and no SQLAlchemy warnings during session operations.
- Security tests cover headers, CSP, no secrets in public responses, dangerous POST routes returning 405, and dangerous settings remaining disabled when monkeypatched.
- Phase 2 append-only and temporal integrity tests remain intact.
- Phase 3 skeleton endpoints remain GET-only, read-only, empty, and non-mutating.

## Risks E001-E084
Phase 5 mainly controls or avoids regressions for:
- E001-E005: no provider data is ingested or fabricated; temporal protections remain untouched.
- E026: no forced betting advice or prediction creation is introduced.
- E049: pre-match/live remain separated; live stays disabled.
- E066-E074: runtime/session/security cleanup, API key protection, versioning clarity, and missing-data discipline.
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

Docker/PostgreSQL may be started only if needed for `alembic check`. Do not delete Docker volumes with `-v`.
