# Baseline Analytics Engine Without Official Prediction

Phase 43 adds a backend-only, read-only baseline analytics engine for API-Football fixture feature snapshot candidates.

This phase is baseline analytics only. It receives Phase 42 snapshot candidates already loaded in memory and returns
deterministic descriptive aggregates. Scope tags: no official prediction, no real api call, no db write, no ingestion
runtime, no ML, no confidence scoring, and no betting/odds. It does not create a probability, forecast, advice, ranking,
confidence score, model artifact, odds view, betting decision, or persisted row.

## Public-safe output
The engine returns:

- `provider=api-football`
- `mode=fixture_baseline_analytics_without_official_prediction`
- `read_only=true`
- `db_writes=false`
- `prediction_created=false`
- `official_prediction_created=false`
- `betting_created=false`
- `ml_model_used=false`
- `confidence_score_created=false`
- `analytics_schema_version`
- `source_mode`
- candidate, accepted, and rejected counts
- fixture status, league, and season count distributions
- completed, live, scheduled, and cancelled/postponed fixture counts
- fulltime-score goal totals and average total goals when both fulltime scores are present
- descriptive sample flags
- blocking reasons

The output contains aggregate values only. It does not echo source candidate rows, team names, raw provider bodies,
provider URLs, credentials, secret material, API keys, auth material, tokens, odds, bookmaker, stake, predictions,
probabilities, recommended outcomes, suggested bets, final picks, model output, confidence scoring payloads, or betting
signals.

## Acceptance rules
A snapshot candidate contributes to analytics only when:

- the candidate provider is exactly `api-football`;
- `provider_fixture_id` is present and positive integer-like;
- `provider_league_id` is present and positive integer-like;
- `fixture_status_short` is present and non-empty;
- `analytics_schema_version` is non-empty;
- `source_mode` is non-empty.

Invalid candidates are rejected from the aggregate sample and represented only through counts and blocking reasons.
Rows are not repaired, enriched, joined to provider payloads, or normalized with future data.

An empty input sample is allowed and returns `sample_is_empty=true`, `accepted_count=0`, empty distributions, zero fixture
family counts, and no fulltime-score average.

## Descriptive only
Phase 43 may produce counters, distributions, means, simple historical ratios, and descriptive signals. These signals are
not predictions, not probabilities, not confidence scores, not betting recommendations, and not official Kairos
prediction records.

Missing fulltime scores remain separate from zero-goal outcomes. A `0-0` score contributes to the fulltime-score sample;
missing fulltime score fields do not.

## No DB write
Phase 43 performs no DB write. It creates no insert, update, delete, upsert, session add, transaction commit, migration,
schema change, fixture mutation, feature snapshot persistence, or prediction ledger row.

## No real API call
Phase 43 performs no real API call, no API-Football request, no provider transport, no provider authentication, no
provider URL construction, and no quota-consuming action.

## No ingestion runtime
Phase 43 does not trigger a runner, start ingestion, backfill fixtures, create staging rows, fetch provider data, or run
an automatic job. It only analyzes snapshot candidates already present in memory.

## No ML
Phase 43 does not train, load, call, select, calibrate, evaluate, or version an ML model. It does not create model
outputs, official probabilities, backtests, or free-form predictive scoring.

## No confidence scoring
Phase 43 creates no confidence score, certainty label, edge estimate, probability, recommendation, ranked outcome, or
buy/sell/win/lose signal.

## No betting/odds
No betting/odds path is authorized. Phase 43 creates no odds snapshot, bookmaker field, stake field, value calculation,
ticket selection, betting decision, or real-money action.

## Phase 44 boundary
Phase 44 may add only a Kairos prediction protocol gate. It is not yet free prediction and must not create unrestricted
official predictions, probabilities, confidence scoring, betting, odds, bookmaker, stake, public unauthenticated routes,
provider calls, ingestion runtime, frontend changes, or schema changes unless explicitly authorized.
