# Provider Readiness Contracts

Phase 6 prepare les contrats provider URIM/Kairos sans connecter de fournisseur reel. Phase 7 renforce ces contrats avec une couche QA, redaction et golden payloads non-production.

## Perimetre
- Aucun connecteur API-Football.
- Aucun appel reseau provider.
- Aucune cle API ou credential provider.
- Aucun bookmaker, aucune mise reelle, aucune prediction reelle et aucun modele ML.
- Aucun seed de production et aucun resultat sportif fictif presente comme reel.

## Contrats exposes
Les schemas backend Phase 6 couvrent :
- `ProviderIdentity`
- `ProviderCapability`
- `ProviderCapabilityMatrix`
- `TemporalAvailabilityMetadata`
- `RawPayloadReference`
- `ProviderObservation`
- `CanonicalEntityMapping`
- `OfficialResultEnvelope`
- `DataQualityReport`
- `ProviderReadinessResponse`

## Provenance obligatoire
Toute observation provider future doit porter :
- `provider`
- `provider_event_id`
- `observed_at`
- `available_at`
- `fetched_at`
- `source_version`
- `raw_hash`
- `quality_flags`

Ces champs ne remplacent pas les protections Phase 2 : les payloads bruts, observations, snapshots et predictions publiees restent append-only ou immuables selon leur table.

## Temporalite
La regle provider de base est :

```text
observed_at <= available_at <= fetched_at
```

La regle prediction future reste :

```text
available_at <= prediction_time
```

Une observation disponible apres l'heure de prediction ne peut pas alimenter une prediction passee.

## Qualite et securite
- Les providers restent desactives.
- Toutes les capacites provider restent desactivees.
- `production_mock_fallback_allowed` reste `false`.
- Le Bet Center reste virtuel/interne.
- Les resultats declares par l'utilisateur dans les tickets ne sont jamais source d'apprentissage.
- Le futur Post-Match Learning ne peut apprendre que depuis `post_match_outcomes` officiels verifies.

## Endpoint
`GET /api/v1/providers/readiness` retourne uniquement les exigences contractuelles et les statuts desactives.

`POST /api/v1/providers/readiness` n'existe pas et doit retourner `405`.

## Phase 7 QA
Phase 7 ajoute les exigences QA suivantes a la readiness provider :
- `license_review_required`
- `quota_and_rate_limit_required`
- `golden_payloads_required`
- `payload_redaction_required`
- `monitoring_required`
- `independent_audit_required`
- `no_production_mock_fallback`

Les golden payloads restent limites aux tests et a la documentation. Ils doivent etre marques `DEMO_NON_PROD` ou `PLACEHOLDER`, ne doivent pas contenir de resultat sportif reel et ne doivent jamais remplacer une observation provider reelle.

La redaction des payloads provider doit masquer recursivement les cles sensibles, notamment `api_key`, `token`, `authorization`, `secret`, `password`, `bearer`, `credential` et `provider_credentials`.

## Phase 8 Sandbox Adapter
Phase 8 ajoute un adaptateur sandbox interne pour valider les contrats sans fournisseur reel.

Contraintes :
- payloads uniquement en memoire ;
- marqueurs `DEMO_NON_PROD`, `PLACEHOLDER` et `SANDBOX_ONLY` obligatoires ;
- aucun nom d'equipe reel, score, vainqueur, identifiant provider reel, bookmaker ou credential ;
- aucun appel reseau ;
- aucune ingestion base de donnees ;
- aucune prediction creee.

L'endpoint `GET /api/v1/providers/sandbox/status` expose uniquement un statut informatif, les hashes stables des payloads sandbox, les capacites desactivees et des resumes de payloads passes par redaction.

## Phase 9 Sandbox Integration QA
Phase 9 renforce l'auditabilite du sandbox sans connecter de provider reel.

Le flux complet expose ou teste uniquement des contrats :
`identity -> payloads -> raw_reference -> observation -> quality_report -> canonical_mapping_placeholder -> official_result_envelope_placeholder`.

`official_result_envelope` reste volontairement sandbox-only. Il sert a verifier la forme d'une enveloppe future sans resultat sportif, sans score, sans vainqueur et sans activation de Post-Match Learning. Le protocole fournisseur general reste limite aux donnees provider; le futur Official Result Verifier sera une surface separee.

Avant tout provider reel, les prerequis restent obligatoires :
- licence et redistribution ;
- quotas, rate limits et couts ;
- latence, pagination, retries et circuit breaker ;
- redaction recursive et absence de secret expose ;
- monitoring, alertes et procedure de desactivation ;
- reconciliation avec entites canoniques et provenance par champ ;
- golden payloads reels anonymises ;
- audit securite independant.

Les contrats quota/rate-limit/reconciliation sont readiness-only en Phase 9. Aucun scheduler, queue, retry execution, circuit breaker execution, appel reseau provider, ecriture DB ou overwrite canonique n'est ajoute.
