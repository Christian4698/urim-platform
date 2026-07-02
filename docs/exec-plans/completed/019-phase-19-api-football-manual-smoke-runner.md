# Phase 19 API-Football Manual Smoke Runner

## Objectif
Preparer un runner local/manual-only pour le smoke client API-Football Phase 18, utilisable depuis le terminal ou
un appel Python local sans endpoint public.

## Scope
- Ajouter un runner local disabled by default.
- Exiger mode smoke local, read-only, non-production, auth locale, transport injecte et gate provider bloque.
- Retourner uniquement un resultat public-safe sans payload brut, cle, credential, URL provider ou nom de variable.
- Garder DB, prediction, bookmaker et betting desactives.
- Mettre a jour la documentation et les tests.

## Hors scope
- Aucun endpoint FastAPI.
- Aucun appel API-Football automatique.
- Aucun secret, `.env.example`, Alembic, modele DB, ingestion, prediction, ML, bookmaker, betting, frontend ou design.

## Validation
Depuis `apps/api` :

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

Depuis la racine :

```bash
git diff --check
```

`alembic check` reste conditionnel a un environnement DB/Docker local disponible.
