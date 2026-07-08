# API-Football Fixture Real Smoke Evidence And Compact Output

Phase 32 freezes the public-safe evidence from the first real local API-Football `/fixtures` smoke and tightens the
script output contract to compact evidence only.

## Public-safe evidence
- `status=completed_fixture_first_real_local_smoke`
- `executed=true`
- `provider=api-football`
- `endpoint=/fixtures`
- `mode=fixture_first_real_local_smoke_only`
- `request_query.date=2026-07-07`
- `request_query.timezone=Africa/Kinshasa`
- `normalized_count=108`
- `payload_hash=a2ee84bc090fcbf0dd09ec9ab007d0c267fb95246f58390b382dc70900505c3a`
- `payload_top_level_keys=errors,get,paging,parameters,response,results`
- `db_writes=false`
- `prediction_created=false`
- `betting_created=false`

No raw provider payload, provider URL, API key, full match list, individual fixture ID, team name or score row is
recorded here.

## Compact output contract
The Phase 31 script public-safe success output may contain only:

- `provider`
- `endpoint`
- `mode`
- `executed`
- `status`
- `request_query`
- `normalized_count`
- `payload_hash`
- `payload_top_level_keys`
- `db_writes`
- `prediction_created`
- `betting_created`

The script may still normalize the provider response internally, but it must not expose the normalized fixture list.

## What this proves
- One local controlled `/fixtures` smoke completed successfully.
- The smoke result can be reduced to a query, a normalized count, a payload hash and top-level keys.
- The result created no database writes, no prediction and no betting artifact.

## What this does NOT prove yet
- It does not prove provider activation readiness.
- It does not prove coverage, pagination, quota behavior, latency or license readiness.
- It does not prove canonical fixture ingestion, entity reconciliation, field-level provenance or temporal availability.
- It does not prove prediction, ML, odds, bookmaker, stake or betting readiness.
- It does not create a public runtime endpoint.

## Forbidden material
- Raw provider payloads, provider response bodies or reconstructed provider JSON.
- API keys, credentials, local provider references or provider URLs.
- Full fixture lists, individual fixture IDs, team names, countries, leagues or score rows.
- DB ingestion, DB models, Alembic migrations or raw payload storage.
- Prediction, feature generation, ML, calibration or backtesting activation.
- Odds, bookmaker, stake, betting, real-money execution or betting advice.
- Public endpoints, schedulers, queues, jobs, webhooks or frontend changes.
- Reintroducing `apps/web/lib/integrations`, `_references/public-apis` or `docs/api-catalog.md`.
