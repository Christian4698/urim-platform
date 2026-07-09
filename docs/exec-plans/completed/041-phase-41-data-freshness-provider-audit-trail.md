# Phase 41 Data Freshness and Provider Audit Trail

## Objective
Add a backend-only read-only freshness and provider audit layer for API-Football fixture staging rows already available in
memory.

## Completed Scope
- Added a deterministic freshness audit function requiring injected timezone-aware UTC `now_utc`.
- Returned public-safe aggregate counters for row freshness, payload evidence, source modes, fixture statuses, and
  readiness blockers.
- Treated stale rows, missing/invalid `fetched_at`, missing payload evidence, missing provider fixture IDs, wrong
  providers, and empty batches as blockers for internal read readiness.
- Kept Phase 41 free of DB writes, schema changes, API-Football calls, secrets, quota use, public endpoints, frontend
  changes, ingestion runtime, prediction, ML, confidence scoring, odds, bookmaker, stake, and betting.

## Files
- `apps/api/app/modules/providers/api_football_fixture_data_freshness_audit.py`
- `apps/api/tests/test_api_football_fixture_data_freshness_audit.py`
- `docs/60_DATA_FRESHNESS_AND_PROVIDER_AUDIT_TRAIL.md`
- `docs/index.md`

## Validation Commands
- `ruff check .`
- `pytest`
- `git diff --check`
- `git status --short --untracked-files=all`

## Risks Tracked
- E001 incomplete staging context.
- E002 stale staging data.
- E003 malformed provider fixture IDs or timestamps.
- E005 future or invalid temporal evidence.
- E026 forced advice before data sufficiency.
- E065 single-provider fragility.
- E071 missing values confused with zero.
- E072 fixture status and provider ID audit gaps.
- E074 provider secret exposure.
- E083-E084 unsafe betting pressure or unclear limits.
