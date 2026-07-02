# API-Football Test Transport Contracts

La Phase 17 ajoute un transport API-Football test-only pour verifier les formes de reponse futures sans
connecter API-Football.

## Statut public
`GET /api/v1/providers/readiness` expose `api_football_test_transport_contracts_status` avec :

- `status=test_only_contracts_no_public_runtime`
- `test_transport_enabled=false`
- `public_endpoint_enabled=false`
- `network_calls_enabled=false`
- `db_ingestion_enabled=false`
- `credentials_loaded=false`
- `prediction_creation_enabled=false`
- `betting_enabled=false`
- `production_payloads_enabled=false`
- `real_provider_connected=false`

## Contrats couverts
Le faux transport interne couvre uniquement des payloads placeholders pour :

- `fixtures`
- `results`
- `team_statistics`
- `standings`
- `lineups`
- `events`

Chaque payload doit porter `TEST_ONLY`, `DEMO_NON_PROD`, `PLACEHOLDER`, `provider_name`, `fetched_at`
timezone-aware, `raw_hash` stable et des timestamps ordonnes.

## Garde-fous
- Aucun appel reseau API-Football.
- Aucun `requests`, `httpx`, `aiohttp`, socket, URL provider ou endpoint reel.
- Aucune cle API, credential ou nom de secret public ajoute.
- Aucune ingestion DB, migration, modele DB, prediction, ML, bookmaker ou betting.
- Aucun vrai club, score, cote, competition ou resultat sportif de production.
- Aucun fallback mock silencieux en production.

## Risques couverts
- E001-E005 : completude, provenance, source unique et temporalite restent contractuelles et bloquees.
- E026 : aucune prediction ou decision forcee n'est creee.
- E037-E039 : lineups, statistiques et resultats test-only ne peuvent pas alimenter une prediction.
- E065-E074 : provider, fallback, timestamps, mapping, latence, logs et secrets restent gates.
- E083-E084 : aucun betting reel et limites produit explicites.
