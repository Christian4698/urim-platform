# First Offline Prediction Sandbox

Phase 45 adds a backend-only, read-only first offline prediction sandbox controlled by the Phase 44 Kairos prediction
protocol gate.

This phase is offline sandbox only. It receives one public-safe protocol gate result and one public-safe baseline
analytics result already loaded in memory, then creates a descriptive sandbox hypothesis only when the gate allows it.
Scope tags: no official prediction, no prediction record, no real api call, no db write, no ingestion runtime, no ML, no
confidence scoring, no probability, and no betting/odds/stake.

The sandbox hypothesis is experimental, non-official, not persisted, not public, not a recommendation, and not for
betting. It does not choose an outcome, rank a market, estimate a probability, create a model output, or create an
immutable prediction ledger row.

## Public-safe output
The sandbox returns:

- `provider=api-football`
- `mode=kairos_first_offline_prediction_sandbox`
- `sandbox_version`
- `source_mode`
- `read_only=true`
- `db_writes=false`
- `official_prediction_created=false`
- `prediction_record_created=false`
- `betting_created=false`
- `ml_model_used=false`
- `confidence_score_created=false`
- `probability_created=false`
- `sandbox_hypothesis_created`
- `allowed_by_protocol_gate`
- candidate, accepted, completed-fixture, and scheduled-fixture counts
- `sandbox_hypothesis` only when all blockers are absent
- public-safe sandbox notes
- aggregate blocking reasons

When created, the hypothesis contains only:

- `hypothesis_type=descriptive_offline_sandbox`
- `basis=baseline_analytics_only`
- `sample_state`
- `non_official=true`
- `not_for_betting=true`

The output does not echo source inputs, raw provider bodies, team names, provider URLs, credentials, secret material, API
keys, auth material, tokens, odds, bookmaker, stake, prediction records, probabilities, recommended outcomes, suggested
bets, final picks, model output, confidence scoring payloads, or betting signals.

## Sandbox rules
The sandbox creates a hypothesis only when:

- `sandbox_version` is non-empty;
- `source_mode` is non-empty;
- both inputs have provider `api-football`;
- the protocol gate mode is `kairos_prediction_protocol_gate_only`;
- the baseline mode is `fixture_baseline_analytics_without_official_prediction`;
- the protocol gate has `allowed_for_future_offline_prediction_sandbox=true`;
- no input creation or model flags are true;
- no raw, credential, market, predictive, or betting material is present at any nested key;
- both gate and baseline candidate counts are greater than zero;
- both gate and baseline accepted counts are greater than zero;
- neither input carries upstream blocking reasons.

Invalid inputs return `sandbox_hypothesis_created=false`, `sandbox_hypothesis=null`, and stable aggregate blocking reasons.
The sandbox does not repair, enrich, fetch, persist, or normalize data.

## No official prediction
Phase 45 creates no official prediction, user-visible forecast, final pick, outcome recommendation, production decision,
or immutable prediction ledger row.

## No prediction record
Phase 45 creates no prediction record, no persisted sandbox artifact, no ledger entry, no training row, no backtest row,
and no production publishable prediction object.

## No real API call
Phase 45 performs no real API call, no API-Football request, no provider transport, no provider authentication, no
provider URL construction, and no quota-consuming action.

## No DB write
Phase 45 performs no DB write. It creates no insert, update, delete, upsert, session add, transaction commit, migration,
schema change, fixture mutation, feature snapshot persistence, prediction persistence, or ledger row.

## No ingestion runtime
Phase 45 does not trigger a runner, start ingestion, backfill fixtures, create staging rows, fetch provider data, or run
an automatic job. It only evaluates two public-safe objects already present in memory.

## No ML
Phase 45 does not train, load, call, select, calibrate, evaluate, or version an ML model. It does not produce a model
output or official model decision.

## No confidence scoring
Phase 45 creates no confidence score, certainty label, edge estimate, recommendation, ranked outcome, or buy/sell/win/lose
signal.

## No probability
Phase 45 creates no probability, no implied probability, no win probability, no calibrated probability, and no probability
distribution.

## No betting/odds/stake
No betting/odds/stake path is authorized. Phase 45 creates no odds snapshot, bookmaker field, stake field, value
calculation, ticket selection, betting decision, or real-money action.

## Phase 46 boundary
Phase 46 may add only a backtesting foundation. It must remain offline, controlled, non-public, non-betting, and
non-official unless a later phase explicitly authorizes a stricter release path.
