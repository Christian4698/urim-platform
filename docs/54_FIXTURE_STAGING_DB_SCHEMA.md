# Fixture Staging DB Schema

Phase 35 adds the controlled database schema for future API-Football fixture staging.

This phase is schema-only. It creates no fixture rows, no ingestion runtime, no upsert path, no public endpoint, no
frontend change, no prediction, and no betting/odds path.

## Table
The staging table is:

- `api_football_fixture_staging`

It is intended to receive normalized fixture fields in a later phase after an ingestion gate approves source handling,
temporal availability, idempotence, deduplication, rollback, quota behavior, and security controls.

## Columns
The table follows the Phase 34 prompt field list:

- `id`
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
- `payload_hash`
- `payload_top_level_keys`
- `fetched_at`
- `source_mode`
- `created_at`
- `updated_at`

`payload_top_level_keys` is JSONB structural evidence only. It stores key names, not provider values or provider body
content.

## Constraints and indexes
- `provider` is non-null.
- `provider_fixture_id` is non-null.
- `payload_hash` is non-null.
- `fetched_at` is non-null.
- `source_mode` is non-null.
- `(provider, provider_fixture_id)` is unique.
- `provider_fixture_id` is indexed.
- `fixture_date` is indexed.
- `(provider_league_id, provider_season)` is indexed.
- `fixture_status_short` is indexed.

`payload_hash is non-null` because every future staging row must remain tied to compact, reproducible evidence. This is
a hash only; it is not permission to store provider content.

Optional fixture, team, status, goal and score fields remain nullable so missing provider values stay missing instead of
being converted to invented zeroes or default truth.

## No ingestion yet
Phase 35 does not insert fixtures, perform upserts, run a job, call a runner, schedule ingestion, call API-Football, or
consume provider quota. It only adds DDL plus the SQLAlchemy Core table declaration.

No real API call is authorized in this phase.

## No provider body storage
The staging table intentionally has no provider body column. It also has no field for provider credentials, provider URL,
or local smoke material.

If a later phase needs provider body archival, it must use a separate access-controlled design with license review,
retention rules, redaction, and payload-location references.

## No prediction
No Phase 35 table, field, migration, or model may feed features, backtests, calibration, prediction ledgers, scenario
simulation, user advice, or any model path.

Phase 35 also does not add `available_at`, `source_version`, or `quality_flags`. Phase 36 must define how staging rows
become compliant provider observations before any downstream use.

## No betting/odds
Phase 35 creates no odds snapshot, bookmaker field, stake field, value calculation, betting decision, ticket selection,
or real-money execution path.

## Phase 36 boundary
Phase 36 must be an ingestion gate, not free ingestion. It must prove, before any write path is enabled:

- how local or scheduled ingestion is gated;
- how idempotence and deduplication are enforced;
- how `available_at`, `source_version`, and `quality_flags` are assigned;
- how rollback and quarantine work;
- how provider quotas and retry limits are respected;
- how logs and tests avoid secrets and provider body content;
- how staging rows stay blocked from prediction and betting paths.
