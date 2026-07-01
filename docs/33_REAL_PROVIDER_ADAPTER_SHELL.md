# Real Provider Adapter Shell

La Phase 14 ajoute un shell pour un futur adaptateur provider reel. Ce shell documente une forme technique
possible sans activer de fournisseur.

## Statut public
`/api/v1/providers/readiness` expose `real_provider_shell_status` avec :
- `label=api_football_future_provider_shell` ;
- `status=blocked_shell_only` ;
- `provider_enabled=false` ;
- `network_calls_enabled=false` ;
- `credentials_configured=false` ;
- `http_client_enabled=false` ;
- `provider_base_url_configured=false` ;
- `provider_endpoint_configured=false` ;
- `real_requests_enabled=false` ;
- `db_ingestion_enabled=false` ;
- `prediction_creation_enabled=false`.

Les reponses publiques ne doivent jamais exposer une URL provider, un chemin endpoint reel, un nom de variable
secrete provider ou une valeur secrete.

## Egress guard
`ProviderNetworkDisabledError` est leve avant toute operation qui exigerait une donnee provider reelle.
Le guard ne touche pas aux sockets et n'instancie aucun client HTTP.

## Hors portee
La Phase 14 ne connecte pas API-Football, n'appelle pas Internet, ne charge aucune cle, ne cree aucune
prediction, n'ingere rien en base, ne cree aucun resultat sportif, ne connecte aucun bookmaker, n'ajoute pas
de ML et ne modifie pas les migrations.

Les protections Phase 2 restent inchangees : anti data leakage, anti look-ahead bias, append-only et
predictions immuables.
