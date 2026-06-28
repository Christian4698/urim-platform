# API et base de donnees

## Endpoints
`GET /matches`, `GET /matches/{id}`, `POST /analyses`, `GET /predictions/{id}`, `GET /predictions/{id}/provenance`, `GET /models`, `GET /providers/health`, `GET /calibration`, `GET /agent-messages`, `POST /admin/providers/{id}/disable`.

## Tables
providers, provider_capabilities, provider_observations, raw_payload_refs, canonical_entities, entity_mappings, fixtures, lineups, availability_events, match_events, statistics, odds_snapshots, data_conflicts, feature_snapshots, model_versions, predictions, prediction_versions, prediction_outcomes, calibration_reports, agent_messages, audit_logs, incidents.

Timestamps UTC, contraintes uniques, foreign keys, append-only et index temporels.

## Phase 3 API Foundation
Les endpoints Phase 3 sont limites a une fondation FastAPI versionnee, des statuts systeme et des collections skeleton read-only. Ils ne creent pas de predictions, ne connectent pas de fournisseur, n'exposent aucun bookmaker et n'executent aucune mise reelle.

## Phase 4 API/Security Hardening
La Phase 4 conserve les endpoints skeleton read-only et ajoute uniquement du hardening API/securite.

Les headers de securite publics incluent une CSP API-first restrictive : `default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`. Cette politique peut limiter le rendu des docs interactives; aucun portail docs, auth complete, RBAC complet, session, cookie ou changement CORS n'est ajoute en Phase 4.

`/version` et `/api/v1/system/capabilities` exposent des overrides de securite de phase : `live_enabled=false` et `real_betting_enabled=false` meme si une configuration locale est modifiee. Providers, API-Football, bookmakers, ML, prediction creation, production mocks et production seeds restent desactives.

## Phase 5 API Runtime Cleanup
La Phase 5 conserve les endpoints skeleton read-only et stabilise les statuts runtime publics : `read_only_skeleton`, `virtual_internal`, `disabled` et `not_required`.

La CSP reste stricte et API-first : `default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`. Swagger UI ou ReDoc peuvent ne pas se rendre interactifs sous cette politique; aucun portail docs, auth complete, RBAC complet, session, cookie ou changement CORS n'est ajoute en Phase 5.

`/version`, `/readiness` et `/api/v1/system/capabilities` restent coherents : live, real betting, providers, API-Football, bookmakers, ML, prediction creation, production mocks et production seeds sont desactives.

## Post-Match Learning
Le futur Post-Match Learning ne peut apprendre que depuis des resultats officiels verifies dans `post_match_outcomes`.

Les champs `tickets.user_declared_result` et `tickets.user_declared_profit_loss` servent uniquement a l'experience utilisateur du Bet Center virtuel/interne. Ils ne sont jamais une source d'apprentissage, d'evaluation modele, de calibration, de backtest ou de resultat officiel.
