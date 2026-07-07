# API-Football Real Smoke Evidence and Safe Response Contract

Phase 25 freezes the public-safe evidence from the first real local API-Football smoke. It is documentation-only
and contract-only. It does not enable provider activation, ingestion, prediction, betting or a public endpoint.

## Public-safe evidence
- `status=completed_first_real_local_smoke`
- `executed=true`
- `provider=api-football`
- `mode=first_real_local_smoke_only`
- `payload_hash=c4dc669eb135caca91c623ce5b30a6aea065ee70134cee45111a576fe19b59ed`
- `payload_top_level_keys=errors,get,paging,parameters,response,results`
- `db_writes=false`
- `prediction_created=false`
- `betting_created=false`

No raw provider payload, provider URL, credential, API key, local reference or sports data row is recorded here.

## Allowed safe response contract
The Phase 25 public-safe contract contains exactly these fields:

- `status`
- `executed`
- `provider`
- `mode`
- `payload_hash`
- `payload_top_level_keys`
- `db_writes`
- `prediction_created`
- `betting_created`

Any value outside this field list is out of scope for Phase 25 evidence sharing.

## What this proves
- A first real local smoke attempt reached a completed public-safe state for `provider=api-football`.
- The smoke result can be summarized without exposing a raw payload, credential, provider URL or local reference.
- The observed provider payload shape can be reduced to a hash and top-level key names only.
- The attempt created no database writes, no prediction and no betting artifact.

## What this does NOT prove yet
- It does not prove provider activation readiness.
- It does not prove coverage, freshness, quota behavior, latency, pagination or license compliance.
- It does not prove canonical mapping, field-level provenance, reconciliation or temporal availability.
- It does not prove DB ingestion, raw payload archival, feature creation, prediction quality, ML readiness or betting readiness.
- It does not prove any endpoint is safe for public runtime use.

## Next allowed read-only endpoints
The next candidates may be investigated only as future read-only provider endpoints, still without DB writes:

- fixtures
- standings
- team statistics
- fixture events
- fixture lineups
- fixture statistics

Phase 25 enables none of these endpoints, creates no route, performs no ingestion and permits no DB writes.

## Forbidden until later phases
- Committing raw provider payloads or reconstructing the provider response body.
- Adding API keys, credentials, local provider references, provider URLs or secret names with values.
- Making real API-Football calls in automated tests.
- Adding DB ingestion, DB models, Alembic migrations or raw payload storage.
- Adding prediction, feature generation, ML, calibration or backtesting activation.
- Adding odds, bookmaker, stake, betting, real-money execution or betting advice.
- Adding public endpoints, schedulers, queues, jobs, webhooks or frontend changes.
- Adding `.env` files or `.env.example` secrets.
- Reintroducing `apps/web/lib/integrations`, `_references/public-apis` or `docs/api-catalog.md`.
