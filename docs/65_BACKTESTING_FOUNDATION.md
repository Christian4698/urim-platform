# Backtesting Foundation

Phase 46 adds a backend-only, read-only Kairos backtesting foundation for non-official Phase 45 sandbox outputs and
completed fixture rows already supplied in memory.

This phase is backtesting foundation only. It creates a descriptive backtest report only when sandbox outputs and
completed fixture rows are present, clean, and evaluable. Scope tags: no official prediction, no prediction record, no
real api call, no db write, no ingestion runtime, no ML, no confidence scoring, no probability, no betting/odds/stake,
and no ROI/profit/bankroll.

The report is descriptive. It counts whether historical fixture rows are completed and evaluable, then reports only the
observed result distribution: `home_win`, `draw`, and `away_win`. It does not score a model, rank an outcome, estimate a
probability, compute financial metrics, or publish a prediction.

## Public-safe output
The foundation returns:

- `provider=api-football`
- `mode=kairos_backtesting_foundation_only`
- `backtest_version`
- `source_mode`
- `read_only=true`
- `db_writes=false`
- `official_prediction_created=false`
- `prediction_record_created=false`
- `betting_created=false`
- `ml_model_used=false`
- `confidence_score_created=false`
- `probability_created=false`
- `backtest_report_created`
- sandbox, fixture, matched, unmatched, evaluable, non-evaluable, completed, and missing-result counts
- `outcome_distribution` with only `home_win`, `draw`, and `away_win`
- `evaluation_summary`
- aggregate blocking reasons

The output does not echo source inputs, raw provider bodies, team names, provider URLs, credentials, secret material, API
keys, auth material, tokens, odds, bookmaker, stake, prediction records, probabilities, recommended outcomes, suggested
bets, final picks, model output, confidence scoring payloads, betting signals, ROI, profit, payout, or bankroll.

## Input Contract
Sandbox outputs may contribute only when they are Phase 45 offline sandbox outputs and remain non-official,
non-persisted, non-probabilistic, non-ML, non-confidence-scored, and non-betting.

Completed fixture rows may contribute only public-safe fixture result fields. A fixture is considered completed when
`fixture_status_short` is one of `FT`, `AET`, or `PEN`.

A completed fixture row is evaluable only when it has:

- provider `api-football`;
- a positive integer-like `provider_fixture_id`;
- fulltime scores from `score_fulltime_home` and `score_fulltime_away`, or fallback scores from `goals_home` and
  `goals_away`.

Missing scores remain separate from zero-goal outcomes. A `0-0` result is evaluable; absent score fields are not.

## Matching Rule
Phase 45 sandbox outputs are aggregate hypotheses and do not carry per-fixture IDs. Phase 46 therefore performs
sample-level matching only: when at least one clean sandbox output and at least one evaluable completed fixture row are
present, the evaluable fixture rows form the matched historical sample. It does not create event-level prediction/result
pairs.

Empty sandbox inputs and empty fixture inputs are blocked. They return `backtest_report_created=false` and
`evaluation_summary.sample_is_empty=true`.

## No Official Prediction
Phase 46 creates no official prediction, user-visible forecast, final pick, outcome recommendation, production decision,
or immutable prediction ledger row.

## No Prediction Record
Phase 46 creates no prediction record, no persisted sandbox artifact, no ledger entry, no training row, no production
prediction object, and no backtest row.

## No Real API Call
Phase 46 performs no real API call, no API-Football request, no provider transport, no provider authentication, no
provider URL construction, and no quota-consuming action.

## No DB Write
Phase 46 performs no DB write. It creates no insert, update, delete, upsert, session add, transaction commit, migration,
schema change, fixture mutation, feature snapshot persistence, prediction persistence, or ledger row.

## No Ingestion Runtime
Phase 46 does not trigger a runner, start ingestion, backfill fixtures, create staging rows, fetch provider data, or run
an automatic job. It only evaluates public-safe objects already present in memory.

## No ML
Phase 46 does not train, load, call, select, calibrate, evaluate, or version an ML model. It does not produce a model
output or official model decision.

## No Confidence Scoring
Phase 46 creates no confidence score, certainty label, edge estimate, recommendation, ranked outcome, or buy/sell/win/lose
signal.

## No Probability
Phase 46 creates no probability, no implied probability, no win probability, no calibrated probability, and no probability
distribution.

## No Betting/Odds/Stake
No betting/odds/stake path is authorized. Phase 46 creates no odds snapshot, bookmaker field, stake field, value
calculation, ticket selection, betting decision, or real-money action.

## No ROI/Profit/Bankroll
Phase 46 computes no ROI, profit, payout, bankroll, yield, simulated return, drawdown, or financial performance metric.

## Phase 47 Boundary
Phase 47 may add only a controlled confidence scoring engine, separate from betting. It must remain gated, non-public,
non-betting, and non-official unless a later phase explicitly authorizes a stricter release path.
