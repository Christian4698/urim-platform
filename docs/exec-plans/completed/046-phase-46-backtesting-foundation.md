# Phase 46 Backtesting Foundation

## Objective
Add a backend-only read-only backtesting foundation that evaluates non-official Phase 45 sandbox outputs against
completed fixture rows already supplied in memory, without DB writes, official prediction, prediction records,
probabilities, confidence scoring, ML, betting, odds, stake, ROI, profit, provider calls, public endpoints, frontend
changes, or schema changes.

## Completed Scope
- Added an in-memory `build_kairos_backtesting_foundation` function with explicit backtest version and source mode
  metadata.
- Returned public-safe read-only flags, sandbox/fixture/evaluable counts, completed and missing-result counts,
  sample-level matching counts, descriptive outcome distribution, evaluation summary, and aggregate blocking reasons.
- Treated empty sandbox inputs and empty fixture inputs as blocked samples with `sample_is_empty=true`.
- Counted completed fixtures only for `FT`, `AET`, and `PEN` statuses.
- Marked completed fixtures evaluable only when they have a positive fixture ID and numeric fulltime scores or numeric
  goal fallback scores.
- Kept missing result fields separate from valid zero-goal outcomes.
- Reported only `home_win`, `draw`, and `away_win`; no accuracy, probability, confidence score, ROI, profit, payout,
  bankroll, odds, stake, or betting metric is produced.
- Blocked wrong providers, non-Phase-45 sandbox modes, missing sandbox hypotheses, denied protocol gates, empty sandbox
  candidate/accepted counts, upstream sandbox blockers, official prediction flags, prediction record flags, betting
  flags, ML flags, confidence-score flags, probability flags, raw material, credential material, market material,
  predictive material, and financial material.
- Scanned nested input keys without echoing source rows, raw provider material, credentials, odds, bookmaker, stake,
  prediction records, probabilities, recommendations, model output, confidence scoring payloads, betting signals, ROI,
  profit, payout, or bankroll.
- Kept Phase 46 free of DB writes, schema changes, API-Football calls, secrets, quota use, public endpoints, frontend
  changes, ingestion runtime, official prediction, prediction record creation, probability creation, ML, confidence
  scoring, odds, bookmaker, stake, betting, ROI, profit, payout, and bankroll.

## Files
- `apps/api/app/modules/providers/kairos_backtesting_foundation.py`
- `apps/api/tests/test_kairos_backtesting_foundation.py`
- `docs/65_BACKTESTING_FOUNDATION.md`
- `docs/index.md`

## Validation Commands
- `ruff check .`
- `pytest`
- `git diff --check`
- `git status --short --untracked-files=all`

## Risks Tracked
- E001 incomplete sandbox or fixture context.
- E003 malformed providers, modes, fixture IDs, statuses, or score fields.
- E005 future temporal use before true prediction-time snapshots.
- E013 small samples represented without overclaiming.
- E026 forced advice before data sufficiency.
- E029-E031 future leakage in later backtesting, preprocessing, or evaluation.
- E037-E039 market, lineup, or target-match leakage in later phases.
- E041-E047 descriptive result distribution mistaken for predictive or betting value.
- E048 missing segmentation in later backtesting phases.
- E050-E052 post-hoc selection and cherry-picking risks in later phases.
- E067-E069 future ledger immutability and versioning requirements.
- E071 missing scores confused with zero-goal outcomes.
- E072 fixture, league, season, or team ID mapping risks inherited from earlier layers.
- E074 provider secret exposure.
- E075-E077 unsafe certainty language.
- E083-E084 unsafe betting pressure or unclear limits.

## Plan State
The active execution plan was completed and moved to this completed location.
