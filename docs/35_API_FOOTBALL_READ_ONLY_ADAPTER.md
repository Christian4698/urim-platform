# API-Football Read-Only Adapter

La Phase 16 ajoute uniquement une structure d'adaptateur API-Football read-only. Elle reste desactivee par
defaut et bloquee par le gate d'activation provider Phase 15.

## Statut public
`GET /api/v1/providers/readiness` expose `api_football_read_only_adapter_status` avec :

- `status=disabled_until_provider_activation_gate_approved`
- `enabled=false`
- `connected=false`
- `network_calls_enabled=false`
- `db_ingestion_enabled=false`
- `credentials_loaded=false`
- `prediction_creation_enabled=false`
- `betting_enabled=false`

## Methodes bloquees
Les methodes suivantes peuvent exister comme forme future, mais elles levent `ApiFootballProviderDisabledError`
avant toute execution :

- `fetch_fixtures`
- `fetch_results`
- `fetch_team_statistics`
- `fetch_standings`
- `fetch_lineups`
- `fetch_events`

## Garde-fous
- Aucun appel reseau API-Football.
- Aucun client HTTP, socket, URL provider ou endpoint reel.
- Aucune cle API, credential ou nom de secret public ajoute.
- Aucune ingestion DB, migration, modele DB, prediction, ML, bookmaker ou betting.
- Aucune donnee sportive reelle n'est creee, importee ou presentee.

## Risques couverts
- E001-E005 : completude, provenance, source unique et temporalite restent bloquees avant activation.
- E026 : aucune prediction ou decision forcee n'est creee.
- E037-E039 : aucun odds, lineup ou statistique future ne peut contaminer une prediction.
- E065-E074 : provider, latence, fallback, mapping, logs et secrets restent gates.
- E083-E084 : aucun betting reel et limites produit explicites.
