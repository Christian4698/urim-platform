# API-Football Fixture Read-Only Request Builder

Phase 27 adds a local backend builder for conceptual API-Football `/fixtures` read-only requests.

- `provider=api-football`
- `endpoint=/fixtures`
- `method=GET`
- `read_only=true`
- `db_writes=false`
- `prediction_requested=false`
- `betting_requested=false`
- No real API-Football call is made.
- No quota is consumed.
- No API key or auth header is required.
- No provider response body or raw provider payload is stored.
- No public endpoint is added.

## Why the builder comes before ingestion
The request builder is a safety gate before any ingestion design. It lets Kairos define the exact read-only query
shape that may be prepared locally while the provider remains non-active for automated code paths.

This prevents three risks:

- accepting unknown provider parameters silently;
- confusing a conceptual request with an observed provider payload;
- writing data before provenance, temporal availability and raw hash lineage are designed.

Phase 27 does not create a provider observation storage contract. Any later DB write must still add provider,
provider event identity, observed, fetched and available times, source version, quality flags and raw hash lineage.

## Why /fixtures remains priority
`/fixtures` remains the priority endpoint because it can identify matches, league and season, kickoff timing, teams,
fixture status, goals and score slots without requiring provider predictions, odds, bookmakers or stakes.

The builder only prepares a safe local description of the request. It does not contact the provider, normalize a
fixture, publish a route or activate a scheduler.

## Allowed parameters
Only these Phase 27 query parameters are allowed:

- `league`: positive integer.
- `season`: four digit integer between `1900` and `2100`.
- `team`: positive integer.
- `date`: valid calendar date in `YYYY-MM-DD` format.
- `from`: valid calendar date in `YYYY-MM-DD` format.
- `to`: valid calendar date in `YYYY-MM-DD` format.
- `timezone`: non-empty string after trimming.
- `status`: non-empty string after trimming.

If both `from` and `to` are present, `from` must be earlier than or equal to `to`. Numeric strings are rejected for
integer fields; callers must pass real integers.

## Forbidden parameters and actions
The builder must reject unknown parameters and must reject the following names:

- `odds`
- `bookmaker`
- `stake`
- `prediction`
- `predictions`
- `bet`
- `betting`

Forbidden actions for Phase 27:

- real API-Football calls;
- quota use;
- auth header construction;
- provider URL construction;
- provider response body commits;
- DB ingestion, DB models or Alembic migrations;
- prediction, ML or feature-store activation;
- odds, bookmaker, stake or betting paths;
- public endpoints, frontend changes, schedulers, queues, webhooks or jobs;
- reintroducing `apps/web/lib/integrations`, `_references/public-apis` or `docs/api-catalog.md`.

## Public-safe request object
The builder returns only this public-safe shape:

- `provider`
- `endpoint`
- `method`
- `read_only`
- `query`
- `db_writes`
- `prediction_requested`
- `betting_requested`

The query contains only allowed keys, emitted in this deterministic order: `league`, `season`, `team`, `date`,
`from`, `to`, `timezone`, `status`.

## No real API call
Phase 27 does not perform HTTP, socket, client, transport or script execution against API-Football. The builder is a
pure local validation function and consumes no Free Plan quota.

## No DB write
Phase 27 writes nothing to PostgreSQL, object storage, raw archives, fixture tables or canonical entity tables.

## No prediction
Phase 27 does not create provider predictions, Kairos predictions, model features, backtests, calibration artifacts,
scenario simulations or user advice.

## No betting
Phase 27 does not create odds snapshots, bookmaker fields, stake fields, value calculations, betting decisions or
real-money execution paths.

## Next phase recommendation
The next safe phase should define a read-only fixture response normalizer using static test fixtures only. It should
still avoid real API-Football calls, quota use, provider payload commits, DB ingestion, prediction, odds and betting.
