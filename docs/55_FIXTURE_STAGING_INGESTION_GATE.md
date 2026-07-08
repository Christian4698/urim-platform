# Fixture Staging Ingestion Gate

Phase 36 adds a backend-only dry-run gate for future API-Football fixture staging ingestion.

This phase does not ingest fixtures. It receives normalized fixture dictionaries in memory, checks whether they are
eligible for a later staging write, and returns only public-safe aggregate evidence.

## Gate behavior
The gate targets the future table:

- `api_football_fixture_staging`

It reports:

- candidate, accepted, and rejected counts;
- whether `payload_hash`, `payload_top_level_keys`, and `source_mode` are present;
- duplicate `provider_fixture_id` values inside the batch;
- missing required field names by candidate reference;
- blocking reasons;
- fixed safety flags showing no database, prediction, or betting output was created.

The output is public-safe. It does not return provider bodies, provider URLs, API keys, complete fixture lists, or team
names.

## Required candidate fields
A candidate can be accepted only when these fields are present:

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

The provider must be exactly `api-football`. Numeric IDs must be integer-like and not booleans. Blank strings and
`NULL`-like values are rejected for required fields.

## Optional inert fields
These normalized score and goal fields may be present, but they do not activate any downstream path:

- `goals_home`
- `goals_away`
- `score_halftime_home`
- `score_halftime_away`
- `score_fulltime_home`
- `score_fulltime_away`

## Blocking rules
The gate blocks readiness when:

- there are no candidates;
- `source_mode` is blank;
- `payload_hash` is blank;
- `payload_top_level_keys` is empty;
- a candidate provider is not `api-football`;
- required candidate fields are missing;
- duplicate `provider_fixture_id` values exist in the batch;
- a candidate contains odds, bookmaker, stake, prediction, or betting fields.

All candidates sharing a duplicate `provider_fixture_id` are rejected so the accepted and rejected counts stay explicit.
Duplicate output contains IDs only.

## No DB write in Phase 36
Phase 36 performs no DB write in Phase 36. It adds no ingestion runtime, no upsert path, no scheduled job, no SQL session,
no SQL statement, no migration, and no schema change.

The Phase 35 table remains empty unless another authorized future phase writes to it.

## No real API call
Phase 36 performs no real API call, no API-Football request, no provider authentication, and no quota-consuming action.
Tests use fake in-memory normalized fixtures only.

## No raw provider payload
The gate accepts compact normalized fixture dictionaries only. It does not store, echo, reconstruct, or serialize raw
provider payload content.

## No prediction
No Phase 36 output can feed features, backtests, calibration, model training, prediction ledgers, scenario simulation, or
user advice. The gate exposes `prediction_created=false` only as a safety flag.

## No betting/odds
No betting/odds path is authorized. Phase 36 rejects odds, bookmaker, stake, prediction, and betting fields in candidate
fixtures and exposes `betting_created=false` only as a safety flag.

## Phase 37/38 boundary
Phase 37/38 must prepare leagues/teams read-only reconciliation before full staging linkage. Future work must define
entity identity, provenance, `available_at`, `source_version`, `quality_flags`, rollback, quota controls, and security
review before any staging write can be authorized.
