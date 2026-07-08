# Phase 35 Fixture Staging DB Schema

## Objectif
Ajouter le schema DB staging `api_football_fixture_staging` pour de futures fixtures normalisees API-Football, sans
ingestion runtime, sans endpoint public, sans nouvel appel provider, sans prediction et sans betting.

## Scope
- Ajouter une migration Alembic controlee apres `202606260001`.
- Ajouter la table SQLAlchemy Core correspondante dans `app/db/models.py`.
- Utiliser les champs Phase 34/prompt uniquement; `available_at`, `source_version` et `quality_flags` restent pour la
  Phase 36 ingestion gate.
- Ajouter tests statiques/metadata pour migration, table, contraintes, indexes, doc et garde-fous.
- Ajouter `docs/54_FIXTURE_STAGING_DB_SCHEMA.md` et l'entree d'index.

## Hors scope
- Aucun appel API-Football, aucune consommation de quota, aucune cle API et aucun payload provider brut.
- Aucune insertion de fixtures, logique d'ingestion, upsert, job, scheduler ou runner.
- Aucun endpoint public, frontend, prediction, ML, odds, bookmaker, stake ou betting.
- Aucune reintroduction de `apps/web/lib/integrations`, `_references/public-apis` ou `docs/api-catalog.md`.

## Regles de schema
- `provider`, `provider_fixture_id`, `payload_hash`, `fetched_at` et `source_mode` sont non nuls.
- `payload_hash` est non nul car chaque future ligne staging doit rester reliee a une preuve compacte hashable.
- `payload_top_level_keys` est JSONB avec defaut `[]`; aucun champ `raw_payload` n'est ajoute.
- Contrainte unique sur `(provider, provider_fixture_id)`.
- Index sur `provider_fixture_id`, `fixture_date`, `(provider_league_id, provider_season)` et
  `fixture_status_short`.

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

Verifier aussi que les chemins interdits ne sont pas reintroduits.

## Risques couverts
- E001-E005 : schema staging traceable, sans ingestion ni usage prediction.
- E026 : aucune prediction forcee ou decision utilisateur n'est creee.
- E037-E039 : odds, lineups avancees et information future restent hors activation.
- E065-E074 : provider, quotas, latence, logs et secrets restent gates.
- E083-E084 : aucune action betting et limites produit explicites.
