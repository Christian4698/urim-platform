# API et base de données

## Endpoints
`GET /matches`, `GET /matches/{id}`, `POST /analyses`, `GET /predictions/{id}`, `GET /predictions/{id}/provenance`, `GET /models`, `GET /providers/health`, `GET /calibration`, `GET /agent-messages`, `POST /admin/providers/{id}/disable`.

## Tables
providers, provider_capabilities, provider_observations, raw_payload_refs, canonical_entities, entity_mappings, fixtures, lineups, availability_events, match_events, statistics, odds_snapshots, data_conflicts, feature_snapshots, model_versions, predictions, prediction_versions, prediction_outcomes, calibration_reports, agent_messages, audit_logs, incidents.

Timestamps UTC, contraintes uniques, foreign keys, append-only et index temporels.

## Phase 3 API foundation
Les endpoints Phase 3 sont limites a une fondation FastAPI versionnee, des statuts systeme et des collections skeleton read-only. Ils ne creent pas de predictions, ne connectent pas de fournisseur, n'exposent aucun bookmaker et n'executent aucune mise reelle.

## Post-Match Learning
Le futur Post-Match Learning ne peut apprendre que depuis des resultats officiels verifies dans `post_match_outcomes`.

Les champs `tickets.user_declared_result` et `tickets.user_declared_profit_loss` servent uniquement a l'experience utilisateur du Bet Center virtuel/interne. Ils ne sont jamais une source d'apprentissage, d'evaluation modele, de calibration, de backtest ou de resultat officiel.
