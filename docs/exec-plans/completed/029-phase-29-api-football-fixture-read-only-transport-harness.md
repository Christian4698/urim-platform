# Phase 29 API-Football Fixture Read-Only Transport Harness

## Objectif
Ajouter un harness backend local qui connecte le request builder `/fixtures`, un transport injecte fake/test-only et le
fixture response normalizer, sans appel API reel, quota, secret, DB, prediction ou betting.

## Scope
- Construire la requete safe via le builder Phase 27.
- Passer le resume de requete public-safe a un transport injecte par les tests.
- Normaliser le payload fake/test-only via le normalizer Phase 28.
- Retourner une reponse public-safe contenant la query, le transport utilise, les fixtures normalisees et les flags
  d'absence de DB/prediction/betting.
- Gerer proprement une response vide et une erreur de transport fake sans exposer le contenu provider.
- Ajouter des tests unitaires statiques sans socket, provider reel, DB, endpoint public ou runtime API.
- Ajouter la documentation Phase 29 et la reference dans l'index documentaire.

## Hors scope
- Aucun appel API-Football reel et aucune consommation de quota.
- Aucune cle, credential, URL provider, en-tete d'authentification ou contenu provider complet dans les docs.
- Aucun endpoint public, runtime API, pyproject, README, frontend, scheduler, queue, webhook ou job.
- Aucune ecriture DB, migration Alembic, modele DB, ingestion, prediction, ML, odds, bookmaker, stake ou betting.
- Aucune reintroduction de `apps/web/lib/integrations`, `_references/public-apis` ou `docs/api-catalog.md`.

## Regles de securite
- Le transport est toujours injecte et test-only dans cette phase.
- Le harness ne construit aucun client reseau et ne depend d'aucun secret.
- La query doit rester validee par le builder; les parametres inconnus ou interdits sont refuses avant transport.
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

Ajouter un scan cible des nouveaux fichiers Phase 29 pour verifier l'absence de secrets, URLs provider, marqueurs de
contenu provider brut et flags d'activation DB/prediction/betting.

## Risques couverts
- E001-E005 : le transport fake ne devient pas une source active et ne peut pas alimenter une prediction.
- E026 : aucune prediction forcee ou decision utilisateur n'est creee.
- E037-E039 : odds, lineups, statistiques avancees et evenements restent hors activation.
- E065-E074 : provider, fallback, mapping, latence, logs, valeurs manquantes et secrets restent gates.
- E083-E084 : aucun betting et limites produit explicites.
