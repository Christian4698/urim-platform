# Phase 8 URIM Provider Sandbox Adapter

## Objective
Create a controlled internal sandbox provider adapter that simulates a future official provider without internet access, API-Football, API keys, real sports data, database ingestion, prediction creation, ML, bookmakers, real betting, production seeds, auth/RBAC, or migration changes.

## Files To Modify Or Create
- `docs/exec-plans/active/008-phase-8-provider-sandbox-adapter.md`
- `apps/api/app/core/constants.py`
- `apps/api/app/main.py`
- `apps/api/app/api/v1/routes/providers.py`
- `apps/api/app/modules/providers/contracts.py`
- `apps/api/app/modules/providers/sandbox.py`
- `apps/api/app/schemas/providers.py`
- `apps/api/tests/test_api_foundation.py`
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_provider_contracts.py`
- `apps/api/tests/test_provider_sandbox.py`
- `apps/api/tests/test_security_hardening.py`
- `apps/api/README.md`
- `apps/api/pyproject.toml`
- `docs/21_API_AND_DATABASE_SPEC.md`
- `docs/29_PROVIDER_READINESS_CONTRACTS.md`

## Out Of Scope
- No API-Football connector, real provider adapter, outbound HTTP, scraping, or internet call.
- No API key, credential field, secret loading, or provider auth flow.
- No bookmaker integration, real betting, stake, payout, bankroll automation, or payment flow.
- No ML, calibration engine, real prediction creation, or post-match learning engine.
- No production seed, real sports fixture/result import, or fake production sports result.
- No DB ingestion, full auth/RBAC, sessions, cookies, CORS expansion, docs portal, or deployment change.
- No migration edits and no SQLAlchemy model edits.

## Sandbox Work
- Update API phase metadata to `phase-8-provider-sandbox-adapter`.
- Make `SportsDataProviderProtocol` runtime-checkable for structural protocol tests.
- Add `SandboxProviderAdapter` that reads only in-memory `DEMO_NON_PROD` / `PLACEHOLDER` payloads.
- Convert sandbox payloads to `RawPayloadReference`, `ProviderObservation`, `TemporalAvailabilityMetadata`, `DataQualityReport`, and placeholder `OfficialResultEnvelope` structures.
- Generate stable SHA-256 `raw_hash` from canonical JSON payload content.
- Sanitize all public payload summaries with `sanitize_provider_payload`.
- Add `GET /api/v1/providers/sandbox/status` as read-only informational status.
- Keep `POST /api/v1/providers/sandbox/status` unavailable and returning `405`.

## Expected Tests
- Sandbox adapter satisfies `SportsDataProviderProtocol`.
- Identity and capability matrix remain disabled; network, credentials, production mock fallback, DB ingestion, and prediction creation remain disabled.
- Sandbox payloads are non-production only, contain no real team names, scores, winners, provider IDs, bookmaker fields, or credentials.
- Mapping creates complete provenance, timezone-aware timestamps, valid temporal ordering, stable raw hashes, and sanitized payload summaries.
- Endpoint returns security headers, no secrets, no network calls, and `POST` remains refused.
- Existing Phase 2 temporal, append-only, and database tests remain intact.
- `alembic check` detects no new migration operations.

## Risks E001-E084
- E001-E005: provenance completeness, missing handling, and temporal availability guardrails.
- E026: no advice or prediction creation introduced.
- E049: pre-match/live separation remains intact; live stays disabled.
- E065-E074: provider fallback, immutability readiness, versioning, missing-data clarity, mapping, latency readiness, and API key protection.
- E079: no retroactive result mutation path added.
- E083: no real betting or loss-recovery behavior introduced.
- E084: sandbox limitations are explicit.

## Validation Strategy
Run from `apps/api`:
- `pip install -e ".[dev]"`
- `ruff check .`
- `pytest`
- `git diff --check`
- `DATABASE_URL=postgresql+psycopg://urim:urim_local_only@localhost:5432/urim_local alembic check`

Docker/PostgreSQL may be started only if needed for `alembic check`; do not delete Docker volumes with `-v`.

## Implementation Result
Status: implemented and validated locally.

Sandbox adapter added:
- `SandboxProviderAdapter` implements the provider protocol structurally.
- Sandbox reads only in-memory `DEMO_NON_PROD` / `PLACEHOLDER` payloads.
- Identity, capabilities, network calls, credentials, DB ingestion, prediction creation, and production mock fallback remain disabled.
- Payload mapping creates `RawPayloadReference`, `ProviderObservation`, temporal metadata, quality reports, canonical mapping placeholders, and official-data placeholders without real sports results.
- Public sandbox summaries are sanitized before exposure.

Endpoint added:
- `GET /api/v1/providers/sandbox/status` returns read-only sandbox status.
- `POST /api/v1/providers/sandbox/status` remains unavailable and returns `405`.

Validation results:
- `pip install -e ".[dev]"`: passed.
- `ruff check .`: passed.
- `pytest` without `DATABASE_URL`: 89 passed, 2 skipped, 1 warning.
- `git diff --check`: passed.
- `docker compose -f infra/docker/docker-compose.yml up -d`: passed.
- `alembic upgrade head`: passed against local Postgres.
- `alembic check`: passed; no new upgrade operations detected.
- `pytest` with local `DATABASE_URL`: 91 passed, 1 warning.
- `docker compose -f infra/docker/docker-compose.yml stop`: passed; volumes preserved.

Guardrail result:
- No Alembic or SQLAlchemy DB model changes.
- No provider HTTP client usage in application code.
- No API-Football connector, bookmaker, real betting, ML, real prediction, or production seed added.
- No network call path added to the sandbox adapter.
- Bet Center remains virtual/internal.
- Phase 2 temporal and append-only protections remain intact.

Remaining risks:
- Sandbox is still non-production only; real provider onboarding still requires license, quota, latency, redaction, monitoring, reconciliation, and audit validation.
- No complete auth/RBAC is added in Phase 8.
- Starlette/TestClient emits a dependency warning from the installed stack.
