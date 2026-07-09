# Phase 39 Fixtures/Leagues/Teams Staging Linkage Gate

## Objective
Add a backend-only dry-run gate that checks whether normalized API-Football fixtures can link to normalized leagues and
teams before any future staging ingestion.

## Completed Scope
- Added a pure in-memory fixture/league/team linkage gate for compact normalized dictionaries.
- Returned public-safe counts, duplicate league/team IDs, missing-reference counts, readiness, and blocking reasons.
- Kept Phase 39 free of DB writes, schema changes, API-Football calls, secrets, quota use, public endpoints, frontend
  changes, ingestion runtime, prediction, ML, odds, bookmaker, stake, and betting.

## Files
- `apps/api/app/modules/providers/api_football_fixture_league_team_staging_linkage_gate.py`
- `apps/api/tests/test_api_football_fixture_league_team_staging_linkage_gate.py`
- `docs/58_API_FOOTBALL_FIXTURE_LEAGUE_TEAM_STAGING_LINKAGE_GATE.md`
- `docs/index.md`

## Validation Commands
- `ruff check .`
- `pytest`
- `git diff --check`
- `git status --short --untracked-files=all`

## Risks Tracked
- E001 incomplete fixture, league, or team context.
- E003 incorrect or duplicated provider IDs.
- E005 future temporal use before availability contracts are defined.
- E026 forced advice before data sufficiency.
- E065 single-provider fragility.
- E071 missing values confused with zero.
- E072 league/team mapping errors.
- E074 provider secret exposure.
- E083-E084 unsafe betting pressure or unclear limits.
