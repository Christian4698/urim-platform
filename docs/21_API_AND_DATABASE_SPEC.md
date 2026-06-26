# API et base de donnees

## Endpoints
`GET /matches`, `GET /matches/{id}`, `POST /analyses`, `GET /predictions/{id}`, `GET /predictions/{id}/provenance`, `GET /models`, `GET /providers/health`, `GET /calibration`, `GET /agent-messages`, `POST /admin/providers/{id}/disable`.

## Endpoints documentes pour la fondation finale
`GET /providers/capabilities`, `GET /matches/{id}/official-result`, `POST /admin/result-verifications/run`, `GET /data-quality/runs/{id}`, `GET /model-cards/{model_version}`, `GET /data-cards/{dataset_id}`.

## Tables
providers, provider_capabilities, provider_observations, raw_payload_refs, canonical_entities, entity_mappings, fixtures, lineups, availability_events, match_events, statistics, odds_snapshots, data_conflicts, feature_snapshots, model_versions, predictions, prediction_versions, prediction_outcomes, calibration_reports, agent_messages, audit_logs, incidents.

## Tables documentees pour la fondation finale
official_results, official_result_verifications, data_quality_runs, data_quality_violations, model_cards, data_cards, locale_preferences, responsible_betting_events.

Timestamps UTC, contraintes uniques, foreign keys, append-only et index temporels.

## Stack recommandee
- `Next.js + React + TypeScript` pour `URIM Dashboard` et `Bet Center`.
- `FastAPI + Python` pour l'API intelligence et les services `Kairos`.
- `PostgreSQL/Supabase` comme base principale.
- `RLS` pour l'isolation multi-utilisateur.
- `Redis` pour cache, rate limit et files courtes.
- `Celery` pour les taches MVP.
- `TimescaleDB` et `Temporal` restent differes.

## Sources officielles stack
- Next.js : https://nextjs.org/docs
- FastAPI : https://fastapi.tiangolo.com/
- Supabase RLS : https://supabase.com/docs/guides/database/postgres/row-level-security
- Redis rate limiting : https://redis.io/docs/latest/develop/use-cases/rate-limiter/
- Celery : https://docs.celeryq.dev/
- Temporal : https://docs.temporal.io/temporal
- TimescaleDB : https://www.tigerdata.com/docs
- scikit-learn : https://scikit-learn.org/
- MLflow Model Registry : https://mlflow.org/docs/latest/ml/model-registry/
- Great Expectations : https://greatexpectations.io/
- OpenTelemetry : https://opentelemetry.io/docs/
- Sentry : https://docs.sentry.io/
- GitHub Actions : https://docs.github.com/actions
- GitHub Secrets : https://docs.github.com/actions/security-guides/using-secrets-in-github-actions
