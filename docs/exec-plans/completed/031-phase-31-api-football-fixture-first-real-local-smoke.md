# Phase 31 API-Football Fixture First Real Local Smoke

## Objectif
Ajouter l'execution locale controlee du premier vrai smoke API-Football `/fixtures`, capable d'un seul appel GET
manuel uniquement si toutes les confirmations Phase 30, la cle locale et la reference locale sont presentes.

## Scope
- Verifier le protocole Phase 30 avant toute tentative.
- Exiger une cle API locale fournie par variable d'environnement et ne jamais l'afficher.
- Exiger une reference locale de l'endpoint `/fixtures` et ne jamais l'afficher.
- Construire la query minimale `date` + `timezone`.
- Effectuer un seul GET controle avec le header autorise `x-apisports-key`.
- Normaliser la reponse via le normalizer Phase 28.
- Retourner uniquement un JSON public-safe avec hash, top-level keys, fixtures normalisees et flags safe.
- Ajouter des tests avec transport fake/monkeypatch, sans appel API reel.
- Ajouter la documentation Phase 31 et la reference dans l'index documentaire.

## Hors scope
- Aucun appel API-Football pendant les tests automatises.
- Aucune cle reelle, credential, payload provider brut ou URL provider dans les sorties.
- Aucun endpoint public, runtime API, pyproject, README, frontend, scheduler, queue, webhook ou job.
- Aucune ecriture DB, migration Alembic, modele DB, ingestion, prediction, ML, odds, bookmaker, stake ou betting.
- Aucune reintroduction de `apps/web/lib/integrations`, `_references/public-apis` ou `docs/api-catalog.md`.

## Regles de securite
- Le script est local-only et manuel.
- Le script refuse `APP_ENV=production`.
- Le script refuse toute execution sans protocole Phase 30 pret.
- Le script refuse l'absence de cle locale et de reference locale.
- Les erreurs provider sont converties en sortie public-safe sans stack trace ni contenu provider.

## Validation
Depuis `apps/api` :

```bash
ruff check .
pytest
python .\scripts\api_football_fixture_first_real_local_smoke.py
```

Depuis la racine :

```bash
git diff --check
git status --short --untracked-files=all
```

Ajouter un scan cible des nouveaux fichiers Phase 31 pour verifier l'absence de cle reelle, payload provider brut,
headers interdits et flags d'activation DB/prediction/betting.

## Risques couverts
- E001-E005 : l'appel reste manuel, minimal et ne produit qu'une preuve public-safe.
- E026 : aucune prediction forcee ou decision utilisateur n'est creee.
- E037-E039 : odds, lineups, statistiques avancees et evenements restent hors activation.
- E065-E074 : provider, fallback, mapping, latence, logs, valeurs manquantes et secrets restent gates.
- E083-E084 : aucun betting et limites produit explicites.
