# Phase 40 Internal Read-Only Fixtures API

## Objective
Add a backend-only service layer for internal read-only access to existing API-Football fixture staging rows.

## Completed Scope
- Added a strict read-plan builder for `api_football_fixture_staging` with provider, filter, limit, offset, and date
  validation.
- Added a public-safe serializer that returns only allowlisted fixture staging fields.
- Kept Phase 40 service-only because no internal auth/RBAC route boundary exists yet.
- Kept Phase 40 free of DB writes, schema changes, API-Football calls, secrets, quota use, public endpoints, frontend
  changes, ingestion runtime, prediction, ML, confidence scoring, odds, bookmaker, stake, and betting.

## Files
- `apps/api/app/modules/providers/api_football_fixture_staging_read_api.py`
- `apps/api/tests/test_api_football_fixture_staging_read_api.py`
- `docs/59_INTERNAL_READ_ONLY_FIXTURES_API.md`
- `docs/index.md`

## Validation Commands
- `ruff check .`
- `pytest`
- `git diff --check`
- `git status --short --untracked-files=all`

## Risks Tracked
- E001 incomplete staging context.
- E003 incorrect fixture IDs or malformed filters.
- E005 future temporal use before Phase 41 freshness and audit checks.
- E026 forced advice before data sufficiency.
- E065 single-provider fragility.
- E071 missing values confused with zero.
- E072 fixture/team/league mapping errors.
- E074 provider secret exposure.
- E083-E084 unsafe betting pressure or unclear limits.
