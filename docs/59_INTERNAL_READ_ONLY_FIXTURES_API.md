# Internal Read-Only Fixtures API

Phase 40 adds a backend-only service layer for internal read-only access to existing API-Football fixture staging rows.

This phase is internal read-only only. It builds a validated read plan and serializes already fetched row mappings into a
compact public-safe response shape. It does not add a public route because the current API has no internal auth/RBAC
boundary for staging fixture data.

## Public-safe response
The service returns:

- `provider=api-football`
- `mode=fixture_staging_internal_read_only_api`
- `target_table=api_football_fixture_staging`
- `read_only=true`
- `db_writes=false`
- `prediction_created=false`
- `betting_created=false`
- validated filters, `limit`, and `offset`
- response row count
- serialized fixture rows

Serialized fixture rows include only Phase 35 staging fields that are safe to expose internally:

- provider and provider fixture, league, season, team IDs
- fixture date, timezone, status, team names, goals, and score fields
- `payload_hash`, `payload_top_level_keys`, `fetched_at`, and `source_mode`

The service does not return raw provider bodies, provider URLs, credentials, secret material, odds, bookmaker, stake,
prediction output, confidence scoring, model output, or betting fields.

## Filter validation
The read plan accepts only:

- `provider=api-football`
- positive integer `provider_league_id`
- `provider_season` between `1900` and `2100`
- non-empty `fixture_status_short`
- `date_from` and `date_to` as valid `YYYY-MM-DD` calendar dates
- `limit` between `1` and `100`
- `offset` greater than or equal to `0`

Invalid values are rejected. Phase 40 does not clamp unsafe limits or silently correct filters.

## No public free endpoint
Phase 40 does not wire a FastAPI route. A future route must be internal-only, authenticated, rate limited, and documented
before staging fixture data can be exposed over HTTP.

## No DB write
Phase 40 performs no DB write. It adds no insert, update, delete, upsert, session add, transaction commit, migration,
schema change, ingestion job, scheduled task, or fixture mutation.

The Phase 35 `api_football_fixture_staging` schema remains unchanged.

## No real API call
Phase 40 performs no real API call, no API-Football request, no provider transport, no provider authentication, no
provider URL construction, and no quota-consuming action.

## No ingestion runtime
Phase 40 does not trigger a runner, start ingestion, backfill fixtures, create staging rows, or fetch provider data. It
only prepares and serializes read-only access to rows that already exist.

## No prediction
No Phase 40 output can feed features, backtests, calibration, model training, prediction ledgers, scenario simulation,
confidence scoring, or user advice. `prediction_created=false` is only a safety flag.

## No betting/odds
No betting/odds path is authorized. Phase 40 creates no odds snapshot, bookmaker field, stake field, value calculation,
ticket selection, betting decision, or real-money action.

## Phase 41 boundary
Phase 41 will add data freshness and provider audit trail checks for fixture staging reads. It must still avoid free
ingestion, provider calls, public unauthenticated routes, prediction, betting, odds, bookmaker, stake, ML, frontend
changes, and schema changes unless explicitly authorized.
