# Phase 32 API-Football Fixture Real Smoke Evidence And Compact Output

## Objectif
Documenter la preuve public-safe du premier vrai smoke local API-Football `/fixtures` et durcir la sortie Phase 31
pour ne plus exposer la liste des fixtures normalisees.

## Scope
- Ajouter la documentation Phase 32 avec uniquement le resultat compact safe fourni par l'operateur.
- Conserver la normalisation interne Phase 28 dans le script Phase 31.
- Retirer `fixtures` de la sortie publique Phase 31.
- Conserver seulement `request_query`, `normalized_count`, `payload_hash`, `payload_top_level_keys` et les flags safe.
- Ajouter des tests documentaires et de contrat compact.
- Mettre a jour l'index documentaire et la documentation Phase 31 devenue compacte.

## Hors scope
- Aucun nouvel appel API-Football reel et aucune consommation de quota.
- Aucune cle reelle, URL provider brute, payload provider brut ou liste complete de fixtures dans Git.
- Aucun endpoint public, runtime API, pyproject, README, frontend, scheduler, queue, webhook ou job.
- Aucune ecriture DB, migration Alembic, modele DB, ingestion, prediction, ML, odds, bookmaker, stake ou betting.
- Aucune reintroduction de `apps/web/lib/integrations`, `_references/public-apis` ou `docs/api-catalog.md`.

## Regles de securite
- Le resultat Phase 31 fourni par l'operateur est la seule preuve safe a documenter.
- Les noms d'equipes reelles ne sont pas documentes; ils ne peuvent apparaitre que dans des tests negatifs.
- La sortie compacte refuse les champs individuels comme fixture ID, equipes et scores.
- Les sorties restent `db_writes=false`, `prediction_created=false` et `betting_created=false`.

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

Ajouter un `git grep` cible sur les fichiers Phase 32 et le script Phase 31 pour verifier l'absence de secrets, URL
provider brute, payload brut, liste de fixtures, champs individuels et flags d'activation.

## Risques couverts
- E001-E005 : la preuve reste hash/top-level keys et n'expose pas de donnees provider detaillees.
- E026 : aucune prediction forcee ou decision utilisateur n'est creee.
- E037-E039 : odds, lineups, statistiques avancees et evenements restent hors activation.
- E065-E074 : provider, fallback, mapping, latence, logs, valeurs manquantes et secrets restent gates.
- E083-E084 : aucun betting et limites produit explicites.
