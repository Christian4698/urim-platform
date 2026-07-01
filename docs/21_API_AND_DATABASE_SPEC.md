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

## Phase 6 Provider Readiness Contracts
La Phase 6 ajoute uniquement des contrats provider et un endpoint read-only `/api/v1/providers/readiness`.

Cet endpoint n'appelle aucun provider, ne charge aucune cle API, ne connecte pas API-Football et ne cree aucune prediction. Il expose les exigences de provenance, la matrice de capacites futures toutes desactivees, la regle temporelle `observed_at <= available_at <= fetched_at`, la future contrainte `available_at <= prediction_time` et l'interdiction de fallback mock en production.

Les observations provider futures doivent conserver `provider`, `provider_event_id`, `observed_at`, `available_at`, `fetched_at`, `source_version`, `raw_hash` et `quality_flags`. Les mappings canoniques restent audites et ne doivent pas ecraser silencieusement une observation divergente.

## Phase 7 Provider QA Contract Hardening
La Phase 7 conserve `/api/v1/providers/readiness` en lecture seule et ajoute uniquement des exigences QA provider.

L'endpoint expose les exigences `license_review_required`, `quota_and_rate_limit_required`, `golden_payloads_required`, `payload_redaction_required`, `monitoring_required`, `independent_audit_required` et `no_production_mock_fallback`.

Les golden payloads sont autorises seulement en tests/docs avec marqueurs `DEMO_NON_PROD` ou `PLACEHOLDER`. Ils ne doivent contenir aucun resultat sportif reel, aucune cle fournisseur et aucun credential.

Les payloads provider doivent passer par une redaction recursive avant exposition, log ou rapport QA. Les cles sensibles comme `api_key`, `token`, `authorization`, `secret`, `password`, `bearer`, `credential` et `provider_credentials` sont masquees.

## Phase 8 Provider Sandbox Adapter
La Phase 8 ajoute un adaptateur sandbox interne et un endpoint read-only `/api/v1/providers/sandbox/status`.

Cet adaptateur lit uniquement des payloads en memoire marques `DEMO_NON_PROD` et `PLACEHOLDER`. Il ne connecte pas API-Football, n'appelle pas Internet, n'utilise aucune cle API, n'expose aucun credential, n'ingere rien en base et ne cree aucune prediction.

Le mapping sandbox produit seulement des contrats provider : `RawPayloadReference`, `ProviderObservation`, metadata temporelle, rapport qualite et enveloppe officielle placeholder sans resultat sportif. Les `raw_hash` sont stables et calcules depuis le JSON canonique du payload sandbox.

`POST /api/v1/providers/sandbox/status` reste absent et doit retourner `405`.

## Phase 9 Provider Sandbox Integration QA
La Phase 9 conserve les endpoints read-only `/api/v1/providers/readiness` et `/api/v1/providers/sandbox/status`, puis renforce leur valeur d'audit avant tout provider reel.

Le statut sandbox expose le flux QA `identity -> payloads -> raw_reference -> observation -> quality_report -> canonical_mapping_placeholder -> official_result_envelope_placeholder`. Ce flux reste non-production, sans appel reseau, sans credential, sans ecriture base, sans ingestion canonique et sans creation de prediction.

`official_result_envelope` reste une extension sandbox placeholder uniquement. Il n'entre pas dans le protocole provider general et ne remplace pas le futur Official Result Verifier. Post-Match Learning reste inactif et ne pourra apprendre que depuis des `post_match_outcomes` officiels verifies dans une phase future.

La readiness provider expose aussi les prerequis avant activation reelle : licence, quota, rate limit, latence, pagination, retries, circuit breaker, redaction, monitoring, reconciliation, golden payloads reels anonymises et audit securite. Ces elements sont des contrats readiness-only : aucun scheduler, queue, retry execution, circuit breaker execution ou provider network call n'est ajoute en Phase 9.

## Phase 10 Provider Onboarding Gate
La Phase 10 ajoute un gate d'activation provider dans `/api/v1/providers/readiness`.

Le gate retourne `blocked_until_real_provider_audit`, `can_activate=false` et `providers_enabled=false`. Il liste les raisons de blocage tant que licence, quotas, rate limits, latence, pagination, retries/circuit breaker, redaction, monitoring, reconciliation, golden payloads reels anonymises, audit securite et gestion secrete des credentials ne sont pas valides.

Les exigences QA restent separees des exigences onboarding : QA verifie les payloads, la provenance, la redaction et les contrats; onboarding couvre les conditions business, operations et securite avant activation reelle.

Les noms de variables d'environnement futurs pour secrets provider sont documentes uniquement en configuration locale avec valeurs vides. Les reponses publiques exposent seulement des categories et un statut de readiness, jamais des noms de variables secretes ni des valeurs.

Aucune migration, ecriture DB, connexion provider, API-Football, bookmaker, prediction reelle, ML ou seed production n'est ajoute en Phase 10.

## Phase 11 Provider Onboarding Gate Hardening
La Phase 11 durcit le gate sans changer sa surface publique principale.

`refuse_provider_activation` reste structurellement bloquant : les champs critiques utilisent des valeurs `false` et les objets checklist ou secret-readiness fournis par appel interne sont reinitialises a des valeurs sures. Cela ferme l'ambiguite des objets construits artificiellement sans validation.

`.env.example` reste limite a des placeholders vides et normalise en LF. Aucune cle reelle, aucun connecteur, aucun appel reseau, aucune ecriture DB et aucune migration ne sont ajoutes.

## Phase 12 Provider Env Secret Safety
La Phase 12 prepare la securite des futurs secrets provider sans activer de fournisseur reel.

`/api/v1/providers/readiness` et `/api/v1/providers/sandbox/status` exposent un resume public `secret_safety` limite a des booleens bloques, categories non sensibles, compteurs et exigences de stockage securise. Les noms complets des variables d'environnement provider et les valeurs locales ne sont jamais retournes dans les reponses publiques.

Le loader secret-safe peut inspecter l'environnement local pour les tests et futures validations, mais il ne serialise jamais les valeurs brutes et ne de-bloque jamais le gate. `can_activate=false`, `providers_enabled=false`, `network_calls_enabled=false`, `db_ingestion_enabled=false` et `blocked_until_real_provider_audit` restent inchanges.

Aucune migration, ecriture DB, connexion provider, API-Football, bookmaker, prediction reelle, ML ou seed production n'est ajoute en Phase 12.

## Phase 13 Provider Preflight Safety Review
La Phase 13 ajoute une decision preflight lisible avant toute future preparation provider reelle.

`/api/v1/providers/readiness` et `/api/v1/providers/sandbox/status` exposent `preflight_review` avec `status=blocked_until_real_provider_preflight_approved` et `real_provider_preparation_ready=false`. Les raisons de blocage couvrent secret manager, egress controls, quotas/rate limits, licence provider, monitoring, reconciliation et audit independant.

Cette decision reste informative et read-only. Elle n'active aucun provider, n'appelle aucun reseau, ne charge aucune cle, n'ecrit rien en base et ne cree aucune prediction.

## Phase 14 Real Provider Adapter Shell
La Phase 14 ajoute uniquement un shell d'adaptateur provider reel futur.

`/api/v1/providers/readiness` expose `real_provider_shell_status` avec le label public
`api_football_future_provider_shell`. Ce statut est informatif et entierement bloque :
`provider_enabled=false`, `network_calls_enabled=false`, `credentials_configured=false`,
`http_client_enabled=false`, `provider_base_url_configured=false`, `provider_endpoint_configured=false`,
`real_requests_enabled=false`, `db_ingestion_enabled=false` et `prediction_creation_enabled=false`.

Le shell ne contient aucune URL provider, aucun chemin endpoint, aucun nom de secret public, aucune valeur
secrete et aucune dependance HTTP active. Toute methode qui produirait des donnees provider leve une erreur
controlee avant tout appel reseau. Aucune migration, ecriture DB, prediction, resultat sportif, bookmaker,
ML ou seed production n'est ajoute.
