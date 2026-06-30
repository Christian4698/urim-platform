# Provider Onboarding Gate

Phase 10 cree un gate de verification avant toute activation provider reelle.

## Statut
Le gate reste bloque par defaut :
- `blocked_until_real_provider_audit`
- `can_activate=false`
- `providers_enabled=false`

Ce statut est volontaire. Il empeche d'activer un provider reel tant que les preuves techniques, securite, licence, operationnelles et qualite ne sont pas disponibles.

## Checklist d'activation
Avant une future activation provider, URIM/Kairos doit verifier :
- licence et redistribution ;
- quotas et rate limits ;
- latence mesuree ;
- pagination documentee ;
- retries et circuit breaker definis ;
- redaction des payloads ;
- monitoring et alertes ;
- reconciliation avec entites canoniques ;
- golden payloads reels anonymises ;
- audit securite ;
- secrets geres uniquement via environnement securise ou secret manager.

## Secrets
Les noms de variables d'environnement provider futurs peuvent etre documentes avec valeurs vides dans `.env.example`. Les reponses API publiques ne doivent jamais exposer ces noms ni aucune valeur.

## Hors portee Phase 10
Aucun connecteur API-Football, aucun appel Internet, aucune cle API reelle, aucun bookmaker, aucune mise reelle, aucun ML, aucune prediction reelle, aucun seed production, aucune ingestion DB et aucune migration ne sont ajoutes.

