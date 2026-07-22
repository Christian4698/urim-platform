# Dashboard MVP Read-Only

Phase 48 adds a backend-only Kairos dashboard payload builder. This is dashboard read-only only: it aggregates already
computed Phase 41 through Phase 47 public-safe outputs in memory and returns controlled cards for readiness, counts,
blocking state, technical confidence band, and safety flags.

Scope tags: no real api call, no DB write, no ingestion runtime, no official prediction, no prediction record, no ML,
confidence score is technical only, no probability, no betting/odds/stake, and no ROI/profit/bankroll.

## Public-Safe Output
The dashboard returns:

- `provider=api-football`
- `mode=kairos_dashboard_mvp_read_only`
- `dashboard_version`
- `source_mode`
- `read_only=true`
- `db_writes=false`
- `api_football_call_created=false`
- `ingestion_created=false`
- `official_prediction_created=false`
- `prediction_record_created=false`
- `betting_created=false`
- `ml_model_used=false`
- `probability_created=false`
- `dashboard_ready`
- `cards`
- `summary`
- aggregate blocking reasons

Cards are intentionally small and do not echo raw source objects. They expose only presence, status, provider, mode,
read-only state, write state, safe counters, readiness booleans, and the technical confidence score fields already
created by Phase 47.

## Cards
The MVP payload includes seven cards:

- `data_freshness`
- `feature_snapshots`
- `baseline_analytics`
- `protocol_gate`
- `offline_sandbox`
- `backtesting`
- `confidence_scoring`

`dashboard_ready=true` requires all cards to be present, provider `api-football`, expected mode, no upstream blocking
reasons, no unsafe created flags, no unsafe nested keys, and the card-specific readiness flags required by the previous
phases.

If cards are missing but no unsafe material is present, `overall_status=partial`. If metadata is empty, provider is
wrong, upstream blockers exist, unsafe flags are true, or forbidden material is present, `overall_status=blocked`.

## Blocking Rules
The dashboard blocks when:

- `dashboard_version` is empty;
- `source_mode` is empty;
- an input provider is not `api-football`;
- an input mode does not match the expected upstream phase output;
- upstream blocking reasons are present;
- official prediction, prediction record, betting, ML, or probability flags are true;
- raw, credential, market, predictive, betting, or financial material is present at any nested key;
- a card-specific readiness requirement is false or missing.

## No Real API Call
Phase 48 performs no real API call, no API-Football request, no provider transport, no provider authentication, no
provider URL construction, and no quota-consuming action.

## No DB Write
Phase 48 performs no DB write. It creates no insert, update, delete, upsert, session add, transaction commit, migration,
schema change, fixture mutation, feature snapshot persistence, prediction persistence, dashboard persistence, or ledger
row.

## No Ingestion Runtime
Phase 48 does not start ingestion, create staging rows, backfill fixtures, run a background job, enqueue a task, fetch
provider data, or refresh upstream tables. It only formats already available safe summaries passed in memory.

## No Official Prediction
Phase 48 creates no official prediction, user-visible forecast, final pick, outcome recommendation, production decision,
or immutable prediction ledger row.

## No Prediction Record
Phase 48 creates no prediction record, persisted forecast artifact, model decision row, training row, scoring row,
backtest row, or official ledger event.

## No ML
Phase 48 does not train, load, call, select, evaluate, calibrate, or version an ML model. It only displays the Phase 47
technical signal-quality score when that score is already present and safe.

## Confidence Score Is Technical Only
The displayed `confidence_score` is technical only. It describes signal quality, sample sufficiency, and readiness of
the internal pipeline. It is not a team outcome estimate, market signal, edge estimate, or user-facing prediction.

## No Probability
Phase 48 creates no probability, no implied probability, no win probability, no calibrated probability, and no probability
distribution. `not_probability=true` remains part of the summary contract.

## No Betting/Odds/Stake
No betting/odds/stake path is authorized. Phase 48 creates no betting advice, odds snapshot, bookmaker field, stake
field, ticket selector, price comparison, value calculation, or real-money action.

## No ROI/Profit/Bankroll
Phase 48 computes no ROI, profit, payout, bankroll, yield, simulated return, drawdown, or financial performance metric.

## Frontend Boundary
This phase creates the dashboard payload backend only. The existing frontend was not modified because a controlled
read-only API surface for this new payload is not part of Phase 48. A later phase can expose a UI only after route,
auth, monitoring, and logging boundaries are explicitly defined.

## Public System Availability Increment
The frontend now consumes only the existing public-safe `GET /health` and `GET /readiness` system endpoints through a
typed client. It does not consume the Phase 48 provider dashboard payload, call a sports provider, create a prediction,
enable ML, connect a bookmaker, or execute betting. Loading, timeout, invalid-response, network-error, API-online, and
database-availability states are explicit. Only the public backend origin is exposed to the browser.

## Phase 49 Boundary
Phase 49 will add monitoring, quotas and safe logs before any broader dashboard exposure. It must preserve read-only
behavior, avoid provider calls from UI code, and keep all secret, betting, probability, and prediction boundaries intact.
