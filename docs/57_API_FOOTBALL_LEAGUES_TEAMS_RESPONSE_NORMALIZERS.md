# API-Football Leagues/Teams Response Normalizers

Phase 38 adds local-only response normalizers for fake/test-only API-Football `/leagues` and `/teams` payloads.

This phase is read-only normalizer only. It transforms in-memory test payloads into compact public-safe structures for
future fixture, league and team staging linkage work.

## Public-safe output
Each normalizer returns:

- `provider=api-football`
- `endpoint=/leagues` or `endpoint=/teams`
- a Phase 38 normalizer-only mode
- `payload_hash`
- `payload_top_level_keys`
- `normalized_count`
- compact normalized rows
- `db_writes=false`
- `prediction_created=false`
- `betting_created=false`

The output never returns provider bodies, media fields, URLs, credentials, or complete provider payloads.

## Leagues normalization
The `/leagues` normalizer emits one row per league and season pair.

Allowed normalized fields are:

- `provider`
- `provider_league_id`
- `league_name`
- `league_type`
- `country_name`
- `country_code`
- `season`
- `season_start`
- `season_end`
- `season_current`

If a league item has no usable seasons list, Phase 38 emits one row with league and country identity while season fields
remain `NULL`-like `None`. Missing provider values stay missing; the normalizer does not invent zeroes or defaults.

League logos, country flags, coverage blocks, images, URLs and other provider-only fields are ignored.

## Teams normalization
The `/teams` normalizer emits one row per team item.

Allowed normalized fields are:

- `provider`
- `provider_team_id`
- `team_name`
- `team_code`
- `team_country`
- `team_founded`
- `team_national`
- `venue_provider_id`
- `venue_name`
- `venue_city`
- `venue_capacity`

Venue fields are nullable when absent. Team logos, venue images, URLs and other provider-only fields are ignored.

## Payload evidence
`payload_hash` is stable compact evidence for reproducibility. It is not permission to store or publish provider body
content.

`payload_top_level_keys` contains only sorted top-level key names. It must not contain provider values.

## No real API call
Phase 38 makes no real API call. It adds no HTTP transport, provider client, socket use, runner, script execution,
provider URL construction, auth header construction, API key use, or Free Plan quota consumption.

## No DB write
Phase 38 makes no DB write. It adds no SQLAlchemy model, no Alembic migration, no SQL statement, no session operation,
no staging write, no canonical entity write, no scheduler, and no job.

## No ingestion
Phase 38 adds no ingestion. It does not persist leagues, teams, fixtures, venue rows, provider bodies, media references,
or staging linkage.

## No prediction
No Phase 38 output may feed features, backtests, calibration, model training, prediction ledgers, scenario simulation,
or user advice.

## No betting/odds
No betting/odds path is authorized. Phase 38 creates no odds snapshot, bookmaker field, stake field, value calculation,
betting decision, or real-money action.

## Phase 39 boundary
Phase 39 may plan fixtures + leagues + teams staging linkage. It must still define provenance, temporal availability,
idempotence, deduplication, rollback, quota controls and security review before any write path can be authorized.
