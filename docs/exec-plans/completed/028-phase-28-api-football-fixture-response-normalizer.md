# Phase 28 API-Football Fixture Response Normalizer

## Objectif
Ajouter un normalizer backend local pour transformer un payload fake/test-only API-Football `/fixtures` en fixtures
normalisees public-safe, sans appel API reel, quota, secret, DB, prediction ou betting.

## Scope
- Ajouter un module local qui accepte uniquement un payload en memoire sous forme de mapping.
- Extraire seulement les champs fixture autorises par le contrat Phase 26.
- Retourner un resume public-safe avec `payload_hash`, `payload_top_level_keys`, fixtures normalisees et flags safe.
- Gerer une `response` vide, les champs imbriques manquants et une `response` mal typee sans exposer le brut.
- Ajouter des tests unitaires statiques sans socket, provider, DB, endpoint public ou runtime API.
- Ajouter la documentation Phase 28 et la reference dans l'index documentaire.

## Hors scope
- Aucun appel API-Football reel et aucune consommation de quota.
- Aucune cle, credential, URL provider, en-tete d'authentification ou payload provider brut dans les docs.
- Aucun endpoint public, runtime API, pyproject, README, frontend, scheduler, queue, webhook ou job.
- Aucune ecriture DB, migration Alembic, modele DB, ingestion, prediction, ML, odds, bookmaker, stake ou betting.
- Aucune reintroduction de `apps/web/lib/integrations`, `_references/public-apis` ou `docs/api-catalog.md`.

## Regles de securite
- Les payloads Phase 28 sont fake/test-only et ne deviennent pas une source provider active.
- Le normalizer calcule un hash deterministe mais ne retourne jamais le contenu provider brut.
- Les champs manquants restent `None`; ils ne deviennent jamais `0`, `False` ou valeur inventee.
- La sortie indique explicitement `db_writes=false`, `prediction_created=false` et `betting_created=false`.

## Validation
Depuis `apps/api` :

```bash
ruff check .
pytest
```

Depuis la racine :

```bash
git diff --check
git status --short --untracked-files=all
```

Ajouter un scan cible des nouveaux fichiers Phase 28 pour verifier l'absence de secrets, URLs provider, marqueurs de
payload brut et flags d'activation DB/prediction/betting.

## Risques couverts
- E001-E005 : le payload fake ne devient pas une source active et ne peut pas alimenter une prediction.
- E026 : aucune prediction forcee ou decision utilisateur n'est creee.
- E037-E039 : odds, lineups, statistiques avancees et evenements restent hors activation.
- E065-E074 : provider, fallback, mapping, latence, logs, valeurs manquantes et secrets restent gates.
- E083-E084 : aucun betting et limites produit explicites.
