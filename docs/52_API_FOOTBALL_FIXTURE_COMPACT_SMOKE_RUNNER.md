# API-Football Fixture Compact Smoke Runner

Phase 33 adds a local-only PowerShell runner for the existing compact API-Football `/fixtures` smoke script.

This phase does not perform a real provider call during implementation or automated validation. The runner only gives a
local operator a controlled wrapper around the Phase 31/32 compact smoke path.

## Local-only runner
The runner is:

- `apps/api/scripts/run_fixture_first_real_local_smoke.ps1`

From `apps/api`, a local operator can launch it manually:

```powershell
.\scripts\run_fixture_first_real_local_smoke.ps1 -SmokeDate 2026-07-07
```

`-SmokeDate` defaults to `2026-07-07` and must be a real `YYYY-MM-DD` calendar date. The timezone is fixed to
`Africa/Kinshasa`.

## Secret handling
The runner reads the local API-Football auth material from the clipboard first. If the clipboard is empty or unavailable,
it asks for the value with a masked PowerShell prompt.

The runner must never:

- print the auth material;
- write the auth material to a file;
- create or update `.env`;
- leave `URIM_API_FOOTBALL_FIXTURE_SMOKE_AUTH` in the process environment after completion;
- leave the clipboard uncleared after the run.

## Compact output only
The wrapped Python script is still `api_football_fixture_first_real_local_smoke.py`.

Allowed public evidence remains compact output only:

- provider, endpoint, mode and status;
- `request_query.date` and `request_query.timezone`;
- `normalized_count`;
- `payload_hash`;
- `payload_top_level_keys`;
- `db_writes=false`;
- `prediction_created=false`;
- `betting_created=false`.

The runner must not print the provider URL, provider response body, reconstructed provider JSON, full fixture list,
fixture IDs, team names, leagues, countries or score rows.

## No DB write
Phase 33 creates no DB ingestion path, no model, no migration, no object-storage archive and no canonical fixture write.
The local confirmation `URIM_LOCAL_PREFLIGHT_NO_DB_WRITE_CONFIRMED=1` is set only for the temporary smoke process.

## No prediction
Phase 33 creates no feature snapshot, model call, calibration report, prediction ledger entry, scenario simulation or user
advice. The local confirmation `URIM_LOCAL_PREFLIGHT_NO_PREDICTION_CONFIRMED=1` is set only for the temporary smoke
process.

## No betting/odds
Phase 33 creates no odds snapshot, bookmaker field, stake field, value calculation, betting decision or real-money
execution path. The local confirmation `URIM_LOCAL_PREFLIGHT_NO_BETTING_CONFIRMED=1` is set only for the temporary
smoke process.

## Test boundary
Automated tests inspect the PowerShell runner as text only. No automated tests may call the real provider, consume the
Free Plan quota, read a real key, open a provider URL or execute the runner.

## Remaining limits
This runner does not prove provider activation readiness, coverage, pagination, latency, quota behavior, license
readiness, field-level provenance, entity reconciliation or temporal availability. Those remain future gated phases.
