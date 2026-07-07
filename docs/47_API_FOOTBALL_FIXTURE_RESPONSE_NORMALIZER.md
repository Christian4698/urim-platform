# API-Football Fixture Response Normalizer

Phase 28 adds a backend-only normalizer for fake/test-only API-Football `/fixtures` payloads held in memory.

- `provider=api-football`
- `endpoint=/fixtures`
- `read_only=true`
- `db_writes=false`
- `prediction_created=false`
- `betting_created=false`
- No real API-Football call is made.
- No quota is consumed.
- No provider secret or auth header is required.
- No provider response body is exposed.
- No public endpoint is added.

## Why normalize before DB ingestion
Normalization comes before ingestion because Kairos must prove the safe extraction shape before any provider
observation can become storage. This phase keeps the provider payload in memory, extracts only the fields allowed by
the fixture contract and returns a public-safe structure.

The normalizer does not create a canonical fixture table row, a provider observation row or a feature input. Later
ingestion must still add full provenance, temporal availability, source version, quality flags and raw hash lineage
before any DB write.

## Fake/test-only payloads
The payloads used in Phase 28 are fake/test-only fixtures owned by the test suite. They are not production fallbacks,
not provider evidence, not source-of-truth records and not quota-backed observations.

## Read-only normalization
Phase 28 accepts only an in-memory mapping and reads the `response` list when present. It handles an empty response
with `normalized_count=0`. Missing nested fixture fields are returned as `None`, never as invented zeroes or default
truth values.

## Safe evidence
The only safe evidence derived from the input payload is:

- `payload_hash`
- `payload_top_level_keys`

The hash is deterministic for the received payload shape. Top-level keys are listed without exposing their values.

## Allowed extracted fields
Only these fields may be extracted into each normalized fixture:

- `provider`
- `provider_fixture_id`
- `provider_league_id`
- `provider_season`
- `fixture_date`
- `fixture_timezone`
- `fixture_status_short`
- `fixture_status_long`
- `home_team_provider_id`
- `home_team_name`
- `away_team_provider_id`
- `away_team_name`
- `goals_home`
- `goals_away`
- `score_halftime_home`
- `score_halftime_away`
- `score_fulltime_home`
- `score_fulltime_away`

## Forbidden fields/actions
- Real API-Football calls.
- Free Plan quota use.
- Provider URL construction.
- Auth header construction or provider secret access.
- Provider response body commits in documentation.
- DB ingestion, DB models, Alembic migrations or canonical fixture writes.
- Prediction, ML, feature-store, backtest or user-advice activation.
- Odds, bookmaker, stake or betting paths.
- Public endpoints, frontend changes, schedulers, queues, webhooks or jobs.
- Reintroducing `apps/web/lib/integrations`, `_references/public-apis` or `docs/api-catalog.md`.

## No DB ingestion yet
No Phase 28 output may be inserted into PostgreSQL, object storage, fixture tables, provider observation tables or
canonical entity tables. The normalized structure is read-only and test-only until a later phase designs ingestion
gates.

## No prediction yet
No Phase 28 field may feed a model, feature store, backtest, calibration report, scenario simulation, prediction
ledger or user advice.

## No betting/odds yet
Phase 28 adds no odds snapshots, bookmaker fields, stake fields, value calculations, betting decisions or real-money
execution path.

## Next phase recommendation
The next safe phase should add a fixture read-only transport adapter/harness or a fixture contract bridge. It should
still avoid direct DB ingestion, real provider calls in tests, quota use, provider response commits, prediction, odds
and betting.
