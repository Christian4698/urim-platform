# URIM API

Backend FastAPI des Programmes B1, B2.1 et B2.2.

## Capacités actives

- sondes publiques `/health` et `/readiness`;
- PostgreSQL via SQLAlchemy 2 et Alembic;
- client API-Football backend-only avec timeout, retry borné, rate limiting,
  budget par run, quotas et validation de réponse;
- normalisation traçable des compétitions, saisons, équipes, matchs,
  classements, statistiques, événements, compositions et blessures;
- stockage append-only et idempotent;
- journal des synchronisations et erreurs neutralisées;
- routes read-only sous `/api/v1/sports`;
- Kairos Core B2.1 sous `/api/v1/kairos`, pré-match, read-only, non persisté
  et non calibré;
- Kairos B2.2 sous `/api/v1/kairos/suggestions/today`, analytique et read-only;
- contrat détaillé séparant `safety_decision` (Garde-fou Kairos) et
  `analytical_suggestion` (Suggestion analytique), avec alias historiques
  strictement équivalents;
- commandes manuelles `urim-sports-sync`.

Le client est désactivé par défaut et sans clé. Les prédictions officielles
publiées, bookmakers, live automatique, authentification et paris réels
restent désactivés. Kairos Core ne constitue pas un conseil de pari.

## Installation et validation

```powershell
python -m pip install -e ".[dev]"
ruff check .
pytest
python -m build
```

Avec une base PostgreSQL jetable :

```powershell
$env:B1_TEST_DATABASE_URL="<URL PostgreSQL explicitement isolée de test>"
python scripts/b1_test_database_gate.py --migrate
pytest tests/test_database_foundation.py `
  tests/test_program_b1_postgres_integration.py `
  tests/test_kairos_core_postgres_integration.py
```

Le gate refuse l'exécution si l'URL manque, n'est pas PostgreSQL, ressemble à
une cible de production, ne porte pas de marqueur explicite de test, correspond
à `DATABASE_URL` ou si `APP_ENV` est production-like. Il n'affiche jamais une
URL de connexion. `B1_TEST_DATABASE_URL` est réservée au poste de test ou à la
CI et ne doit pas être configurée sur le service Render de production.

Kairos requiert aussi `REDIS_URL` en production. Le rate limiting distribué est
fail-closed : si Redis manque ou ne répond pas, les endpoints Kairos retournent
un 503 avant toute requête PostgreSQL et la readiness reste négative.
Le code public `kairos_rate_limit_unavailable` est destiné à un message
frontend neutralisé; aucun hôte, credential ou détail Redis n'est sérialisé.

Depuis le Shell Render du service `urim-api`, après configuration runtime de
`REDIS_URL`, le gate d'intégration Redis s'exécute avec :

```text
python scripts/b2_2_redis_gate.py
```

Le gate refuse une URL absente, locale, factice ou invalide, puis contrôle le
ping, le script atomique concurrent, le TTL, les limites 30/120, le hashage
client et le comportement fail-closed. Il utilise uniquement des clés
éphémères à espace de noms unique, supprime exactement ces clés et ne journalise
jamais l'URL, l'hôte ni les identifiants.

La configuration complète, le schéma, les routes et le runbook Render sont dans
`docs/72_PROGRAM_B1_REAL_SPORTS_DATA.md`. La méthodologie Kairos Core est dans
`docs/73_PROGRAM_B2_1_KAIROS_CORE.md`.
Les suggestions quotidiennes sont documentées dans
`docs/76_PROGRAM_B2_2_KAIROS_DAILY_SUGGESTIONS.md`.
