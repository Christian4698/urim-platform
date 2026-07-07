# Phase 26 API-Football Read-Only Endpoint Fixture Contract

## Objectif
Selectionner les premiers endpoints API-Football read-only utiles a Kairos et formaliser un contrat fixture
conceptuel sans consommer l'API reelle et sans activer ingestion, prediction ou betting.

## Scope
- Ajouter la documentation Phase 26 pour le choix des endpoints read-only.
- Declarer `/fixtures` comme endpoint prioritaire pour le premier contrat conceptuel.
- Documenter `/leagues`, `/teams` et `/standings` comme utiles en planification read-only.
- Marquer `/fixtures/headtohead`, `/fixtures/statistics` et `/fixtures/events` comme candidats later only.
- Marquer `/predictions` et `/odds` comme interdits pour l'instant.
- Ajouter un test documentaire statique et referencer la Phase 26 dans l'index.

## Hors scope
- Aucun appel API-Football reel et aucune consommation de quota.
- Aucune cle, credential, URL provider, reference locale ou payload provider brut.
- Aucun endpoint public, runtime API, pyproject, frontend, scheduler, queue, webhook ou job.
- Aucune ecriture DB, migration Alembic, modele DB, ingestion, prediction, ML, cote, bookmaker, stake ou betting.
- Aucune reintroduction de `apps/web/lib/integrations`, `_references/public-apis` ou `docs/api-catalog.md`.

## Regles de securite
- Les endpoints peuvent etre nommes seulement comme chemins conceptuels, sans URL provider.
- Le contrat fixture reste une liste de champs safe et ne devient pas un schema de stockage.
- Les champs fixture ne peuvent alimenter aucune prediction avant une future phase de provenance et temporalite.
- `/predictions` et `/odds` restent explicitement interdits.

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

Ajouter des `git grep` cibles pour verifier l'absence de secret, URL provider, payload brut et flags
d'activation DB/prediction/betting dans les nouveaux fichiers Phase 26.

## Risques couverts
- E001-E005 : les endpoints utiles restent documentes sans source unique active ni fuite temporelle.
- E026 : aucune prediction ou decision forcee n'est creee.
- E037-E039 : odds, lineups, statistiques et evenements restent hors chemin de prediction.
- E065-E074 : provider, fallback, mapping, latence, logs et secrets restent gates.
- E083-E084 : aucun betting et limites produit explicites.
