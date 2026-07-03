# Phase 20 API-Football Local Smoke Execution Guide & Safety Checklist

## Objectif
Preparer une documentation operateur et une checklist de securite pour une future execution locale controlee du
smoke test API-Football.

## Scope
- Documenter le caractere local-only du smoke test.
- Documenter les controles avant et apres execution.
- Rappeler que la cle reste hors Git, hors prompt, hors `.env.example`, hors logs et hors reponses publiques.
- Confirmer absence d'endpoint public, d'ingestion DB, de prediction, de bookmaker et de betting.

## Hors scope
- Aucun appel API-Football reel.
- Aucune vraie cle API ou vraie URL provider.
- Aucun endpoint FastAPI.
- Aucun changement Alembic, modele DB, ingestion, prediction, ML, bookmaker, betting, frontend ou design.

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
