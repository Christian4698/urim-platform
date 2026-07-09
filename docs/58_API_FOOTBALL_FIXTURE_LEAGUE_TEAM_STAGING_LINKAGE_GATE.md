# API-Football Fixture/League/Team Staging Linkage Gate

Phase 39 adds a backend-only linkage gate between normalized API-Football fixtures, leagues, and teams.

This phase is dry-run/in-memory only. It checks whether fixture references can be matched to normalized league and team
IDs before a future staging ingestion phase, but it does not persist or expose the linked rows.

## Public-safe output
The gate returns only:

- `provider=api-football`
- `mode=fixture_league_team_staging_linkage_gate_only`
- `target_table=api_football_fixture_staging`
- fixed safety flags: `db_writes=false`, `prediction_created=false`, `betting_created=false`
- `source_mode`
- fixture, league, and team counts
- linked and unlinked fixture counts
- missing league, home-team, and away-team reference counts
- duplicate league and team provider IDs
- readiness and blocking reasons

It does not return raw provider content, complete fixture lists, team names, league names, provider URLs, credentials, or
secret material.

## Linkage rules
A fixture is linked only when:

- the fixture provider is exactly `api-football`;
- `provider_league_id` is present and resolves to one normalized league `provider_league_id`;
- `home_team_provider_id` is present and resolves to one normalized team `provider_team_id`;
- `away_team_provider_id` is present and resolves to one normalized team `provider_team_id`;
- the fixture itself does not contain odds, bookmaker, stake, prediction, or betting fields.

League IDs and team IDs are indexed in memory for this dry run only. Duplicate `provider_league_id` values are detected
by ID alone, even when the duplicate rows represent different seasons. Duplicate `provider_team_id` values are also
detected. Duplicate IDs block readiness because Phase 39 must not resolve ambiguous provider identity silently.

Missing-reference counters count absent, invalid, or unknown fixture references. IDs that exist but are duplicated are
reported through duplicate-ID blocking reasons rather than missing-reference counters.

## Blocking rules
The gate blocks future staging linkage readiness when:

- there are no fixtures;
- `source_mode` is blank;
- any fixture provider differs from `api-football`;
- a fixture has a missing league, home-team, or away-team reference;
- duplicate league or team provider IDs exist;
- any fixture, league, or team row contains odds, bookmaker, stake, prediction, or betting fields.

The gate is intentionally a readiness check. It does not perform canonical entity resolution, field-level provenance,
temporal availability assignment, rollback, quarantine, or idempotent writes.

## No DB write
Phase 39 performs no DB write. It creates no SQLAlchemy model, no SQL statement, no migration, no session operation, no
upsert path, no scheduled job, no ingestion runtime, and no staging row.

The Phase 35 `api_football_fixture_staging` table remains untouched.

## No real API call
Phase 39 performs no real API call, no API-Football request, no provider authentication, no provider URL construction,
and no quota-consuming action. Tests use fake in-memory normalized dictionaries only.

## No prediction
No Phase 39 output can feed features, backtests, calibration, model training, prediction ledgers, scenario simulation,
or user advice. `prediction_created=false` is only a safety flag.

## No betting/odds
No betting/odds path is authorized. Phase 39 rejects odds, bookmaker, stake, prediction, and betting fields and creates
no odds snapshot, value calculation, stake, ticket, bookmaker interaction, or real-money action.

## Phase 40 boundary
Phase 40 may add only a read-only internal API over this dry-run linkage evidence. It must not add free ingestion,
public endpoints, DB writes, provider calls, prediction, betting, odds, bookmaker, stake, ML, jobs, or frontend changes.

Before any future write path is authorized, the project must still define provenance contracts, `available_at`,
`source_version`, `quality_flags`, idempotence, deduplication, rollback, quota controls, and security review.
