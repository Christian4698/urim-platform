# Phase 10 URIM Provider Onboarding Gate

## Objective
Create a Provider Onboarding Gate that blocks real provider activation until technical, security, operational, licensing, reconciliation, and data quality prerequisites are independently satisfied. Phase 10 remains gate-only: no API-Football connector, no internet/provider calls, no real API key, no bookmaker, no real betting, no ML, no real prediction, no production seed, no auth/RBAC build-out, no database ingestion, no migration/model change, and no production sports result.

## Files To Modify Or Create
- `docs/exec-plans/active/010-phase-10-provider-onboarding-gate.md`
- `.env.example`
- `apps/api/app/core/constants.py`
- `apps/api/app/core/security.py`
- `apps/api/app/main.py`
- `apps/api/app/api/v1/routes/fixtures.py`
- `apps/api/app/api/v1/routes/post_match.py`
- `apps/api/app/api/v1/routes/predictions.py`
- `apps/api/app/api/v1/routes/providers.py`
- `apps/api/app/modules/providers/__init__.py`
- `apps/api/app/modules/providers/onboarding_gate.py`
- `apps/api/app/modules/providers/sandbox.py`
- `apps/api/app/schemas/providers.py`
- `apps/api/tests/helpers/payload_helpers.py`
- `apps/api/tests/test_api_foundation.py`
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_provider_contracts.py`
- `apps/api/tests/test_provider_onboarding_gate.py`
- `apps/api/tests/test_provider_sandbox.py`
- `apps/api/tests/test_security_hardening.py`
- `apps/api/README.md`
- `apps/api/pyproject.toml`
- `docs/21_API_AND_DATABASE_SPEC.md`
- `docs/29_PROVIDER_READINESS_CONTRACTS.md`
- `docs/30_PROVIDER_ONBOARDING_GATE.md`
- `docs/index.md`

## Out Of Scope
- No real provider adapter, outbound HTTP, scraping, API-Football connector, API key value, bookmaker, real betting, ML, prediction creation, Post-Match Learning activation, official result verification, production seed, real sports fixture/result import, DB ingestion, SQLAlchemy model change, Alembic migration, full auth/RBAC, session, cookie, CORS expansion, scheduler, queue, retry execution, or circuit breaker execution.

## Phase 10 Work
- Update runtime metadata to `phase-10-provider-onboarding-gate`.
- Add `ProviderActivationChecklist`, `ProviderSecretReadiness`, and `ProviderOnboardingGate` contracts.
- Add helper logic that always refuses activation in Phase 10 with status `blocked_until_real_provider_audit`, `can_activate=false`, and explicit blocking reasons.
- Enrich `GET /api/v1/providers/readiness` with the gate while keeping all provider capabilities disabled and all POST routes unavailable.
- Document future provider secret environment variable names with empty values only in `.env.example`; public API responses expose only secret categories/counts, not env var names or values.
- Clarify `PROVIDER_QA_REQUIREMENTS` as payload/contract validation requirements and `PROVIDER_ONBOARDING_REQUIREMENTS` as business/ops/security prerequisites before real activation.
- Extract duplicated `_walk_values` and `_walk_keys` test helpers into `apps/api/tests/helpers/payload_helpers.py`.

## Expected Tests
- Gate refuses activation even with a constructed checklist.
- Incomplete checklist blocks activation and returns explicit reasons.
- Readiness endpoint exposes gate status, providers disabled, disabled capabilities, no network, no credentials, and no public secret env names.
- Future env var names exist only as empty `.env.example` placeholders.
- Provider test helpers are shared; existing golden payload and sandbox tests remain intact.
- Security tests confirm public responses are secret-free and dangerous POST endpoints return `405`.
- Existing Phase 2 temporal, append-only, and database tests remain intact; `alembic check` reports no new migration operations.

## Risks E001-E084
- E001-E005: provider completeness, provenance, multi-source readiness, and temporal availability remain gated.
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
Status: implemented and validated locally.

Phase 9 audit notes corrected:
- Duplicated `_walk_values` and `_walk_keys` helpers were extracted to `apps/api/tests/helpers/payload_helpers.py`.
- `PROVIDER_QA_REQUIREMENTS` and `PROVIDER_ONBOARDING_REQUIREMENTS` now have explicit descriptions separating payload/contract QA from business/operations/security onboarding.

Provider Onboarding Gate added:
- Runtime metadata now reports `phase-10-provider-onboarding-gate`.
- `ProviderActivationChecklist`, `ProviderSecretReadiness`, and `ProviderOnboardingGate` contracts were added.
- `refuse_provider_activation` always returns `can_activate=false`, `providers_enabled=false`, and status `blocked_until_real_provider_audit`.
- `GET /api/v1/providers/readiness` and `/api/v1/providers/sandbox/status` expose the blocked gate without provider activation.
- Future provider secret env names are documented only as empty `.env.example` placeholders; public API responses expose only non-sensitive categories/counts.

Documentation updated:
- `docs/21_API_AND_DATABASE_SPEC.md`
- `docs/29_PROVIDER_READINESS_CONTRACTS.md`
- `docs/30_PROVIDER_ONBOARDING_GATE.md`
- `docs/index.md`

Validation results:
- `pip install -e ".[dev]"`: passed.
- `ruff check .`: passed.
- `pytest`: passed with 97 passed, 2 skipped, 1 known Starlette/TestClient warning.
- `git diff --check`: passed with a line-ending warning for `.env.example` only.
- `docker compose -f infra/docker/docker-compose.yml up -d`: passed.
- `alembic upgrade head`: passed using existing migrations only.
- `alembic check`: passed; no new upgrade operations detected.
- `docker compose -f infra/docker/docker-compose.yml stop`: passed; volumes preserved.

Guardrail result:
- No Alembic migration or SQLAlchemy model changes.
- No provider HTTP client usage in application code.
- No API-Football connector, bookmaker, real betting, ML, real prediction, production seed, DB ingestion, or production sports result added.
- No real API key or non-empty provider secret placeholder added.
- Bet Center remains virtual/internal.
- Phase 2 temporal, append-only, immutable prediction, and anti-look-ahead protections remain intact.

Remaining risks:
- Phase 10 still blocks real provider activation; a future real provider phase must satisfy the gate with audited evidence.
- Complete auth/RBAC remains out of scope.
- Starlette/TestClient emits a dependency warning from the installed stack.
