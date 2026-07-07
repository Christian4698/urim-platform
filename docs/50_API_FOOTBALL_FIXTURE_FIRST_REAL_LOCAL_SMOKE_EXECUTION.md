# API-Football Fixture First Real Local Smoke Execution

Phase 31 adds the local-only execution script for the first controlled real API-Football `/fixtures` smoke.

- `provider=api-football`
- `endpoint=/fixtures`
- `mode=fixture_first_real_local_smoke_only`
- `db_writes=false`
- `prediction_created=false`
- `betting_created=false`
- The execution must remain manual, local and controlled.
- Automated tests must use fake transports or monkeypatches only.
- No automated tests may call the real provider.
- No provider payload is returned or stored.
- No public endpoint is added.

## Why this phase exists
Phase 30 proved that local gates can decide whether a future `/fixtures` smoke is allowed. Phase 31 adds the manual
execution script that can perform that single controlled call only when all local gates are present.

This is still not provider activation. It is a narrow evidence-gathering path for one local operator action.

## Required local gates
The script requires these local-only inputs before any call can happen:

- `APP_ENV=development`
- `URIM_API_FOOTBALL_FIXTURE_SMOKE_ENABLED=1`
- `URIM_API_FOOTBALL_FIXTURE_SMOKE_AUTH=<local operator value>`
- `URIM_API_FOOTBALL_FIXTURE_SMOKE_BASE_URL=<local fixture endpoint reference>`
- `URIM_API_FOOTBALL_FIXTURE_SMOKE_DATE=YYYY-MM-DD`
- `URIM_API_FOOTBALL_FIXTURE_SMOKE_TIMEZONE=Africa/Kinshasa`
- `URIM_API_FOOTBALL_FIXTURE_SMOKE_READ_ONLY=1`
- `URIM_API_FOOTBALL_FIXTURE_SMOKE_NON_PROD=1`
- `URIM_LOCAL_PREFLIGHT_NO_DB_WRITE_CONFIRMED=1`
- `URIM_LOCAL_PREFLIGHT_NO_PREDICTION_CONFIRMED=1`
- `URIM_LOCAL_PREFLIGHT_NO_BETTING_CONFIRMED=1`

The local operator value is never printed, stored or committed.

## Request shape
The request uses only:

- `date`
- `timezone`

The script rejects provider references for predictions or odds paths. It does not add league, team, season, bookmaker,
stake, prediction or betting parameters.

## Allowed header
The only provider auth header used by the script is `x-apisports-key`.

Other auth styles remain forbidden for this phase.

## Public-safe success output
On success, the script returns only:

- `provider`
- `endpoint`
- `mode`
- `executed`
- `status`
- `request_query`
- `normalized_count`
- `fixtures`
- `payload_hash`
- `payload_top_level_keys`
- `db_writes`
- `prediction_created`
- `betting_created`

The script never returns the provider URL, local auth value, raw provider content or the full environment.

## HTTP errors
Provider HTTP errors are converted to public-safe JSON with a status and HTTP code only. The response body, stack trace,
local auth value and provider reference are not exposed.

## No DB ingestion
No Phase 31 output may be inserted into PostgreSQL, object storage, provider observation tables, fixture tables or
canonical entity tables.

## No prediction
No Phase 31 field may feed a model, feature store, backtest, calibration report, prediction ledger, scenario
simulation or user advice.

## No betting/odds
Phase 31 adds no odds snapshots, bookmaker fields, stake fields, value calculations, betting decisions or real-money
execution path.

## Next phase recommendation
The next safe phase should document the public-safe evidence from the first fixture real local smoke after an operator
has run it manually. That evidence should include only the status, request query, normalized count, hash and top-level
keys, with no provider payload.
