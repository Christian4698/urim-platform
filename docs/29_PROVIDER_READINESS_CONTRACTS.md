# Provider Readiness Contracts

Phase 6 prepare les contrats provider URIM/Kairos sans connecter de fournisseur reel.

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
