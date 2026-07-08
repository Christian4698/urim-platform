# Phase 33 API-Football Fixture Compact Smoke Runner

## Objectif
Ajouter un runner PowerShell local-only pour lancer le smoke API-Football `/fixtures` compact Phase 31/32 de facon
controlee, sans nouvel appel automatisable dans les tests et sans exposer de secret.

## Scope
- Ajouter `apps/api/scripts/run_fixture_first_real_local_smoke.ps1`.
- Lire la cle locale depuis le presse-papiers ou via prompt masque.
- Definir temporairement les gates locales fixture, dont `APP_ENV=development`, read-only, non-prod, no DB, no prediction
  et no betting.
- Utiliser `-SmokeDate` avec le defaut controle `2026-07-07` et `Africa/Kinshasa`.
- Executer uniquement `python .\scripts\api_football_fixture_first_real_local_smoke.py`.
- Ajouter des tests textuels du runner et de la documentation Phase 33.
- Ajouter `docs/52_API_FOOTBALL_FIXTURE_COMPACT_SMOKE_RUNNER.md` et l'entree d'index.

## Hors scope
- Aucun appel API-Football pendant les tests ou validations.
- Aucune cle reelle, payload provider brut, ingestion DB, modele DB, migration Alembic, endpoint public ou frontend.
- Aucune prediction, ML, odds, bookmaker, stake ou action betting.
- Aucune reintroduction de `apps/web/lib/integrations`, `_references/public-apis` ou `docs/api-catalog.md`.
- Aucun commit automatique.

## Regles de securite
- Le runner annonce son caractere local-only sans afficher la cle, l'URL provider ou le contenu provider.
- Le runner restaure les variables non sensibles et supprime toujours `URIM_API_FOOTBALL_FIXTURE_SMOKE_AUTH`.
- Le presse-papiers est nettoye dans un `finally`.
- Les tests inspectent le PowerShell comme texte et ne lancent jamais le runner.

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

Ne pas lancer `run_fixture_first_real_local_smoke.ps1` pendant la validation.

## Risques couverts
- E001-E005 : smoke local minimal, compact et non ingere.
- E026 : aucune prediction forcee ou decision utilisateur n'est creee.
- E037-E039 : odds, lineups avancees et statistiques restent hors activation.
- E065-E074 : provider, quotas, logs, valeurs manquantes et secrets restent gates.
- E083-E084 : aucune action betting et limites produit explicites.
