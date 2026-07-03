# Phase 21 API-Football Local-Only HTTP Smoke Harness

## Summary
Phase 21 adds a local-only smoke harness that can connect the Phase 19 manual smoke runner to an explicitly
injected request callable. It is terminal/dev-only, disabled by default, and never imported by FastAPI.

## Scope
- Add a local script harness with a public-safe result shape.
- Reuse the Phase 18 smoke client and Phase 19 manual runner gates.
- Keep provider activation blocked until the Phase 15 final gate is approved in a future phase.
- Add no public endpoint, DB ingestion, prediction creation, bookmaker integration, betting or frontend change.

## Safety Rules
- No concrete HTTP client is added in this phase.
- No real API-Football URL, credential, secret name/value or provider payload is committed.
- Unit tests use only a fake injected callable and must not open sockets.
- Output contains only status, execution flag, provider, mode, disabled write/prediction/betting flags and an optional payload hash.

## Validation
- From `apps/api`: `pip install -e ".[dev]"`, `ruff check .`, `pytest`.
- From the repository root: `git diff --check`.
- Run `alembic check` only when a dedicated disposable local DB is configured.

## Risks Covered
E005, E036, E065, E074 and E083 remain controlled by local-only gating, redaction and disabled betting/prediction paths.
