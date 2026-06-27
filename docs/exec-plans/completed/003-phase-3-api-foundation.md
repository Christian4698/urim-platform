# Phase 3 URIM API Foundation

## Objectif
Mettre en place une fondation API FastAPI versionnee, testable et securisee pour URIM/Kairos, sans logique metier avancee et sans demarrer les phases 4, 5 ou 6.

## Fichiers a modifier ou creer
- `apps/api/app/main.py`
- `apps/api/app/api/__init__.py`
- `apps/api/app/api/v1/__init__.py`
- `apps/api/app/api/v1/router.py`
- `apps/api/app/api/v1/routes/*.py`
- `apps/api/app/schemas/*.py`
- `apps/api/app/core/constants.py`
- `apps/api/app/core/security.py`
- `apps/api/app/db/models.py`
- `apps/api/app/db/session.py`
- `apps/api/tests/*.py`
- `apps/api/README.md`
- `docs/21_API_AND_DATABASE_SPEC.md`

## Hors-portee
- Aucun connecteur API-Football.
- Aucun bookmaker.
- Aucune mise reelle.
- Aucun modele ML.
- Aucune prediction reelle.
- Aucun seed de production.
- Aucun faux resultat sportif de production.
- Aucune auth complete, RBAC complet ou politique RLS complete.
- Aucune migration de schema attendue pour la Phase 3.

## Corrections Phase 2 mineures
- M1 : aligner les noms des contraintes CHECK SQLAlchemy avec la migration Phase 2 deja appliquee, sans modifier cette migration.
- M2 : refactoriser `get_db()` pour reutiliser un moteur SQLAlchemy singleton par `DATABASE_URL`.
- M3 : documenter que le futur Post-Match Learning apprend uniquement depuis `post_match_outcomes`, jamais depuis les champs declares par utilisateur dans `tickets`.

## Implementation Phase 3
- Ajouter un routeur versionne `/api/v1`.
- Conserver les endpoints racine `/health`, `/version` et `/readiness` pour compatibilite.
- Ajouter `GET /api/v1/system/capabilities`.
- Ajouter des endpoints skeleton read-only pour fixtures, predictions, tickets, providers et post-match outcomes.
- Retourner uniquement des metadonnees, collections vides et statuts explicites disabled/internal.
- Ajouter des schemas Pydantic communs pour metadata, reponse standard, erreur standard, pagination et capabilities.
- Ajouter des headers de securite minimaux : `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`.

## Tests attendus
- Tests health, version, readiness en Phase 3.
- Tests capabilities : providers, bookmakers, ML, live, vraie mise, prediction creation et production mocks restent desactives.
- Tests skeleton endpoints : GET autorises, POST dangereux absents ou 405.
- Tests Bet Center virtuel/interne.
- Tests session DB : moteur reutilise pour la meme URL, recree si l'URL change, erreur seulement lorsqu'une vraie session est demandee sans `DATABASE_URL`.
- Tests metadata : contraintes CHECK attendues avec noms `ck_*`.
- Tests Phase 2 existants append-only et temporalite conserves.

## Strategie de validation
Depuis `apps/api` :
- `pip install -e ".[dev]"`
- `ruff check .`
- `pytest`
- `DATABASE_URL=postgresql+psycopg://urim:urim_local_only@localhost:5432/urim_local alembic check`
- `git status --short --branch`

## Risques E001-E084 concernes
Phase 3 encadre surtout E001-E005, E026, E049, E066-E074, E079, E083 et E084.

## Notes de securite et temporalite
- La Phase 3 ne produit aucune prediction et ne lit aucun futur `available_at`.
- Les protections append-only et temporalite Phase 2 restent intactes.
- Les endpoints degradent vers des etats disabled/internal au lieu de fabriquer des donnees.
- Aucun secret fournisseur ne doit etre ajoute au code, aux logs ou au frontend.
