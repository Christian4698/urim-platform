# Sécurité — URIM

## Principes fondamentaux

- Aucune clé fournisseur dans le frontend, les logs ou Git (E074).
- Toutes les clés via secret manager — jamais dans `.env` commité.
- Audit log immuable pour toute action sensible.
- Least privilege : chaque service n'accède qu'à ce dont il a besoin.
- Fail closed : en cas de doute, refuser et logger.

## Secrets

### Règles
- Les clés API fournisseurs résident uniquement dans le secret manager (GCP Secret Manager ou Vault).
- Les services les lisent via l'API du secret manager au démarrage ou à la rotation.
- `.env` est interdit dans Git (`.gitignore` bloquant + `env-guard` CI).
- `.env.example` commité avec des valeurs fictives uniquement.
- Rotation documentée : toute clé compromise → révocation dans les 15 minutes + incident log.

### Secret scan CI
Le job `secret-scan` (gitleaks) bloque toute PR contenant une clé détectable.
Patterns surveillés : `API_KEY`, `SECRET`, `PASSWORD`, `TOKEN`, `-----BEGIN`, `AKIA*`, UUID longs.

### Variables d'environnement sensibles
```
# Interdit dans Git — lire depuis secret manager uniquement
PROVIDER_X_API_KEY
PROVIDER_Y_API_KEY
JWT_SECRET
DB_PASSWORD
REDIS_PASSWORD
```

## API — Authentification et autorisation

### AuthN
- JWT signé RS256 (clé publique vérifiable sans partager la clé privée).
- Expiration courte : `access_token` 15 min, `refresh_token` 7 jours.
- Révocation via liste noire Redis (jti claim).

### RBAC
| Rôle | Permissions |
|---|---|
| `viewer` | Lecture prédictions, calibration, dashboard |
| `analyst` | Viewer + lecture provenance, logs d'agents |
| `operator` | Analyst + gestion fournisseurs, désactivation |
| `admin` | Operator + gestion utilisateurs, migrations |

### Rate limiting
- Par IP : 100 req/min sur les endpoints publics.
- Par token : 1000 req/min sur les endpoints authentifiés.
- Header `Retry-After` sur 429.

### Validation stricte
- Tous les inputs validés par Pydantic v2 avant traitement.
- Rejet immédiat de tout champ inconnu (`extra = "forbid"`).
- IDs vérifiés contre base avant toute opération.

### Protection SSRF
- Le backend ne fait jamais de requête HTTP vers une URL fournie par l'utilisateur.
- Les URLs fournisseurs sont configurées en dur dans le secret manager ou le registre fournisseur.
- Pas de redirect dynamique.

### Webhooks
- Signature HMAC-SHA256 vérifiée sur chaque payload entrant.
- Replay-protection : timestamp dans la signature, rejet si `|now - ts| > 5 min`.

### CORS
- `ALLOWED_ORIGINS` exhaustif : jamais `*` en production.
- Credentials uniquement pour les origines explicitement listées.

### Audit logs
- Toute écriture (prédiction publiée, désactivation fournisseur, modification utilisateur) loggée avec `actor`, `action`, `resource_id`, `timestamp`, `ip`.
- Logs append-only, non modifiables par l'API.

## Données

### Chiffrement
- Transit : TLS 1.3 minimum pour toutes les communications.
- Repos : chiffrement du disque activé (cloud provider).
- Payloads bruts sensibles : stockés chiffrés en object storage.

### Minimisation
- Les payloads bruts fournisseurs ne sont jamais exposés via l'API.
- Les logs ne contiennent pas de données personnelles ni de clés.
- `REDACT_LOGS=true` en production pour masquer automatiquement les patterns sensibles.

### Rétention
- Prédictions : illimitée (ledger immuable).
- Payloads bruts : 90 jours (configurable).
- Audit logs : 1 an minimum.
- Données utilisateur : selon politique de confidentialité.

## Supply chain

### Dépendances
- Lockfiles commités (`requirements.lock`, `package-lock.json`).
- `pip-audit` ou `safety` en CI pour scanner les dépendances Python.
- `npm audit` pour le frontend.
- Pas de dépendances directes sur des forks non maintenus.

### Images Docker
- Images de base officielles minimales (`python:3.12-slim`, `node:20-alpine`).
- `COPY` uniquement les fichiers nécessaires.
- Pas de `RUN apt-get install` de paquets inutiles.
- Scanner d'images (Trivy ou equivalant) en CI.

### SBOM
- Générer un SBOM par release (CycloneDX ou SPDX).

## Frontend

- Aucune clé fournisseur dans `apps/web`.
- Aucun appel B2B direct depuis le navigateur.
- CSP stricte : `script-src 'self'`, pas de `unsafe-inline` en production.
- Tous les inputs utilisateur HTML-échappés.
- Pas de `dangerouslySetInnerHTML` avec contenu externe.

## Checklist pré-release

- [ ] Gitleaks ne détecte aucun secret.
- [ ] `.env` absent du dépôt.
- [ ] `pip-audit` 0 vulnérabilité critique.
- [ ] `npm audit` 0 vulnérabilité critique.
- [ ] Trivy image scan OK.
- [ ] CORS configuré sans `*`.
- [ ] JWT expiration vérifiée.
- [ ] Rate limiting activé.
- [ ] `REDACT_LOGS=true` en production.
- [ ] SBOM généré et archivé.
- [ ] Incident log à jour.

## Erreurs E couvertes

- **E074** : clés API mal protégées → secret manager obligatoire, gitleaks CI bloquant.
- **E067** : ledger immuable → audit logs append-only.
- **E071** : missing confondu avec zéro → validation Pydantic `extra = "forbid"`.
