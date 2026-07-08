# API-Football Leagues/Teams Read-Only Builders

Phase 37 adds local-only backend builders for API-Football `/leagues` and `/teams` request descriptions.

This phase is read-only only. It prepares safe dictionaries for later read-only provider work, but it does not add
transport, normalization, database ingestion, or public runtime behavior.

## Public-safe request shape
Each builder returns only:

- `provider=api-football`
- `endpoint=/leagues` or `endpoint=/teams`
- `method=GET`
- `read_only=true`
- `query`
- `db_writes=false`
- `prediction_created=false`
- `betting_created=false`

The query contains only validated allowlisted parameters. Empty params are allowed because this phase only describes a
safe local request shape; a later transport phase may define provider-specific required combinations.

## Allowed /leagues parameters
- `id`: positive integer.
- `name`: non-empty string after trimming.
- `country`: non-empty string after trimming.
- `code`: non-empty string after trimming.
- `season`: integer between `1900` and `2100`.
- `team`: positive integer.
- `type`: non-empty string after trimming.
- `current`: boolean.
- `search`: non-empty string after trimming.
- `last`: positive integer.

## Allowed /teams parameters
- `id`: positive integer.
- `name`: non-empty string after trimming.
- `league`: positive integer.
- `season`: integer between `1900` and `2100`.
- `country`: non-empty string after trimming.
- `code`: non-empty string after trimming.
- `venue`: positive integer.
- `search`: non-empty string after trimming.

Numeric strings are rejected for numeric fields. Booleans are rejected for numeric fields even though Python treats
booleans as integers.

## Forbidden parameters
The builders reject unknown parameters and these unsafe names:

- `odds`
- `bookmaker`
- `stake`
- `prediction`
- `predictions`
- `betting`
- raw provider payload fields
- API key fields
- auth fields
- secret fields

## No real API call
Phase 37 makes no real API call. It does not import or configure HTTP transport, provider clients, sockets, headers,
provider URLs, or auth material. No API-Football quota is consumed.

## No DB write
Phase 37 makes no DB write. It adds no SQLAlchemy model, no Alembic migration, no SQL statement, no session operation,
no job, and no scheduler.

## No ingestion
Phase 37 adds no ingestion. It does not store leagues, teams, fixtures, raw provider payloads, canonical entities, or
staging rows.

## No prediction
No Phase 37 request description may feed features, model training, backtests, calibration, prediction ledgers,
scenario simulation, or user advice.

## No betting/odds
No betting/odds path is authorized. Phase 37 rejects odds, bookmaker, stake, prediction, predictions, and betting
parameters and creates no real-money action.

## Phase 38 boundary
Phase 38 may add only the normalizers leagues/teams for static local test data. It must still avoid HTTP transport,
real provider calls, DB writes, ingestion, prediction, odds, bookmaker, stake, and betting.
