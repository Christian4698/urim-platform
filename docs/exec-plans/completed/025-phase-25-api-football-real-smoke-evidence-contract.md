# Phase 25 API-Football Real Smoke Evidence Contract

## Objectif
Figer la preuve public-safe du premier smoke local reel API-Football et formaliser le contrat de reponse autorise
sans activer d'ingestion DB, de prediction, de betting ou de surface publique.

## Scope
- Ajouter `docs/44_API_FOOTBALL_REAL_SMOKE_EVIDENCE_AND_SAFE_RESPONSE_CONTRACT.md`.
- Referencer la Phase 25 dans `docs/index.md`.
- Ajouter un test documentaire statique pour verifier la preuve safe, le contrat autorise et les interdictions.
- Conserver la metadata runtime en Phase 24, car Phase 25 est documentaire et contractuelle uniquement.

## Hors scope
- Aucun appel API-Football reel.
- Aucune vraie cle, credential, reference provider brute, URL provider ou payload brut.
- Aucun endpoint public, scheduler, queue, webhook ou job automatique.
- Aucune ecriture DB, migration Alembic, modele DB, ingestion, prediction, ML, cote, bookmaker, stake ou betting.
- Aucun changement frontend, `.env`, `.env.example`, `apps/web/lib/integrations`, `_references/public-apis` ou
  `docs/api-catalog.md`.

## Regles de securite
- Le hash et les top-level keys sont les seules preuves de payload autorisees.
- La sortie safe autorisee contient uniquement `status`, `executed`, `provider`, `mode`, `payload_hash`,
  `payload_top_level_keys`, `db_writes`, `prediction_created` et `betting_created`.
- Les flags `db_writes=false`, `prediction_created=false` et `betting_created=false` restent obligatoires.
- Les tests restent statiques et ne doivent ouvrir aucun socket ni executer de script smoke.

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

## Risques couverts
- E005 : aucune information provider ne peut alimenter une prediction passee.
- E036 et E065 : le smoke reel reste une preuve locale limitee, pas une activation fournisseur.
- E074 : aucune cle, credential, URL ou reference brute n'est documentee.
- E083 : aucun betting, bookmaker ou stake n'est ajoute.
- E084 : les limites et interdictions de Phase 25 sont explicites.
