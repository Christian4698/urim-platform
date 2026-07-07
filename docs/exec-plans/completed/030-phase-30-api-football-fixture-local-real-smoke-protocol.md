# Phase 30 API-Football Fixture Local-Only Real Smoke Protocol

## Objectif
Preparer le protocole local-only qui dira si un futur vrai smoke API-Football `/fixtures` serait autorisable, sans
executer ce vrai appel dans cette phase.

## Scope
- Ajouter une documentation Phase 30 pour les conditions avant un futur appel `/fixtures`.
- Ajouter un script de protocole/preflight local-only qui retourne uniquement un JSON public-safe.
- Valider une query minimale limitee a `date` et `timezone`.
- Refuser la production, l'activation implicite, les confirmations read-only/non-prod manquantes et les gates
  DB/prediction/betting manquants.
- Refuser les parametres fixture hors phase comme `league`, `team`, `season`, odds, bookmaker, stake, prediction et
  betting.
- Ajouter des tests statiques et unitaires sans reseau, provider reel, DB, endpoint public ou runtime API.
- Ajouter la reference Phase 30 dans l'index documentaire.

## Hors scope
- Aucun appel API-Football reel et aucune consommation de quota.
- Aucune cle, credential, URL provider, en-tete d'authentification ou payload provider brut.
- Aucun endpoint public, runtime API, pyproject, README, frontend, scheduler, queue, webhook ou job.
- Aucune ecriture DB, migration Alembic, modele DB, ingestion, prediction, ML, odds, bookmaker, stake ou betting.
- Aucune reintroduction de `apps/web/lib/integrations`, `_references/public-apis` ou `docs/api-catalog.md`.

## Regles de securite
- Le protocole ne demande aucune cle API et ne valide aucun secret.
- Le protocole n'appelle aucun client reseau et ne construit aucune URL provider.
- La seule query autorisable est `date` + `timezone`.
- La sortie indique toujours `executed=false`, `db_writes=false`, `prediction_created=false` et
  `betting_created=false`.

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

Ajouter un scan cible des nouveaux fichiers Phase 30 pour verifier l'absence de secrets, URLs provider, marqueurs de
payload brut et flags d'activation DB/prediction/betting.

## Risques couverts
- E001-E005 : aucune donnee provider n'est consommee ou presentee comme disponible.
- E026 : aucune prediction forcee ou decision utilisateur n'est creee.
- E037-E039 : odds, lineups, statistiques avancees et evenements restent hors activation.
- E065-E074 : provider, fallback, mapping, latence, logs, valeurs manquantes et secrets restent gates.
- E083-E084 : aucun betting et limites produit explicites.
