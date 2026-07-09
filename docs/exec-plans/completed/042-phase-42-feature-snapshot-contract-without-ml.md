# Phase 42 Feature Snapshot Contract Without ML

## Objective
Add a backend-only read-only feature snapshot contract that projects API-Football fixture staging rows into deterministic
snapshot candidates without ML, prediction, scoring, betting, or DB writes.

## Completed Scope
- Added an in-memory feature snapshot contract function with explicit schema version and source mode metadata.
- Returned public-safe counts, allowlisted feature keys, accepted snapshot candidates, and aggregate blocking reasons.
- Rejected rows with wrong provider, missing fixture ID, missing league ID, missing fixture date, or missing payload hash.
- Excluded team names, raw provider material, secrets, odds, model output, probabilities, recommendations, and betting
  fields from snapshot candidates.
- Kept Phase 42 free of DB writes, schema changes, API-Football calls, secrets, quota use, public endpoints, frontend
  changes, ingestion runtime, prediction, ML, confidence scoring, odds, bookmaker, stake, and betting.

## Files
- `apps/api/app/modules/providers/api_football_fixture_feature_snapshot_contract.py`
- `apps/api/tests/test_api_football_fixture_feature_snapshot_contract.py`
- `docs/61_FEATURE_SNAPSHOT_CONTRACT_WITHOUT_ML.md`
- `docs/index.md`

## Validation Commands
- `ruff check .`
- `pytest`
- `git diff --check`
- `git status --short --untracked-files=all`

## Risks Tracked
- E001 incomplete staging context.
- E003 malformed fixture IDs or league IDs.
- E005 future temporal use before a true `as_of` feature snapshot contract.
- E026 forced advice before data sufficiency.
- E029-E031 future leakage in future feature generation or evaluation.
- E037-E039 market, lineup, or target-match leakage in later phases.
- E071 missing values confused with zero.
- E072 fixture/team/league mapping errors.
- E074 provider secret exposure.
- E083-E084 unsafe betting pressure or unclear limits.
