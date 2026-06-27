# Securite

## Secrets
Secret manager, rotation, separation des environnements, secret scan CI et revocation documentee.

## API
AuthN/AuthZ, RBAC, rate limits, validation stricte, protection SSRF, webhooks signes, CORS minimal et audit logs.

### Phase 4 API Hardening
La Phase 4 durcit uniquement la fondation FastAPI existante. Elle ajoute des headers de securite systematiques : `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` et `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`.

Cette CSP est adaptee a une API et peut volontairement limiter le rendu des documentations interactives. Un portail docs, une authentification complete, RBAC complet, sessions, cookies et CORS applicatif restent hors portee de la Phase 4.

Les reponses publiques ne doivent jamais exposer `DATABASE_URL`, mots de passe locaux, cles API, secrets ou credentials fournisseur. Providers, API-Football, bookmakers, ML, live, real betting, prediction creation, mocks de production et seeds de production restent desactives.

Le Bet Center reste 100 % virtuel/interne. Aucune mise reelle, aucun bookmaker et aucune execution financiere ne sont autorises.

## Donnees
Chiffrement, minimisation, retention, acces limite aux payloads bruts, respect des licences.

## Supply Chain
Lockfiles, scans, images minimales, SBOM et mises a jour controlees.

## Frontend
Aucune cle fournisseur, aucun appel B2B direct, CSP et HTML nettoye.
