# Phase 18 API-Football Env-Gated Smoke Client

## Objectif
Preparer un smoke client API-Football strictement interne, disabled by default et active uniquement par
configuration locale explicite non committee.

## Scope
- Ajouter un module smoke client interne avec transport injectable.
- Exposer uniquement un statut public safe dans `GET /api/v1/providers/readiness`.
- Garder Phase 15, Phase 16 et Phase 17 bloquees.
- Ajouter tests de non-reseau, redaction, refus par defaut et absence d'effets DB/prediction/betting.
- Mettre a jour la documentation Phase 18.

## Hors scope
- Pas d'activation API-Football par defaut.
- Pas de vrai appel HTTP dans les tests.
- Pas de vraie cle API, URL provider publique, `.env.example`, Alembic, modele DB, ingestion, prediction, ML,
  bookmaker, betting, frontend ou design.

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
