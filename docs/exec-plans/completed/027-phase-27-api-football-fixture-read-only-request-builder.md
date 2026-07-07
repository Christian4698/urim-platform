# Phase 27 API-Football Fixture Read-Only Request Builder

## Objectif
Ajouter un builder backend local pour preparer des requetes conceptuelles API-Football `/fixtures` en lecture seule,
avec validation stricte des parametres autorises, sans appel HTTP, quota, secret, DB, prediction ou betting.

## Scope
- Ajouter un module backend local et type pour construire un objet public-safe de requete `/fixtures`.
- Valider uniquement les parametres `league`, `season`, `team`, `date`, `from`, `to`, `timezone` et `status`.
- Conserver un ordre deterministe des parametres dans la sortie.
- Refuser les parametres inconnus et les parametres interdits lies aux odds, bookmakers, stakes, predictions et betting.
- Ajouter des tests unitaires statiques sans socket, provider, DB ou runtime API.
- Ajouter la documentation Phase 27 et la reference dans l'index documentaire.

## Hors scope
- Aucun appel API-Football reel et aucune consommation de quota.
- Aucune cle, credential, endpoint provider complet, en-tete d'authentification ou payload provider brut.
- Aucun endpoint public, runtime API, pyproject, README, frontend, scheduler, queue, webhook ou job.
- Aucune ecriture DB, migration Alembic, modele DB, ingestion, prediction, ML, odds, bookmaker, stake ou betting.
- Aucune reintroduction de `apps/web/lib/integrations`, `_references/public-apis` ou `docs/api-catalog.md`.

## Regles de securite
- Le builder retourne seulement un resume public-safe et ne construit pas d'URL provider.
- Les parametres numeriques doivent rester de vrais entiers et les dates doivent etre calendaires.
- La phase ne cree aucune source de verite provider ni contrat de stockage.
- Le resultat indique explicitement `db_writes=false`, `prediction_requested=false` et `betting_requested=false`.

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

Ajouter un scan cible des nouveaux fichiers Phase 27 pour verifier l'absence de secrets, URLs provider, marqueurs de
payload brut et flags d'activation DB/prediction/betting.

## Risques couverts
- E001-E005 : la source provider reste non activee et ne peut pas introduire de fuite temporelle.
- E026 : aucune prediction forcee ou decision utilisateur n'est creee.
- E037-E039 : odds, statistiques avancees et evenements restent hors activation.
- E065-E074 : provider, fallback, mapping, latence, logs et secrets restent gates.
- E083-E084 : aucun betting et limites produit explicites.
