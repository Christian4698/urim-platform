# API-Football Fixture Read-Only Transport Harness

Phase 29 adds a backend-only harness for API-Football `/fixtures` using a fake/test-only injected transport.

- `provider=api-football`
- `endpoint=/fixtures`
- `method=GET`
- `read_only=true`
- `transport_used=injected_test_transport`
- `db_writes=false`
- `prediction_created=false`
- `betting_created=false`
- No real API-Football call is made.
- No quota is consumed.
- No provider secret or auth header is required.
- No provider response body is returned.
- No public endpoint is added.

## Why add a harness before a real /fixtures call
The harness proves the local control flow before any controlled real smoke is considered. It verifies that Kairos can
build a safe fixture request, pass only a public-safe request summary into an injected transport and normalize the
fake/test-only response without opening DB, prediction, odds or betting paths.

This phase does not activate API-Football as a live source. It is a local integration harness for code contracts only.

## How the pieces connect
The harness connects three Phase 27 and Phase 28 pieces:

- the fixture request builder validates the query and emits endpoint, method, read-only flags and safe query fields;
- the injected test transport receives that safe request summary and returns a fake/test-only in-memory payload;
- the fixture response normalizer extracts only the allowed fixture fields and returns a public-safe normalized result.

The harness returns `request_query`, `transport_used`, `executed`, `normalized_count`, `fixtures`, `payload_hash` and
`payload_top_level_keys` without returning provider response content.

## Fake/test-only payloads
Payloads used by Phase 29 are owned by tests. They are not provider evidence, not production fallbacks, not stored
fixtures and not quota-backed observations.

## No real API call
Phase 29 does not construct a provider URL, HTTP client, socket call, script runner or request header. The only
transport allowed in this phase is injected by the caller and used in tests.

## No quota
Because the transport is fake/test-only, Phase 29 consumes no Free Plan quota and performs no provider-side action.

## No DB ingestion
No Phase 29 output may be inserted into PostgreSQL, object storage, provider observation tables, fixture tables or
canonical entity tables. The harness remains read-only.

## No prediction
No Phase 29 field may feed a model, feature store, backtest, calibration report, prediction ledger, scenario
simulation or user advice.

## No betting/odds
Phase 29 adds no odds snapshots, bookmaker fields, stake fields, value calculations, betting decisions or real-money
execution path.

## Error handling
If the injected fake transport raises an error, the harness raises a generic harness error and does not expose provider
response content. Query validation errors still come from the builder before any transport call.

## Next phase recommendation
The next safe phase should be a fixture local-only real smoke protocol limited to one controlled call. It must keep the
same no-DB, no-prediction, no-odds and no-betting gates and must not commit provider response content.
