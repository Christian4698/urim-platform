# API-Football Read-Only Endpoint Selection and Fixture Contract

Phase 26 is documentation-only and contract-only.

- `status=documentation_only_read_only_endpoint_selection`
- `provider=api-football`
- No real API-Football call is made.
- No quota is consumed.
- No DB ingestion is enabled.
- No prediction is created.
- No betting, odds, bookmaker or stake path is enabled.
- No public endpoint is added.

## Endpoint selection
Allowed now for documentation and contract planning only:

- `/leagues`: discover competitions, countries, seasons and provider league IDs.
- `/teams`: discover teams and provider team IDs.
- `/fixtures`: priority endpoint for the first safe fixture contract.
- `/standings`: future context for standings enrichment.

Candidates for later phases only:

- `/fixtures/headtohead`: historical context between two teams.
- `/fixtures/statistics`: match statistics after a fixture is selected.
- `/fixtures/events`: match event stream after fixture identity and timing rules are safe.

Forbidden for now:

- `/predictions`: forbidden because provider predictions are not a Kairos truth source and must not feed model
  decisions.
- `/odds`: forbidden because odds can introduce bookmaker, stake, value and betting risk before the odds gate is
  designed.

## Why /fixtures is priority
`/fixtures` is the priority endpoint because it provides match identity, date/time, league/season, teams, status,
goals and score slots without requiring odds or provider predictions. It is the smallest useful read-only shape for
future Kairos fixture discovery, reconciliation and temporal validation.

Phase 26 only documents the fixture shape. It does not execute a request, store a fixture, normalize a fixture or
publish a runtime route.

## Allowed read-only fields
The conceptual safe fixture contract may document only these fields:

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

This fixture contract is not a provider observation storage contract yet. Later ingestion must add full provenance
and temporal fields before any DB write, including observed, fetched and available times, source version, quality
flags and raw hash lineage.

## Forbidden fields/actions
- Raw provider payloads, provider response bodies and reconstructed provider JSON.
- API keys, credentials, local provider references, provider URLs or secret values.
- Real API-Football calls in automated tests.
- Provider predictions, betting suggestions, bookmaker names, odds, stake fields or real-money actions.
- DB ingestion, DB models, Alembic migrations, raw payload storage or canonical fixture writes.
- Runtime API changes, public endpoints, schedulers, queues, webhooks or jobs.
- Frontend changes, `apps/web/lib/integrations`, `_references/public-apis` or `docs/api-catalog.md`.

## No DB ingestion yet
No Phase 26 field may be inserted into PostgreSQL, object storage, a raw payload archive, a fixture table or a
canonical entity table. The fields are documentation-only until a later phase designs provenance, temporal
availability and write gates.

## No prediction yet
No Phase 26 fixture field may feed a model, feature store, backtest, calibration report, scenario simulation,
prediction ledger or user advice. Any future prediction use must first satisfy the temporal rule that data is
available at or before prediction time.

## No betting/odds yet
`/odds` remains forbidden for now. Phase 26 adds no bookmaker, market, odds snapshot, stake, value calculation,
betting decision or real-money execution path.

## Next phase recommendation
The next safe phase should remain read-only and test-only. It may define a fake transport or parser contract for
`/fixtures` using placeholder data only, with no real API-Football request, no provider payload committed, no DB
write, no prediction, no odds and no betting.
