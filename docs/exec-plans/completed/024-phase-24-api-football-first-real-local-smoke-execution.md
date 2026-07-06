# Phase 24 API-Football First Real Local Smoke Execution

## Objectif
Ajouter un script local-only capable de lancer plus tard un premier smoke test API-Football reel depuis le terminal
local, sans executer ce smoke dans les tests automatises.

## Scope
- Ajouter un script terminal-only qui reutilise le preflight Phase 23 et le harnais Phase 21.
- Ajouter une documentation operateur public-safe.
- Mettre a jour la metadata publique vers `phase-24-api-football-first-real-local-smoke-execution`.
- Ajouter des tests avec fake callable uniquement.

## Hors scope
- Aucun appel API-Football reel en tests.
- Aucune vraie cle ou reference fournisseur reelle dans le repo.
- Aucun endpoint FastAPI, scheduler, queue ou job automatique.
- Aucune ecriture DB, migration Alembic, modele DB, ingestion, prediction, ML, bookmaker, cote, stake ou betting.
- Aucun changement frontend ou design.
- Aucun payload brut provider committe.

## Regles de securite
- Le script est local-only et terminal-only.
- FastAPI ne doit jamais importer le script.
- Le preflight Phase 23 doit etre ready avant toute tentative.
- `git status` clean est un gate dur pour l'execution reelle.
- Le gate final provider Phase 15 doit rester bloque/safe.
- La sortie partageable contient seulement statut, execution, provider, mode, hash optionnel, top-level keys
  optionnelles et flags no DB/no prediction/no betting.

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

## Risques couverts
- E005 : aucun payload smoke ne peut alimenter une prediction.
- E036 et E065 : le premier smoke reel reste local et controle.
- E074 : aucune valeur sensible n'est affichee.
- E083 : aucun betting, bookmaker ou stake n'est ajoute.
- E084 : les limites du script sont documentees.
