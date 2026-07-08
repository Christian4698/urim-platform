# Phase 38 API-Football Leagues/Teams Response Normalizers

## Objective
Add local-only read-only response normalizers for fake/test-only API-Football `/leagues` and `/teams` payloads.

## Completed Scope
- Normalized compact public-safe league, season, team, and venue fields from in-memory fake/test-only payloads.
- Computed stable payload hashes and top-level key evidence without returning provider bodies.
- Kept Phase 38 free of HTTP transport, real API-Football calls, quota use, secrets, raw provider payload output, DB writes, ingestion, public endpoints, frontend changes, Alembic/schema changes, prediction, ML, odds, bookmaker, stake, and betting.

## Files
- `apps/api/app/modules/providers/api_football_leagues_teams_response_normalizer.py`
- `apps/api/tests/test_api_football_leagues_teams_response_normalizer.py`
- `docs/57_API_FOOTBALL_LEAGUES_TEAMS_RESPONSE_NORMALIZERS.md`
- `docs/index.md`

## Validation Commands
- `ruff check .`
- `pytest`
- `git diff --check`
- `git status --short --untracked-files=all`

## Risks Tracked
- E001 incomplete provider context.
- E003 incorrect league/team IDs or duplicate entity assumptions.
- E005 temporal use before availability in later phases.
- E026 forced advice before data sufficiency.
- E065 single-provider fragility.
- E071 missing values confused with zero.
- E072 league/team mapping errors.
- E074 API key exposure.
- E083-E084 unsafe betting pressure or unclear limits.
