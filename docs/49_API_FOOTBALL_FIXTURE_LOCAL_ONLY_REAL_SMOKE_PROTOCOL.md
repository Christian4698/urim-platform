# API-Football Fixture Local-Only Real Smoke Protocol

Phase 30 prepares the local-only protocol for a future controlled API-Football `/fixtures` real smoke.

- `provider=api-football`
- `endpoint=/fixtures`
- `mode=fixture_local_real_smoke_protocol_only`
- `executed=false`
- `db_writes=false`
- `prediction_created=false`
- `betting_created=false`
- No real API-Football call is made.
- No quota is consumed.
- No provider secret or auth header is required in this phase.
- No provider payload is returned or stored.
- No public endpoint is added.

## Why prepare a protocol before the real /fixtures call
The fixture smoke protocol defines the exact local confirmations that must be present before a later phase may make
one controlled `/fixtures` request. This keeps the future real smoke narrow, auditable and reversible before any
provider observation, database ingestion, prediction or betting path exists.

Phase 30 is not an execution phase. It only answers whether a future local real smoke would be allowed to proceed.

## Local confirmations
The protocol may consider only these local confirmations:

- `APP_ENV=development`
- `URIM_API_FOOTBALL_FIXTURE_SMOKE_ENABLED=1`
- `URIM_API_FOOTBALL_FIXTURE_SMOKE_DATE=YYYY-MM-DD`
- `URIM_API_FOOTBALL_FIXTURE_SMOKE_TIMEZONE=Africa/Kinshasa`
- `URIM_API_FOOTBALL_FIXTURE_SMOKE_READ_ONLY=1`
- `URIM_API_FOOTBALL_FIXTURE_SMOKE_NON_PROD=1`
- `URIM_LOCAL_PREFLIGHT_NO_DB_WRITE_CONFIRMED=1`
- `URIM_LOCAL_PREFLIGHT_NO_PREDICTION_CONFIRMED=1`
- `URIM_LOCAL_PREFLIGHT_NO_BETTING_CONFIRMED=1`

These names are local gate confirmations, not public response fields.

## Minimal query
The only approved query for a future Phase 31 smoke is:

- `date`
- `timezone`

Phase 30 does not accept `league`, `team` or `season`. It also rejects odds, bookmaker, stake, prediction and betting
parameters.

## No real API call
Phase 30 performs no network call, opens no socket, constructs no provider URL and executes no provider request. It
only validates local readiness gates.

## No quota
Because Phase 30 does not contact API-Football, it consumes no Free Plan quota.

## No provider secret
The API key is not requested, loaded, printed, stored or validated in Phase 30. It may be used only in a future phase
that explicitly executes one controlled local smoke and still keeps the output public-safe.

## No DB ingestion
No Phase 30 output may be inserted into PostgreSQL, object storage, provider observation tables, fixture tables or
canonical entity tables.

## No prediction
No Phase 30 field may feed a model, feature store, backtest, calibration report, prediction ledger, scenario
simulation or user advice.

## No betting/odds
Phase 30 adds no odds snapshots, bookmaker fields, stake fields, value calculations, betting decisions or real-money
execution path.

## Public-safe output
The script returns only:

- `provider`
- `endpoint`
- `mode`
- `executed`
- `ready_for_fixture_real_smoke`
- `blocking_reasons` when not ready
- `approved_query` when ready
- `db_writes`
- `prediction_created`
- `betting_created`

It never returns the full environment, provider credentials, provider URLs or provider payload content.

## Next phase recommendation
The next recommended phase is Phase 31: Fixture First Real Local Smoke Execution. It should remain local-only, perform
at most one controlled `/fixtures` call, return only public-safe evidence, write no DB rows, create no prediction and
open no odds or betting path.
