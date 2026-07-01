# Phase 15 URIM Provider Activation Readiness Final Gate

## Objective
Add a final provider activation readiness gate before any future real provider integration. Phase 15 remains
read-only and blocked: no API-Football connector, no provider network call, no HTTP client, no provider URL,
no real API key, no DB ingestion, no Alembic/model change, no bookmaker, no real betting, no ML, no prediction
creation and no production sports data.

## Files To Modify Or Create
- `apps/api/app/core/constants.py`
- `apps/api/app/main.py`
- `apps/api/app/modules/providers/activation_readiness_final_gate.py`
- `apps/api/app/schemas/providers.py`
- `apps/api/tests/test_provider_activation_readiness_final_gate.py`
- Existing provider/system tests that assert the public phase label.
- `apps/api/README.md`
- `apps/api/pyproject.toml`
- `docs/index.md`
- `docs/21_API_AND_DATABASE_SPEC.md`
- `docs/34_PROVIDER_ACTIVATION_READINESS_FINAL_GATE.md`

## Out Of Scope
- No POST, PUT, PATCH or DELETE route.
- No provider connector, API-Football connection, scraping, real URL, real endpoint path, real credential,
  secret exposure, egress, ingestion, canonical write, SQLAlchemy model change, Alembic migration, bookmaker,
  stake execution, ML or prediction creation.
- No frontend/design changes.

## Phase 15 Work
- Update runtime metadata to `phase-15-provider-activation-readiness-final-gate`.
- Add `ProviderFinalActivationPrerequisites`, all fields locked to `false`.
- Add `ProviderActivationReadinessFinalGate`, all activation, provider, network, DB, credential and production
  flags locked to `false`, with `decision=blocked`.
- Add a builder/refusal helper that resets caller-provided objects, including unsafe `model_construct` inputs.
- Expose `activation_readiness_final_gate` from `GET /api/v1/providers/readiness`.
- Document the final prerequisites: license, terms, quotas, rate limits, latency, egress, secret manager, log
  redaction, monitoring, alerting, reconciliation, rollback, anonymized real golden payloads and security audit.

## Expected Tests
- Final gate is blocked by default.
- Dangerous constructed inputs are reset to safe defaults.
- `GET /api/v1/providers/readiness` exposes the final gate and remains secret-free and URL-free.
- POST, PUT, PATCH and DELETE on `/api/v1/providers/readiness` return `405`.
- Readiness does not touch network sockets.
- Existing provider, sandbox, secret safety, shell and security tests remain green.

## Risks E001-E084
- E001-E005: provider completeness, provenance, multi-source readiness and temporal availability remain blocked.
- E026: no advice or prediction creation is introduced.
- E049: pre-match/live separation remains intact.
- E065-E074: provider activation, fallback, timestamps, mapping, latency, logging and secret handling stay gated.
- E079: no retroactive mutation path is added.
- E083-E084: no real betting and limitations remain explicit.

## Validation Strategy
Run from `apps/api`:
- `pip install -e ".[dev]"`
- `ruff check .`
- `pytest`

Run from repository root:
- `git diff --check`

Run only if local DB/Docker is available:
- `alembic check`
