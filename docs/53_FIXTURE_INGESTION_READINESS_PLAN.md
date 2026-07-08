# Fixture Ingestion Readiness Plan

Phase 34 is a documentation and contract phase for a future fixture staging ingestion. It prepares the rules that must
exist before any database work is allowed.

## No DB write
Phase 34 authorizes no DB write. The compact `/fixtures` smoke proved that a local read can produce public-safe evidence,
but it did not prove staging storage readiness, provenance completeness, temporal availability, reconciliation,
monitoring, or rollback safety.

This phase also means no Alembic migration, no SQLAlchemy model, no public endpoint, no frontend, no real API call, no
prediction, and no betting/odds.

## Why ingestion is still blocked
Future staging ingestion must not start until these gaps are closed:

- provider license and redistribution limits are reviewed for stored fixture rows;
- quota and rate-limit behavior are documented for repeatable staging runs;
- `fetched_at`, `available_at`, `source_version`, `quality_flags`, and `raw_hash` lineage are defined;
- data freshness thresholds exist for scheduled, postponed, cancelled, and live fixtures;
- entity reconciliation rules exist for teams, leagues, seasons, and fixture identity;
- rollback and disablement steps are documented and tested;
- logs and test output are proven to redact credentials and provider details.

## Candidate staging fields
These fields are candidates for a future staging table only. Phase 34 does not create the table.

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
- `fetched_at`
- `source_mode`

These candidates come from the Phase 28 normalizer shape plus the Phase 32 compact evidence. Missing provider values must
stay `NULL` or explicit missing markers in a future design, never invented zeroes.

## Identity, idempotence and deduplication
`provider_fixture_id` is the provider fixture identity inside the API-Football source namespace. A future staging design
must treat the logical identity as at least `(provider, provider_fixture_id, source_mode)` and document whether
`provider_league_id`, `provider_season`, or `fixture_date` are supporting checks rather than identity keys.

Idempotence must be based on deterministic inputs. Re-running the same staging candidate with the same
`provider_fixture_id`, `payload_hash`, and `source_mode` must not create duplicate active rows.

Deduplication must separate exact duplicates from changed observations. Exact duplicates can be collapsed or ignored;
changed observations must be append-only or versioned so status changes, reschedules, score updates, and corrections are
auditable.

## Payload hash strategy
`payload_hash` must be deterministic for the provider response shape used to derive the row. It is evidence for
reproducibility, not permission to store or expose provider content.

`payload_top_level_keys` may be kept as compact structural evidence. It must not include provider values.

## Source/provider audit trail
A future staging row needs an audit trail that can answer:

- which provider produced the observation;
- which endpoint and source mode produced it;
- when it was fetched;
- when it was considered available for downstream use;
- which source version and quality flags applied;
- which hash proves the observed provider shape.

Corrections must be append-only. No future process may rewrite a published prediction or claim a changed fixture was
known before its `available_at` time.

## Freshness and fixture status risk
Freshness rules must distinguish scheduled, postponed, cancelled, and live states. Live and incomplete fixtures are high
risk because scores, status text, and timing can change quickly. Postponed or cancelled matches can keep the same
provider fixture identity while their date, status, or availability changes.

Future staging must define freshness windows, stale-data behavior, and quality flags before any row can feed a canonical
fixture process. Until then, stale or ambiguous rows must stay blocked from prediction and user advice.

## No raw payload by default
The future default is no raw payload storage in staging. If a later phase needs raw provider archival, it must design a
separate access-controlled location, retention policy, license review, redaction policy, and payload-location reference.

Phase 34 commits no provider body, reconstructed provider JSON, complete fixture list, fixture IDs from the real smoke,
team names from the real smoke, or score rows from the real smoke.

## Rollback strategy
Future staging must have a rollback plan before DB work starts:

- disable the ingestion flag without code changes;
- stop scheduled runs and manual runners independently;
- quarantine newly written staging rows by run or source mode;
- preserve audit rows needed to explain what happened;
- verify no prediction, feature, odds, or betting path consumed the quarantined data.

## Quota and operational risk
Future ingestion must not rely on manual smoke assumptions. It needs documented Free Plan quota limits, rate-limit
behavior, retry policy, backoff, alerting, and a dry-run mode before staging writes are permitted.

No automated test may call API-Football. No future readiness test may consume provider quota.

## Non-prediction, non-betting and non-odds rules
No prediction can consume Phase 34 material. A future Phase 35 staging design must still keep fixture staging separate
from features, backtests, calibration, prediction ledgers, scenario simulation, and user advice.

No betting/odds path is authorized. Phase 34 creates no odds snapshot, bookmaker field, stake field, value calculation,
betting decision, or real-money execution path.

## Future Phase 35 authorization criteria
Future Phase 35 may request staging DB work only after these criteria are documented and testable:

- staging schema proposal with no raw provider content by default;
- Alembic migration plan reviewed but not retroactive;
- SQLAlchemy model plan reviewed but isolated from canonical fixtures;
- idempotence and deduplication tests designed;
- `payload_hash`, `provider_fixture_id`, `fetched_at`, `available_at`, `source_version`, and `quality_flags` rules set;
- rollback and quarantine procedure approved;
- quota, rate-limit, retry, and monitoring plan approved;
- security review confirms no real key, provider URL, or provider body is committed;
- temporal review confirms future rows cannot feed predictions before `available_at`;
- explicit approval that Phase 35 remains staging-only unless a later gate authorizes canonical ingestion.
