# Feature Snapshot Contract Without ML

Phase 42 adds a backend-only feature snapshot contract for API-Football fixture staging rows.

This phase is feature snapshot contract only. It receives public-safe staging rows already loaded in memory and projects
eligible rows into deterministic snapshot candidates. It does not persist feature snapshots and does not create model
features for training or prediction.

## Public-safe output
The contract returns:

- `provider=api-football`
- `mode=fixture_feature_snapshot_contract_without_ml`
- `target_table=feature_snapshots`
- `read_only=true`
- `db_writes=false`
- `prediction_created=false`
- `betting_created=false`
- `ml_model_used=false`
- `confidence_score_created=false`
- `feature_schema_version`
- `source_mode`
- candidate, accepted, and rejected counts
- allowlisted feature keys
- accepted snapshot candidates
- blocking reasons

Snapshot candidates contain only deterministic fields copied from staging rows plus the contract metadata:

- provider and provider fixture, league, season, home-team, and away-team IDs
- fixture date, timezone, status, goals, and score fields
- `payload_hash`, `fetched_at`, `source_mode`, and `feature_schema_version`

Snapshot candidates do not include team names, raw provider bodies, provider URLs, credentials, secret material, API
keys, auth material, tokens, odds, bookmaker, stake, prediction payloads, probabilities, recommended outcomes, suggested
bets, model output, confidence scoring, or betting fields.

## Acceptance rules
A row becomes a snapshot candidate only when:

- the row provider is exactly `api-football`;
- `provider_fixture_id` is present and positive integer-like;
- `provider_league_id` is present and positive integer-like;
- `fixture_date` is present;
- `payload_hash` is present;
- `feature_schema_version` is non-empty;
- `source_mode` is non-empty.

Invalid rows are rejected from the candidate list and represented only through aggregate counts and blocking reasons.
Rows are not repaired, enriched, normalized with future data, or joined to provider payloads.

## No DB write
Phase 42 performs no DB write. It creates no insert, update, delete, upsert, session add, transaction commit, migration,
schema change, ingestion job, scheduled task, fixture mutation, or persisted feature snapshot.

The Phase 35 `api_football_fixture_staging` schema and existing `feature_snapshots` table remain unchanged.

## No real API call
Phase 42 performs no real API call, no API-Football request, no provider transport, no provider authentication, no
provider URL construction, and no quota-consuming action.

## No ingestion runtime
Phase 42 does not trigger a runner, start ingestion, backfill fixtures, create staging rows, or fetch provider data. It
only projects rows already present in memory.

## No prediction
Phase 42 creates no prediction, forecast, official outcome, model decision, scenario simulation, user advice, or
prediction ledger row.

## No ML
Phase 42 does not train, load, call, select, calibrate, evaluate, or version an ML model. It does not create model-ready
training data or run backtests.

## No confidence scoring
Phase 42 creates no confidence score, probability, certainty label, edge estimate, recommendation, or ranked outcome.

## No betting/odds
No betting/odds path is authorized. Phase 42 creates no odds snapshot, bookmaker field, stake field, value calculation,
ticket selection, betting decision, or real-money action.

## Phase 43 boundary
Phase 43 may add only a baseline analytics engine without official prediction. It must not add ML, official
probabilities, confidence scoring, betting, odds, bookmaker, stake, public unauthenticated routes, provider calls, free
ingestion, frontend changes, or schema changes unless explicitly authorized.
