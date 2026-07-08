# Phase 37 API-Football Leagues/Teams Read-Only Builders

## Objective
Add local-only backend request builders for API-Football `/leagues` and `/teams`.

## Completed Scope
- Added pure request description helpers for `/leagues` and `/teams`.
- Enforced strict query allowlists and rejected unsafe provider, credential, prediction, odds, and betting parameters.
- Returned public-safe dictionaries only.
- Kept Phase 37 free of HTTP transport, real API-Football calls, quota use, secrets, raw provider payloads, DB writes, ingestion, Alembic/schema changes, public endpoints, frontend changes, prediction, ML, odds, bookmaker, stake, and betting.
- Performed no GitHub remote action, commit, push, or PR creation.

## Files
- `apps/api/app/modules/providers/api_football_leagues_teams_request_builder.py`
- `apps/api/tests/test_api_football_leagues_teams_request_builder.py`
- `docs/56_API_FOOTBALL_LEAGUES_TEAMS_READ_ONLY_BUILDERS.md`
- `docs/index.md`

## Validation Commands
- `ruff check .`
- `pytest`
- `git diff --check`
- `git status --short --untracked-files=all`

## Risks Tracked
- E001 incomplete provider coverage or entity context.
- E003 incorrect provider IDs or query shape.
- E005 temporal use before availability in later phases.
- E026 forced betting advice.
- E065 provider outage or unsupported endpoint assumptions.
- E071 missing values confused with real values.
- E072 league/team ID mapping errors.
- E074 API key exposure.
- E083-E084 unsafe betting pressure or unclear limits.
