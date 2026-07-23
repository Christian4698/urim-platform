# Programme B1 — Fondation des données sportives réelles

## Statut

Le Programme B1 fournit le connecteur backend API-Football, le pipeline
d'acquisition contrôlé, le stockage PostgreSQL append-only, les API publiques
en lecture seule et l'écran de contrôle frontend. Le fournisseur reste
désactivé tant que sa clé backend et le drapeau d'activation ne sont pas tous
les deux configurés.

Ce programme ne crée aucune prédiction, probabilité officielle, recommandation,
mise, cote bookmaker, authentification ou tâche live permanente.

## Architecture du pipeline

```text
Commande opérateur bornée
  └─ urim-sports-sync
       ├─ vérification activation + périmètre + budget
       ├─ client API-Football backend-only
       │    ├─ URL et endpoints allowlistés
       │    ├─ timeout, retry borné, backoff et rate limiting
       │    ├─ validation stricte de l'enveloppe
       │    └─ quotas lus depuis les en-têtes
       ├─ normalisation
       │    ├─ valeurs absentes conservées à NULL
       │    ├─ contrôle temporel bloquant
       │    ├─ raw_hash sans stockage du payload brut
       │    └─ provenance et quality_flags obligatoires
       └─ PostgreSQL / Supabase
            ├─ observations append-only et idempotentes
            ├─ journal des synchronisations et erreurs neutralisées
            └─ RLS activé, aucun accès anon/authenticated
                  ↓
            FastAPI read-only
                  ↓
            Next.js /donnees-sportives
```

Une relance reprend le même périmètre sans écraser une observation publiée.
La contrainte unique `(provider, provider_event_id, raw_hash)` transforme les
relectures identiques en doublons comptabilisés. Une version dont le hash
change est une nouvelle observation traçable.

## Contrat de provenance

Chaque observation sportive porte :

- `provider`, toujours `api-football`;
- `provider_event_id`;
- `observed_at`, `available_at`, `fetched_at`;
- `source_version`;
- `quality_flags`;
- `raw_hash`;
- `provider_id`, `sync_run_id`;
- `freshness_status`;
- `created_at`.

L'ordre `observed_at <= available_at <= fetched_at` est imposé par la
normalisation et par PostgreSQL. Les réponses brutes et les médias distants ne
sont pas conservés. Une absence fournisseur reste `NULL`; elle n'est jamais
remplacée par une valeur inventée.

## Schéma des données

Migration : `26fe26a73d5c_programme_b1_sports_data_foundation.py`.

| Table | Rôle | Identité métier principale |
|---|---|---|
| `sports_sync_runs` | exécutions, compteurs, quotas, checkpoint | UUID de run |
| `sports_sync_errors` | erreurs publiques neutralisées | UUID d'erreur |
| `api_football_competitions` | compétitions et couverture | ID compétition |
| `api_football_seasons` | saisons et périodes | compétition + année |
| `api_football_teams` | équipes et stades disponibles | ID équipe |
| `api_football_matches` | calendrier, statut et scores disponibles | ID match |
| `api_football_standings` | classements observés | compétition + saison + équipe |
| `api_football_match_statistics` | statistiques équipe/match | match + équipe + type |
| `api_football_match_events` | événements de match | clé événement stable |
| `api_football_injuries` | blessures disponibles | match/équipe/joueur |
| `api_football_lineups` | titulaires, remplaçants et formation | match/équipe/joueur/rôle |

Les onze nouvelles tables de données et de synchronisation ont RLS activé. Les tables
d'observations sportives ont un trigger qui refuse `UPDATE` et `DELETE`.

## Client fournisseur

Le client n'accepte que l'origine fixe
`https://v3.football.api-sports.io`, l'en-tête backend
`x-apisports-key` et les ressources suivantes :

- `leagues`;
- `teams`;
- `fixtures`;
- `standings`;
- `fixtures/statistics`;
- `fixtures/events`;
- `fixtures/lineups`;
- `injuries`.

Les chemins et paramètres de prédiction, odds, bookmakers, betting et live sont
bloqués. Le client refuse les redirections, n'utilise pas les proxys ambiants,
limite les retries à trois au maximum et neutralise les corps d'erreur. Les
logs ne contiennent ni clé, ni header d'authentification, ni payload fournisseur.

## Commandes contrôlées

Depuis `apps/api`, après installation du package :

```powershell
urim-sports-sync competitions
urim-sports-sync seasons
urim-sports-sync teams
urim-sports-sync standings
urim-sports-sync matches-date --date 2026-07-23
urim-sports-sync upcoming --days 7
urim-sports-sync results --from 2026-07-01 --to 2026-07-23
urim-sports-sync statistics --from 2026-07-16 --to 2026-07-23
```

`statistics --statistics-only` exclut événements, compositions et blessures.
Les fenêtres sont bornées à 31 jours, le nombre de compétitions à 10 et le
budget par synchronisation à 100 requêtes au maximum. Aucun cron live n'est
créé par B1.

## API publique en lecture seule

Toutes les routes sont sous `/api/v1/sports` :

| Méthode et route | Réponse |
|---|---|
| `GET /provider` | activation, configuration, restrictions |
| `GET /competitions` | dernières compétitions observées |
| `GET /matches/today` | matchs UTC du jour |
| `GET /matches/upcoming?days=7` | matchs à venir, fenêtre 1 à 30 jours |
| `GET /matches/{provider_match_id}` | match et ressources associées |
| `GET /sync/status` | dernier run et erreurs publiques |
| `GET /freshness` | fraîcheur par ressource |

Les erreurs de base ou fournisseur deviennent des réponses publiques génériques.
Les routes ne retournent aucun nom de secret, URL de base de données ou détail
interne.

## Interface frontend

La route `/donnees-sportives` affiche :

- statut du fournisseur sans secret;
- fraîcheur et dernière synchronisation;
- compétitions et matchs disponibles;
- états loading, empty, error et offline;
- erreurs publiques neutralisées;
- rappel explicite du mode consultation, sans prédiction ni pari.

Le navigateur appelle uniquement FastAPI. Il ne connaît ni l'origine
API-Football ni son header d'authentification.

## Variables d'environnement

Variables réservées au service backend :

| Variable | Secret | Valeur initiale recommandée |
|---|---:|---|
| `API_FOOTBALL_KEY` | oui | définie uniquement dans le coffre Render |
| `API_FOOTBALL_ENABLED` | non | `false`, puis `true` après le runbook |
| `API_FOOTBALL_PRIORITY_COMPETITIONS` | non | liste CSV de 3 à 5 IDs validés |
| `API_FOOTBALL_SEASON` | non | saison courante validée |
| `API_FOOTBALL_REQUEST_TIMEOUT_SECONDS` | non | `10` |
| `API_FOOTBALL_MAX_RETRIES` | non | `2` |
| `API_FOOTBALL_REQUESTS_PER_MINUTE` | non | `10` |
| `API_FOOTBALL_MAX_REQUESTS_PER_SYNC` | non | `10` |
| `API_FOOTBALL_UPCOMING_DAYS` | non | `7` |
| `API_FOOTBALL_FRESHNESS_MINUTES` | non | `180` |

`API_FOOTBALL_KEY` ne doit jamais être placée dans `render.yaml`, une variable
`NEXT_PUBLIC_*`, un fichier `.env` suivi par Git, une commande partagée ou un
rapport. Le frontend ne reçoit aucune variable API-Football.

## Procédure Render

1. Sauvegarder la base et vérifier le head Alembic courant.
2. Déployer le code backend avec `API_FOOTBALL_ENABLED=false`.
3. Exécuter `alembic upgrade head` sur le service backend.
4. Vérifier `/health`, `/readiness` et `/api/v1/sports/provider`.
5. Ajouter les variables non secrètes au service backend
   `urim-api-jrbk`.
6. Ajouter `API_FOOTBALL_KEY` directement dans l'interface Render comme secret,
   sans la copier dans un ticket, un log ou cette documentation.
7. Valider les droits contractuels, la couverture, le quota et les IDs de
   compétitions retenus.
8. Passer `API_FOOTBALL_ENABLED=true`, redéployer, puis lancer manuellement
   `urim-sports-sync competitions`.
9. Vérifier le statut du run, sa fraîcheur et l'absence d'erreur publique.
10. Lancer successivement saisons, équipes, classements et une petite fenêtre
    de matchs. Ne programmer aucun live permanent.
11. Déployer le frontend par le Blueprint `render.yaml`; son build filter couvre
    `apps/web/**`.
12. En cas d'incident, repasser immédiatement
    `API_FOOTBALL_ENABLED=false`. Les données déjà observées restent immuables.

## Validation locale obligatoire

```powershell
cd apps/api
alembic upgrade head
alembic current
alembic check
ruff check .
pytest

cd ../..
pnpm contracts:validate
pnpm web:lint
pnpm web:typecheck
pnpm web:test
pnpm web:build
pnpm audit --prod
git diff --check
```

Le test PostgreSQL B1 utilise exclusivement une base jetable explicitement
fournie via `B1_TEST_DATABASE_URL`. Il vérifie la migration réelle, RLS,
l'append-only et l'idempotence.

## Limites et risques

- La disponibilité exacte des blessures, compositions, événements et
  statistiques dépend de la couverture de chaque compétition.
- Les droits de publication doivent être confirmés avant exposition publique de
  données synchronisées.
- Le quota fournisseur impose un périmètre initial réduit et une surveillance
  des headers de quota.
- B1 n'effectue pas de validation croisée avec un second provider.
- Une synchronisation réussie prouve l'acquisition, pas la qualité prédictive.
- Aucun moteur KAIROS, bookmaker, live automatique ou pari réel n'est activé.

## Étape B2

B2 devra porter sur la qualité, la réconciliation et les snapshots historiques
`as-of` : contrôles de couverture, second fournisseur si autorisé, politiques de
correction, archivage sous licence, métriques de complétude et datasets
reproductibles. Le moteur KAIROS ne peut commencer qu'après cette validation.
