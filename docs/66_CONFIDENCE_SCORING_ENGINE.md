# Confidence Scoring Engine

Phase 47 adds a backend-only, read-only Kairos confidence scoring engine for Phase 46 backtesting foundation reports.

This phase is confidence scoring technique only. It creates a technical signal-quality score from public-safe backtesting
counts. It is not probability, not for betting, and not a guarantee. Scope tags: no official prediction, no prediction
record, no real api call, no db write, no ingestion runtime, no ML, no probability, no betting/odds/stake, and no
ROI/profit/bankroll.

The score measures sample quality, presence of an evaluable sample, historical result coherence through descriptive
coverage, result completeness, and sandbox signal maturity. It does not estimate a team outcome, win chance, market
price, expected value, or financial return.

## Public-Safe Output
The engine returns:

- `provider=api-football`
- `mode=kairos_confidence_scoring_engine`
- `scoring_version`
- `source_mode`
- `read_only=true`
- `db_writes=false`
- `official_prediction_created=false`
- `prediction_record_created=false`
- `betting_created=false`
- `ml_model_used=false`
- `probability_created=false`
- `confidence_score_created`
- `confidence_score_type=technical_signal_quality`
- `confidence_score`
- `confidence_band`
- `not_probability=true`
- `not_for_betting=true`
- `not_a_guarantee=true`
- `sample_quality`
- `score_components`
- aggregate blocking reasons

The output does not echo source inputs, raw provider bodies, team names, provider URLs, credentials, secret material, API
keys, auth material, tokens, odds, bookmaker, stake, prediction records, probabilities, recommended outcomes, suggested
bets, final picks, model output, betting signals, ROI, profit, payout, or bankroll.

## Score Components
The scoring rubric is deterministic and bounded from 0 to 100:

- `sample_presence`: 0 or 25 points
- `match_coverage`: 0 to 25 points
- `evaluable_coverage`: 0 to 25 points
- `result_completeness`: 0 to 15 points
- `descriptive_integrity`: 0 or 10 points

`confidence_score` is set to `0` whenever blocking reasons exist. Otherwise it is the sum of component points, clamped to
the 0-100 range.

Bands are:

- `blocked`: score is `0` or blocking reasons are present
- `low`: 1 to 39
- `medium`: 40 to 69
- `high`: 70 to 100

## Blocking Rules
The score is blocked when:

- `scoring_version` is empty;
- `source_mode` is empty;
- provider is not `api-football`;
- mode is not `kairos_backtesting_foundation_only`;
- `backtest_report_created=false`;
- the backtest is not descriptive;
- the sample is empty;
- `evaluable_count=0`;
- upstream blocking reasons are present;
- official prediction, prediction record, betting, ML, or probability flags are true;
- raw, credential, market, predictive, betting, or financial material is present at any nested key.

Blocked outputs return `confidence_score_created=false`, `confidence_score=0`, and `confidence_band=blocked`.

## Not Probability
This score is not probability. It is not a win probability, result probability, calibrated probability, implied
probability, or probability distribution.

## Not For Betting
This score is not for betting. It is not a betting recommendation, edge estimate, price signal, odds pick, stake input,
ticket selector, value calculation, or real-money action.

## No Official Prediction
Phase 47 creates no official prediction, user-visible forecast, final pick, outcome recommendation, production decision,
or immutable prediction ledger row.

## No Prediction Record
Phase 47 creates no prediction record, no persisted scoring artifact, no ledger entry, no training row, no production
prediction object, and no backtest row.

## No Real API Call
Phase 47 performs no real API call, no API-Football request, no provider transport, no provider authentication, no
provider URL construction, and no quota-consuming action.

## No DB Write
Phase 47 performs no DB write. It creates no insert, update, delete, upsert, session add, transaction commit, migration,
schema change, fixture mutation, feature snapshot persistence, prediction persistence, or ledger row.

## No Ingestion Runtime
Phase 47 does not trigger a runner, start ingestion, backfill fixtures, create staging rows, fetch provider data, or run
an automatic job. It only evaluates a public-safe backtesting foundation report already present in memory.

## No ML
Phase 47 does not train, load, call, select, calibrate, evaluate, or version an ML model. It does not produce a model
output or official model decision.

## No Probability
Phase 47 creates no probability, no implied probability, no win probability, no calibrated probability, and no probability
distribution.

## No Betting/Odds/Stake
No betting/odds/stake path is authorized. Phase 47 creates no odds snapshot, bookmaker field, stake field, value
calculation, ticket selection, betting decision, or real-money action.

## No ROI/Profit/Bankroll
Phase 47 computes no ROI, profit, payout, bankroll, yield, simulated return, drawdown, or financial performance metric.

## Phase 48 Boundary
Phase 48 may add only the dashboard MVP read-only. It must display these outputs as controlled, non-public, non-betting,
non-probability, and non-official unless a later phase explicitly authorizes a stricter release path.
