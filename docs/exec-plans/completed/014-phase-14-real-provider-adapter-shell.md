# Phase 14 URIM Real Provider Adapter Shell

## Objective
Prepare a controlled real-provider adapter shell for a future API-Football integration while keeping every real-provider path blocked. Phase 14 is shell-only: no real API-Football connector, no internet/provider call, no active HTTP client, no real API key, no provider URL, no bookmaker, no real betting, no ML, no prediction creation, no production seed, no auth/RBAC build-out, no DB ingestion, no migration/model change, and no production sports result.

## Files To Modify Or Create
- `docs/exec-plans/active/014-phase-14-real-provider-adapter-shell.md`
- `apps/api/app/core/constants.py`
- `apps/api/app/core/security.py`
- `apps/api/app/main.py`
- `apps/api/app/modules/providers/real_provider_shell.py`
- `apps/api/app/modules/providers/sandbox.py`
- `apps/api/app/schemas/providers.py`
- `apps/api/tests/test_api_foundation.py`
- `apps/api/tests/test_health.py`
- `apps/api/tests/test_provider_contracts.py`
- `apps/api/tests/test_provider_sandbox.py`
- `apps/api/tests/test_provider_secret_safety.py`
- `apps/api/tests/test_provider_real_provider_shell.py`
- `apps/api/tests/test_security_hardening.py`
- `apps/api/README.md`
- `apps/api/pyproject.toml`
- `docs/index.md`
- `docs/21_API_AND_DATABASE_SPEC.md`
- `docs/32_PROVIDER_PREFLIGHT_SAFETY_REVIEW.md`
- `docs/33_REAL_PROVIDER_ADAPTER_SHELL.md`

## Out Of Scope
- No outbound HTTP, scraping, real API-Football connector, provider base URL, provider endpoint path, real API key, provider credential value, bookmaker, real betting, ML, prediction creation, official result verification, production seed, real sports fixture/result import, DB ingestion, SQLAlchemy model change, Alembic migration, full auth/RBAC, session, cookie, CORS expansion, scheduler, queue, retry execution, or circuit breaker execution.

## Phase 14 Work
- Update runtime metadata to `phase-14-real-provider-adapter-shell`.
- Lock `ProviderPreflightSafetyReview.status` and `decision` with `Literal` values.
- Add a `RealProviderAdapterShell` that structurally satisfies the provider protocol while every data-producing method is blocked.
- Add `ProviderNetworkDisabledError` and an egress guard helper that always blocks provider network attempts.
- Add a public-safe `real_provider_shell_status` to provider readiness with only disabled booleans and the label `api_football_future_provider_shell`.
- Update provider docs to explain that Phase 14 does not connect API-Football and contains no real provider URL, key, credential, HTTP client, or request path.

## Expected Tests
- Preflight review rejects non-approved status changes and `decision="approved"`.
- Real provider shell satisfies `SportsDataProviderProtocol`, stays disabled, exposes no URL/secret, and raises `ProviderNetworkDisabledError` for fetch/normalize/mapping methods.
- Egress guard blocks without touching socket or network APIs.
- Readiness includes `real_provider_shell_status`, remains secret-free, all providers disabled, and dangerous POST routes remain `405`.
- Phase 2 database tests remain intact and no migration/model change is introduced.

## Risks E001-E084
- E001-E005: provider completeness, provenance, multi-source readiness, and temporal availability remain blocked until approved.
- E026: no advice or prediction creation is introduced.
- E049: pre-match/live separation remains intact; live stays disabled.
- E065-E074: provider fallback, timestamp discipline, immutability readiness, versioning, missing-data clarity, mapping, latency/rate-limit readiness, and API key protection.
- E079: no retroactive result mutation path added.
- E083: no real betting or loss-recovery behavior introduced.
- E084: shell limits and remaining provider blockers are explicit.

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

## Implementation Results
- Runtime metadata updated to `phase-14-real-provider-adapter-shell`.
- `ProviderPreflightSafetyReview.status` and `ProviderPreflightSafetyReview.decision` are now locked with `Literal` values.
- `RealProviderAdapterShell` added as a protocol-compatible blocked shell with `ProviderNetworkDisabledError`.
- Provider readiness now exposes `real_provider_shell_status` with the label `api_football_future_provider_shell` and only disabled booleans.
- Phase 14 docs added in `docs/33_REAL_PROVIDER_ADAPTER_SHELL.md` and referenced from `docs/index.md`.
- No migration, SQLAlchemy model, DB ingestion, provider connector, API-Football URL, HTTP client, real secret, bookmaker, ML, prediction creation, production seed, or production sports result was added.

## Validation Results
- `pip install -e ".[dev]"`: passed.
- `ruff check .`: passed.
- `pytest`: passed, 126 passed, 2 skipped, 1 existing Starlette/TestClient deprecation warning.
- `git diff --check`: passed.
- First `alembic check` attempt without local Postgres did not return; the stuck process was stopped.
- `docker compose -f infra/docker/docker-compose.yml up -d`: started local Postgres/Redis.
- `alembic upgrade head`: passed using existing migrations only.
- `alembic check`: passed with `No new upgrade operations detected.`
- `docker compose -f infra/docker/docker-compose.yml stop`: stopped local services without `-v`.

## Guardrail Scan Results
- No provider HTTP/socket usage found in `apps/api/app`.
- No real provider URL, API-Football host, API-Sports/RapidAPI token, or non-empty provider secret placeholder found.
- No enabled bookmaker, real betting, ML, prediction creation, or production seed flag found.
- No Alembic, model, or DB layer diff found.
