# Data Freshness and Provider Audit Trail

Phase 41 adds a backend-only data freshness and provider audit layer for API-Football fixture staging rows.

This phase is read-only audit only. It receives rows already loaded in memory, evaluates compact freshness and provider
evidence, and returns aggregate public-safe counters and blocking reasons. It does not return fixture lists or raw
provider content.

## Public-safe audit output
The audit returns:

- `provider=api-football`
- `mode=fixture_data_freshness_provider_audit_trail`
- `target_table=api_football_fixture_staging`
- `read_only=true`
- `db_writes=false`
- `prediction_created=false`
- `betting_created=false`
- configured freshness threshold
- row, fresh, stale, missing timestamp, and invalid timestamp counts
- payload hash presence counts
- payload top-level key presence count
- aggregated `source_modes`
- aggregated `fixture_status_short` counts
- missing `provider_fixture_id` count
- internal-read readiness and blocking reasons

The audit uses only `provider`, `provider_fixture_id`, `fetched_at`, `source_mode`, `payload_hash`,
`payload_top_level_keys`, and `fixture_status_short`.

It does not return raw provider bodies, complete fixture lists, provider URLs, credentials, secret material, API keys,
auth material, tokens, odds, bookmaker, stake, prediction payloads, scoring output, model output, or betting fields.

## Freshness rules
A row is fresh when:

- `fetched_at` exists;
- `fetched_at` is a timezone-aware timestamp;
- `fetched_at` is not in the future relative to the injected `now_utc`;
- its age is less than or equal to `freshness_threshold_minutes`.

A row is stale when its valid `fetched_at` age exceeds `freshness_threshold_minutes`.

Rows with missing `fetched_at` increase `missing_fetched_at_count`. Rows with malformed, naive, non-timestamp, or future
`fetched_at` values increase `invalid_fetched_at_count`.

`now_utc` must be injected by the caller as a timezone-aware UTC datetime so tests and future audits remain
deterministic. `freshness_threshold_minutes` must be strictly positive.

## Readiness blockers
`ready_for_internal_read` is false when:

- there are no rows;
- a row provider is not `api-football`;
- any row is stale;
- any row has missing or invalid `fetched_at`;
- any row is missing `payload_hash`;
- any row is missing `payload_top_level_keys`;
- any row is missing a valid `provider_fixture_id`.

These blockers are data trust reasons for internal reads only. They are not model confidence, betting advice, or user
recommendations.

## No DB write
Phase 41 performs no DB write. It creates no insert, update, delete, upsert, session add, transaction commit, migration,
schema change, ingestion job, scheduled task, or fixture mutation.

The Phase 35 `api_football_fixture_staging` schema remains unchanged.

## No real API call
Phase 41 performs no real API call, no API-Football request, no provider transport, no provider authentication, no
provider URL construction, and no quota-consuming action.

## No ingestion runtime
Phase 41 does not trigger a runner, start ingestion, backfill fixtures, create staging rows, or fetch provider data. It
only audits rows already present in memory.

## No prediction/scoring
No Phase 41 output can feed features, backtests, calibration, model training, prediction ledgers, scenario simulation,
confidence scoring, or user advice. Freshness is an audit condition only.

## No betting/odds
No betting/odds path is authorized. Phase 41 creates no odds snapshot, bookmaker field, stake field, value calculation,
ticket selection, betting decision, or real-money action.

## Phase 42 boundary
Phase 42 will add only the feature snapshot contract without ML. It must still avoid free ingestion, provider calls,
public unauthenticated routes, prediction, betting, odds, bookmaker, stake, ML, frontend changes, and schema changes
unless explicitly authorized.
