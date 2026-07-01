# Phase 12 URIM Provider Env Secret Safety

## Objective
Prepare future provider environment-secret safety before any real API-Football or provider integration. Phase 12 remains secret-safety-only: no provider connector, no internet/provider call, no real API key, no bookmaker, no real betting, no ML, no prediction creation, no production seed, no auth/RBAC build-out, no DB ingestion, no migration/model change, and no production sports result.

## Files To Modify Or Create
- `docs/exec-plans/active/012-phase-12-provider-env-secret-safety.md`
- `.env.example`
- `.gitignore`
- `apps/api/app/core/constants.py`
- `apps/api/app/core/security.py`
- `apps/api/app/main.py`
- `apps/api/app/api/v1/routes/providers.py`
- `apps/api/app/modules/providers/secret_safety.py`
- `apps/api/app/modules/providers/__init__.py`
- `apps/api/app/modules/providers/contracts.py`
- `apps/api/app/modules/providers/sandbox.py`
- `apps/api/app/schemas/providers.py`
- `apps/api/tests/test_api_foundation.py`
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_provider_contracts.py`
- `apps/api/tests/test_provider_onboarding_gate.py`
- `apps/api/tests/test_provider_sandbox.py`
- `apps/api/tests/test_security_hardening.py`
- `apps/api/tests/test_provider_secret_safety.py`
- `apps/api/README.md`
- `apps/api/pyproject.toml`
- `docs/index.md`
- `docs/21_API_AND_DATABASE_SPEC.md`
- `docs/30_PROVIDER_ONBOARDING_GATE.md`
- `docs/31_PROVIDER_SECRET_SAFETY.md`

## Out Of Scope
- No API-Football connector, outbound HTTP, scraping, scheduler, queue, retry execution, circuit breaker execution, provider adapter activation, real API key, provider credential value, bookmaker, real betting, ML, prediction creation, official result verification, production seed, real sports fixture/result import, DB ingestion, SQLAlchemy model change, Alembic migration, full auth/RBAC, session, cookie, or CORS expansion.

## Phase 12 Work
- Update runtime metadata to `phase-12-provider-env-secret-safety`.
- Add an internal provider secret safety loader that can inspect local environment presence but returns only safe booleans, categories, counts, and storage requirements.
- Add a public-safe summary to readiness and sandbox responses while keeping the onboarding gate blocked.
- Keep future provider secret placeholders empty in `.env.example`; verify local env files stay ignored.
- Update provider docs to explain that future secrets must live only in secure environment/secret manager storage and never in Git, logs, frontend, or public API responses.

## Expected Tests
- `.env.example` provider placeholders are empty and LF-only.
- `.gitignore` protects `.env`, `.env.*`, and `.env.local`.
- The secret safety loader hides raw values and future env var names even when local values are monkeypatched.
- Public readiness and sandbox responses expose no future provider env var names or secret values.
- Provider activation remains blocked, providers disabled, dangerous POST routes return `405`, no socket call occurs, and Phase 2 database tests remain intact.

## Risks E001-E084
- E001-E005: provider readiness remains blocked until provenance and temporal contracts are safe.
- E026: no advice or prediction creation is introduced.
- E049: pre-match/live separation remains intact; live stays disabled.
- E065-E074: provider fallback, timestamp discipline, immutability readiness, versioning, missing-data clarity, mapping, latency/rate-limit readiness, and API key protection.
- E079: no retroactive result mutation path added.
- E083: no real betting or loss-recovery behavior introduced.
- E084: activation limits and provider readiness gaps are explicit.

## Validation Strategy
Run from `apps/api`:
- `pip install -e ".[dev]"`
- `ruff check .`
- `pytest`

Run from repository root:
- `git diff --check`

Run with local PostgreSQL:
- `DATABASE_URL=postgresql+psycopg://urim:urim_local_only@localhost:5432/urim_local alembic check`

Docker/PostgreSQL may be started only if needed for `alembic check`; apply existing migrations only and do not delete Docker volumes with `-v`.

## Implementation Result
Status: implemented and validated.

Completed:
- Created branch `phase-12/provider-env-secret-safety` from clean `main`.
- Runtime metadata now reports `phase-12-provider-env-secret-safety`.
- Added an internal provider secret safety module that knows future provider env names but returns only public-safe summaries and never raw values.
- Added `secret_safety` summaries to provider readiness and sandbox status responses.
- Kept provider onboarding blocked: `blocked_until_real_provider_audit`, `can_activate=false`, `providers_enabled=false`, `network_calls_enabled=false`, `db_ingestion_enabled=false`.
- Kept future provider secret placeholders empty in `.env.example`; `.gitignore` already protects `.env`, `.env.*`, and `.env.local` via `.env.*`.
- Added `docs/31_PROVIDER_SECRET_SAFETY.md` and updated API/onboarding docs.
- No API-Football connector, provider network call, bookmaker, real betting path, ML, prediction creation, production seed, DB ingestion, model change, or migration change was added.

Validation results:
- `pip install -e ".[dev]"`: passed.
- `ruff check .`: passed.
- `pytest`: passed, `105 passed, 2 skipped, 1 warning`.
- `git diff --check`: passed.
- Docker Compose Postgres/Redis started for validation only, existing migrations were applied with `alembic upgrade head`, and `alembic check` passed with `No new upgrade operations detected.`
- Docker Compose services were stopped without `-v`.

Guardrail scan results:
- No app-code provider HTTP client usage found.
- No migration/model diff found.
- No non-empty future provider secret placeholder found in `.env.example`.
- Public provider readiness and sandbox responses were tested against future provider env names and local fake secret values.

Remaining risk:
- Phase 12 still does not validate a real provider secret manager, rotation process, license, quota, or provider egress controls. Those remain future provider-audit work before any real activation.
