# API-Football Env-Gated Smoke Client

La Phase 18 ajoute uniquement un smoke client API-Football interne, desactive par defaut et utilisable seulement
avec une configuration locale explicite non committee.

## Statut public
`GET /api/v1/providers/readiness` expose `api_football_smoke_client_status` avec :

- `status=disabled_until_explicit_local_smoke_env`
- `enabled_by_default=false`
- `smoke_mode_enabled=false`
- `network_calls_enabled_by_default=false`
- `public_endpoint_enabled=false`
- `db_ingestion_enabled=false`
- `credentials_exposed=false`
- `prediction_creation_enabled=false`
- `betting_enabled=false`
- `real_provider_connected=false`

Ce statut reste public-safe : il ne retourne jamais les noms ou valeurs des variables locales, une cle, un
credential, une URL provider ou le contenu d'une reponse smoke.

## Conditions d'execution interne
Le smoke client refuse toute execution avant transport si les conditions suivantes ne sont pas toutes reunies :

- mode smoke explicitement active en local ;
- materiel d'authentification present localement hors depot ;
- execution confirmee read-only ;
- environnement non-production confirme ;
- gate final provider consulte et toujours bloque ;
- transport explicitement injecte par l'appelant local.

## Garde-fous
- Aucun endpoint public ne lance le smoke client.
- Aucun appel API-Football reel n'est effectue par defaut.
- Aucun `requests`, `httpx` ou `aiohttp` provider n'est ajoute pour cette phase.
- Aucune donnee smoke n'est ingeree en base.
- Aucune prediction, ML, bookmaker, cote, mise ou betting n'est cree.
- Aucune vraie cle API ou URL provider n'est ajoutee dans le code public, `.env.example` ou les reponses API.

## Risques couverts
- E001-E005 : provenance et temporalite restent bloquees avant toute activation.
- E026 : aucune prediction ou decision forcee n'est creee.
- E037-E039 : aucun resultat, lineup ou statistique smoke ne peut alimenter une prediction.
- E065-E074 : provider, fallback, latence, logs et secrets restent gates et redacted.
- E083-E084 : aucun betting reel et limites produit explicites.
