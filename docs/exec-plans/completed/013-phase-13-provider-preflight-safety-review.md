# Phase 13 URIM Provider Preflight Safety Review

## Objective
Run the final provider preflight safety review before any future controlled real-provider preparation. Phase 13 remains review-only and blocked by default: no API-Football connector, no internet/provider call, no real API key, no bookmaker, no real betting, no ML, no prediction creation, no production seed, no auth/RBAC build-out, no DB ingestion, no migration/model change, and no production sports result.

## Files To Modify Or Create
- `docs/exec-plans/active/013-phase-13-provider-preflight-safety-review.md`
- `apps/api/app/core/constants.py`
- `apps/api/app/core/security.py`
- `apps/api/app/main.py`
- `apps/api/app/modules/providers/secret_safety.py`
- `apps/api/app/modules/providers/sandbox.py`
- `apps/api/app/schemas/providers.py`
- `apps/api/tests/test_api_foundation.py`
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_provider_contracts.py`
- `apps/api/tests/test_provider_onboarding_gate.py`
- `apps/api/tests/test_provider_sandbox.py`
- `apps/api/tests/test_provider_secret_safety.py`
- `apps/api/tests/test_security_hardening.py`
- `apps/api/README.md`
- `apps/api/pyproject.toml`
- `docs/index.md`
- `docs/21_API_AND_DATABASE_SPEC.md`
- `docs/30_PROVIDER_ONBOARDING_GATE.md`
- `docs/31_PROVIDER_SECRET_SAFETY.md`
- `docs/32_PROVIDER_PREFLIGHT_SAFETY_REVIEW.md`

## Out Of Scope
- No provider adapter activation, outbound HTTP, scraping, API-Football connector, real API key, provider credential value, bookmaker, real betting, ML, prediction creation, official result verification, production seed, real sports fixture/result import, DB ingestion, SQLAlchemy model change, Alembic migration, full auth/RBAC, session, cookie, CORS expansion, scheduler, queue, retry execution, or circuit breaker execution.

## Phase 13 Work
- Update runtime metadata to `phase-13-provider-preflight-safety-review`.
- Fix Claude Phase 12 audit notes: PEP 8 spacing in provider onboarding tests, named expected provider secret count, and clear documentation of intentionally ignored local secret presence.
- Add a safe preflight review contract that returns `blocked_until_real_provider_preflight_approved` and `real_provider_preparation_ready=false`.
- Expose the preflight review in provider readiness and sandbox status responses without adding any mutating endpoint.
- Keep public responses secret-safe and keep all provider capabilities disabled.
- Update provider docs to explain that future real-provider preparation remains blocked until a later explicit audit approval.

## Expected Tests
- Preflight review is blocked by default and exposes explicit future checklist and blocking reasons.
- Readiness and sandbox responses include Phase 13 metadata, security headers, preflight review, no secret names/values, providers disabled, no network calls, no DB ingestion, and no prediction creation.
- Phase 12 audit fixes are covered: PEP 8 spacing, non-ambiguous expected secret count, and documented ignored local-secret presence.
- Dangerous POST routes remain `405`, and Phase 2 database tests remain intact.

## Risks E001-E084
- E001-E005: provider completeness, provenance, multi-source readiness, and temporal availability remain blocked until approved.
- E026: no advice or prediction creation is introduced.
- E049: pre-match/live separation remains intact; live stays disabled.
- E065-E074: provider fallback, timestamp discipline, immutability readiness, versioning, missing-data clarity, mapping, latency/rate-limit readiness, and API key protection.
- E079: no retroactive result mutation path added.
- E083: no real betting or loss-recovery behavior introduced.
- E084: provider preparation limits and remaining blockers are explicit.

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
- Runtime metadata now reports `phase-13-provider-preflight-safety-review`.
- Fixed Claude Phase 12 audit notes: PEP 8 spacing before the first onboarding gate test, named expected provider secret count, and documented the intentionally ignored local-secret presence inspection.
- Added `ProviderPreflightSafetyReview` with `status=blocked_until_real_provider_preflight_approved` and `real_provider_preparation_ready=false`.
- Exposed `preflight_review` in provider readiness and sandbox status responses.
- Added explicit preflight blocking reasons and future checklist for secret manager, egress controls, quota/rate limits, provider license, monitoring, reconciliation, and independent audit.
- Added `docs/32_PROVIDER_PREFLIGHT_SAFETY_REVIEW.md` and updated API, onboarding gate, secret safety, and docs index pages.
- No API-Football connector, provider network call, bookmaker, real betting path, ML, prediction creation, production seed, DB ingestion, model change, or migration change was added.

Validation results:
- `pip install -e ".[dev]"`: passed.
- `ruff check .`: passed.
- `pytest`: passed, `107 passed, 2 skipped, 1 warning`.
- `git diff --check`: passed.
- Docker Compose Postgres/Redis started for validation only, existing migrations were applied with `alembic upgrade head`, and `alembic check` passed with `No new upgrade operations detected.`
- Docker Compose services were stopped without `-v`.

Guardrail scan results:
- No app-code provider HTTP client usage found.
- No migration/model diff found.
- No non-empty future provider secret placeholder found in `.env.example`.
- Public provider readiness and sandbox responses include blocked preflight review and remain secret-safe.

Remaining risk:
- Phase 13 does not approve controlled real-provider preparation. Real provider work remains blocked until a future explicit audit phase validates secret manager, egress controls, quota/rate limits, license, monitoring, reconciliation, and independent audit evidence.
