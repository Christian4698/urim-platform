# Phase 6 URIM Provider Readiness Contracts

## Objective
Prepare provider contracts, data quality rules, and official integration interfaces for future phases without connecting API-Football or any real provider, making network calls, adding credentials, creating business logic, adding ML, creating real predictions, enabling real betting, seeding production data, or changing migrations.

## Files To Modify Or Create
- `docs/exec-plans/active/006-phase-6-provider-readiness-contracts.md`
- `apps/api/app/core/constants.py`
- `apps/api/app/main.py`
- `apps/api/app/api/v1/routes/providers.py`
- `apps/api/app/modules/providers/__init__.py`
- `apps/api/app/modules/providers/contracts.py`
- `apps/api/app/modules/providers/quality.py`
- `apps/api/app/schemas/providers.py`
- `apps/api/tests/test_api_foundation.py`
- `apps/api/tests/test_provider_contracts.py`
- `apps/api/tests/test_security_hardening.py`
- `apps/api/README.md`
- `apps/api/pyproject.toml`
- `docs/21_API_AND_DATABASE_SPEC.md`
- `docs/29_PROVIDER_READINESS_CONTRACTS.md`

## Out Of Scope
- No API-Football connector, provider adapter, outbound HTTP, scraping, or internet call.
- No API key, credential field, secret loading, or provider auth flow.
- No bookmaker integration.
- No real stake, wager, payout, bankroll automation, or payment flow.
- No ML, calibration engine, real prediction creation, or post-match learning engine.
- No production seed, fake production sports result, or production mock.
- No full auth/RBAC, sessions, cookies, CORS expansion, docs portal, or deployment change.
- No new migration and no edits to existing migrations unless validation proves it unavoidable.

## Provider Readiness Work
- Update API metadata to `phase-6-provider-readiness-contracts`.
- Add Pydantic readiness contracts for provider identity, capabilities, observations, raw payload references, canonical entity mappings, official result envelopes, data quality reports, and temporal availability metadata.
- Require provider provenance fields: `provider`, `provider_event_id`, `observed_at`, `available_at`, `fetched_at`, `source_version`, `raw_hash`, and `quality_flags`.
- Enforce `observed_at <= available_at <= fetched_at`.
- Add temporal helper preventing `available_at > prediction_time`.
- Keep all capability matrix entries disabled: fixtures, results, standings, lineups, events, odds, and injuries.
- Add protocol-only provider interfaces for future providers and official result verification; no concrete adapter.
- Add `GET /api/v1/providers/readiness` as read-only metadata with providers disabled, API-Football disconnected, no network calls enabled, no API keys configured/exposed, and Post-Match Learning restricted to verified `post_match_outcomes`.

## Expected Tests
- Contract tests validate successful complete-provenance model construction.
- Contract tests reject missing provenance and invalid temporal ordering.
- Temporal helper rejects future `available_at` relative to prediction time.
- Capability matrix remains present and fully disabled.
- Official result envelope exposes `post_match_outcomes_only` and rejects user-declared ticket fields as learning sources.
- Readiness endpoint returns 200, includes security headers/CSP, exposes no secrets, and reports no provider/network/API key enabled.
- `POST /api/v1/providers/readiness` returns 405.
- Network monkeypatch proves readiness endpoint performs no outbound socket access.
- Existing Phase 2 append-only and temporal integrity tests remain intact.
- `alembic check` detects no new migration operations.

## Risks E001-E084
Phase 6 mainly controls or avoids regressions for:
- E001-E005: provenance, completeness, multi-source readiness, and temporal availability rules.
- E026: no advice or prediction creation is introduced.
- E049: pre-match/live remain separated; live stays disabled.
- E066-E074: timestamp discipline, immutability readiness, versioning, missing-data clarity, entity mapping, latency readiness, and API key protection.
- E079: no retroactive result mutation path is added.
- E083: no real betting or loss-recovery behavior is introduced.
- E084: readiness limitations and disabled provider status are explicit.

## Validation Strategy
Run from `apps/api`:
- `pip install -e ".[dev]"`
- `ruff check .`
- `pytest`
- `DATABASE_URL=postgresql+psycopg://urim:urim_local_only@localhost:5432/urim_local alembic check`
- `git status --short --branch`

Docker/PostgreSQL may be started only if needed for `alembic check`. Do not delete Docker volumes with `-v`.

## Implementation Result
Status: implemented and validated locally.

Files completed:
- `apps/api/app/api/v1/routes/providers.py`
- `apps/api/app/modules/providers/__init__.py`
- `apps/api/app/modules/providers/contracts.py`
- `apps/api/app/modules/providers/quality.py`
- `apps/api/app/schemas/providers.py`
- `apps/api/tests/test_api_foundation.py`
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_provider_contracts.py`
- `apps/api/tests/test_security_hardening.py`
- `apps/api/README.md`
- `apps/api/pyproject.toml`
- `docs/21_API_AND_DATABASE_SPEC.md`
- `docs/29_PROVIDER_READINESS_CONTRACTS.md`

Provider readiness endpoint:
- `GET /api/v1/providers/readiness` returns contract-only metadata.
- `POST /api/v1/providers/readiness` remains unavailable and returns `405`.

Validated safeguards:
- Providers disabled.
- API-Football disconnected.
- No outbound provider network path in application code.
- No provider credentials exposed.
- Capability matrix fully disabled.
- Production mock fallback forbidden.
- Post-Match Learning restricted to future verified `post_match_outcomes`.
- User-declared ticket result/profit-loss fields are disallowed as learning sources.
- Bet Center remains virtual/internal.
- Existing Phase 2 migration and DB model files were not modified.

Validation results:
- `pip install -e ".[dev]"`: passed.
- `ruff check .`: passed.
- `pytest` without `DATABASE_URL`: 73 passed, 2 skipped, 1 warning.
- `docker compose -f infra/docker/docker-compose.yml up -d`: passed.
- `alembic upgrade head`: passed against local Postgres.
- `alembic check`: passed; no new upgrade operations detected.
- `pytest` with local `DATABASE_URL`: 75 passed, 1 warning.
- `docker compose -f infra/docker/docker-compose.yml stop`: passed; volumes preserved.

Remaining risks:
- Phase 6 is contract-only; real provider onboarding still needs license, quota, latency, payload, reconciliation and redaction validation in a later phase.
- No complete auth/RBAC is added in Phase 6.
- Starlette/TestClient emits a deprecation warning from the installed dependency stack.
