# Plan actif — Phase 2 : Architecture, Skills et Garde-fous

Date : 2026-06-26
Statut : actif
Produit : `URIM`
Objectif : Finaliser la partie documentaire et les garde-fous avant le début du coding

## Contexte

La Phase 1 documentaire est terminée :
- Modules spécialisés : `Half Goals Intelligence Engine`, `Kairos Stake Guard`, `Bet Center`, `Post-Match Learning Engine`
- 16 skills synchronisés `.agents/` ↔ `.claude/`
- Schémas canoniques, contrats de prédiction et d'observation validés
- Catalogue 84 erreurs, CI de base (5 jobs)

La Phase 2 finalise la fondation technique avant le coding :
- Architecture enrichie avec choix de stack et contrats de modules
- Garde-fous concrets et bloquants (temporal gate, CI renforcée)
- Docs d'implémentation prêts (API, DB, tests, sécurité, setup)
- Skills vérifiés et coding-ready

## Contraintes

- Aucun connecteur réel
- Aucun secret dans le dépôt
- Aucune mise réelle dans le MVP
- Toutes les règles temporelles, NO_BET et ledger immuable préservées

## Fichiers à créer ou modifier

### Créer
- `docs/38_DEV_SETUP.md` — stack local, Docker Compose, variables d'environnement, commandes

### Enrichir significativement
- `docs/03_SYSTEM_ARCHITECTURE.md` — tech stack confirmé, contrats inter-modules, env config
- `docs/07_TEMPORAL_INTEGRITY.md` — patterns de tests concrets, exemples de code
- `docs/17_SECURITY.md` — checklist implémentation, exemples de garde-fous
- `docs/20_TESTING_STRATEGY.md` — pyramide avec commandes, répertoires, mapping E001–E084
- `docs/21_API_AND_DATABASE_SPEC.md` — schémas de tables détaillés, formats de champs

### Renforcer
- `.github/workflows/ci.yml` — gate temporel bloquant, scan dépendances, linting

### Mettre à jour
- `docs/index.md`
- `KIT_TREE.md`

## Stack technique retenu

| Composant | Choix |
|---|---|
| Backend API | FastAPI (Python 3.12+) |
| Frontend | Next.js 14 (App Router) |
| Base de données | PostgreSQL 16 + TimescaleDB |
| Cache / file | Redis 7 |
| Worker / tâches | Celery + Redis broker |
| Migrations | Alembic |
| Tests | pytest + pytest-asyncio |
| Linting | ruff + mypy |
| Conteneurisation | Docker + Docker Compose |
| CI | GitHub Actions |
| Secret manager | Vault ou GCP Secret Manager (à confirmer) |

## Erreurs E001–E084 concernées

- E005, E029–E031, E037–E039 : temporal gate bloquant dans CI
- E074 : secret scan CI
- E026 : NO_BET gate dans tests de contrat
- E067–E069 : ledger immuable dans schéma DB
- E071 : missing distinct de zéro dans schémas

## Validation

- Temporal gate CI doit échouer si un test futur est détecté
- Docs/21 doit permettre d'écrire les migrations sans ambiguïté
- Docs/38 doit permettre de lancer l'environnement local en < 10 commandes
- Tous les skills doivent pointer vers les bons docs
