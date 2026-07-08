# Phase 34 Fixture Ingestion Readiness Plan

## Objectif
Documenter la readiness requise avant toute future ingestion staging des fixtures API-Football, sans activer de DB,
de migration, de modele, d'endpoint, de prediction ou de betting.

## Scope
- Ajouter `docs/53_FIXTURE_INGESTION_READINESS_PLAN.md`.
- Documenter les champs candidats issus des contrats Phase 28/32.
- Documenter idempotence, deduplication, `payload_hash`, `provider_fixture_id`, audit trail, fraicheur, rollback,
  quota et statuts `postponed`, `cancelled`, `live`.
- Ajouter des tests textuels qui valident la presence des garde-fous et l'absence de contenu provider sensible.
- Mettre a jour `docs/index.md`.

## Hors scope
- Aucun vrai appel API-Football et aucune consommation de quota.
- Aucune ecriture DB, migration Alembic, modele SQLAlchemy, endpoint public, frontend, service d'ingestion ou runner.
- Aucune prediction, ML, odds, bookmaker, stake ou action betting.
- Aucune vraie cle API, payload provider brut, liste reelle de fixtures ou noms d'equipes du smoke precedent.
- Aucune reintroduction de `apps/web/lib/integrations`, `_references/public-apis` ou `docs/api-catalog.md`.

## Regles de securite
- Phase 34 est documentaire/contractuelle uniquement.
- Les tests inspectent les fichiers comme texte et n'executent aucun runner.
- La future Phase 35 reste bloquee tant que provenance, temporalite, idempotence, rollback, quotas et revue securite ne
  sont pas approuves.

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

Verifier aussi que `apps/web/lib/integrations`, `_references/public-apis` et `docs/api-catalog.md` ne sont pas
reintroduits.

## Risques couverts
- E001-E005 : completude, provenance, deduplication, freshness et temporalite sont gates.
- E026 : aucune prediction forcee ou decision utilisateur n'est creee.
- E037-E039 : odds, lineups, statistiques avancees et information future restent hors activation.
- E065-E074 : provider, quotas, latence, fallback, mapping, logs et secrets restent gates.
- E083-E084 : aucune action betting et limites produit explicites.
