# Phase 11 URIM Provider Onboarding Gate Hardening

## Objective
Harden the Phase 10 Provider Onboarding Gate before any future real provider integration. Phase 11 closes audit ambiguities while keeping provider activation structurally blocked: no API-Football connector, no internet/provider calls, no real API key, no bookmaker, no real betting, no ML, no real prediction, no production seed, no auth/RBAC build-out, no database ingestion, no migration/model change, and no production sports result.

## Files To Modify Or Create
- `docs/exec-plans/active/011-phase-11-provider-onboarding-gate-hardening.md`
- `.gitattributes`
- `.env.example`
- `apps/api/app/core/constants.py`
- `apps/api/app/core/security.py`
- `apps/api/app/main.py`
- `apps/api/app/api/v1/routes/fixtures.py`
- `apps/api/app/api/v1/routes/post_match.py`
- `apps/api/app/api/v1/routes/predictions.py`
- `apps/api/app/api/v1/routes/providers.py`
- `apps/api/app/modules/providers/__init__.py`
- `apps/api/app/modules/providers/contracts.py`
- `apps/api/app/modules/providers/onboarding_gate.py`
- `apps/api/app/modules/providers/sandbox.py`
- `apps/api/app/schemas/providers.py`
- `apps/api/tests/test_api_foundation.py`
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_provider_contracts.py`
- `apps/api/tests/test_provider_onboarding_gate.py`
- `apps/api/tests/test_provider_sandbox.py`
- `apps/api/tests/test_security_hardening.py`
- `apps/api/README.md`
- `apps/api/pyproject.toml`
- `docs/21_API_AND_DATABASE_SPEC.md`
- `docs/30_PROVIDER_ONBOARDING_GATE.md`

## Out Of Scope
- No provider adapter, outbound HTTP, scraping, API-Football connector, API key value, bookmaker, real betting, ML, prediction creation, Post-Match Learning activation, official result verification, production seed, real sports fixture/result import, DB ingestion, SQLAlchemy model change, Alembic migration, full auth/RBAC, session, cookie, CORS expansion, scheduler, queue, retry execution, or circuit breaker execution.

## Phase 11 Work
- Update runtime metadata to `phase-11-provider-onboarding-gate-hardening`.
- Add docstrings to `refuse_provider_activation` explaining structural blocking through Pydantic `Literal[False]` and the absence of conditional activation logic.
- Make `build_provider_onboarding_gate` and `refuse_provider_activation` reset any passed checklist or secret readiness objects to safe defaults, including objects bypassed with `model_construct`.
- Normalize `.env.example` to LF and add `.env.example text eol=lf` in `.gitattributes`.
- Update gate docs to explain Phase 11 closes activation ambiguity while preserving the Phase 10 block.

## Expected Tests
- `refuse_provider_activation.__doc__` documents structural blocking and no conditional activation.
- Injected `ProviderSecretReadiness.model_construct(configured=True, secret_values_present=True, public_env_var_names_exposed=True)` is reset to false defaults.
- Injected `ProviderActivationChecklist.model_construct(...True...)` is reset to false defaults.
- `.env.example` has LF line endings and provider secret placeholders remain empty.
- Public readiness and sandbox responses expose no future secret env names or values.
- Providers remain disabled, dangerous POST routes return `405`, no socket call occurs, and Phase 2 database tests remain intact.

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
Status: implemented, with one environment-blocked validation.

Completed:
- Runtime metadata now reports `phase-11-provider-onboarding-gate-hardening`.
- `refuse_provider_activation()` documents that the gate is structurally blocked by Pydantic `Literal[False]` fields and has no conditional activation logic.
- `build_provider_onboarding_gate()` and `refuse_provider_activation()` reset caller-provided checklist and secret-readiness sub-objects to safe defaults, including objects created with `model_construct`.
- `.env.example` and `.gitattributes` are normalized to LF; `.env.example text eol=lf` and `.gitattributes text eol=lf` are declared.
- Public readiness and sandbox responses keep the blocked gate visible without exposing future provider env var names or secret values.
- No API-Football connector, provider HTTP client, bookmaker, real betting path, ML, prediction creation, production seed, DB ingestion, model change, or migration change was added.

Validation results:
- `pip install -e ".[dev]"`: passed.
- `ruff check .`: passed.
- `pytest`: passed, `99 passed, 2 skipped, 1 warning`.
- `git diff --check`: passed.
- `git ls-files --eol .env.example .gitattributes`: both files have `w/lf` and `attr/text eol=lf`.
- `alembic check`: environment-blocked. `localhost:5432` is not reachable, Docker Compose cannot start Postgres because the Docker Desktop Linux engine pipe is unavailable, and a short-timeout Alembic attempt ends with `psycopg.errors.ConnectionTimeout`.

Guardrail scan results:
- No app-code provider HTTP client usage found.
- No migration/model diff found.
- No non-empty future provider secret placeholder found in `.env.example`.
- Existing API-Football/bookmaker strings remain disabled/future-contract safeguards only.

Remaining risk:
- Alembic live check still needs to be rerun once local PostgreSQL or Docker Desktop is available. No Phase 11 code path required a migration change.
