# Phase 23 API-Football Local Secret & Environment Preflight

## Objectif
Ajouter un controle local-only qui verifie si l'environnement local de l'operateur est pret pour un futur smoke
test API-Football manuel, sans executer ce test pendant cette phase.

## Scope
- Ajouter un script local-only de preflight.
- Ajouter une documentation operateur public-safe.
- Mettre a jour la metadata publique vers `phase-23-api-football-local-secret-env-preflight`.
- Ajouter des tests de surete couvrant secrets, absence de reseau, absence d'endpoint public et absence de chemins
  DB/prediction/betting.

## Hors scope
- Aucun appel API-Football reel.
- Aucune vraie cle ou reference fournisseur reelle.
- Aucun endpoint FastAPI, scheduler, queue ou job automatique.
- Aucune ecriture DB, migration Alembic, modele DB, ingestion, prediction, ML, bookmaker, cote, stake ou betting.
- Aucun changement frontend ou design.
- Aucun payload brut provider committe.

## Regles de securite
- Le preflight peut seulement lire des signaux locaux.
- Le resultat partageable contient des booleens et des codes generiques seulement.
- Les valeurs sensibles ne doivent jamais etre affichees, loggees, documentees ou serialisees.
- La proprete Git est une recommandation avant vrai smoke, pas un deblocage automatique de fournisseur.
- Le preflight ne remplace pas le gate d'activation provider.

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
- E005 : aucun resultat provider ne peut alimenter une prediction.
- E036 et E065 : la preparation reste locale et controlee, sans activation fournisseur.
- E074 : les secrets et references locales ne sont jamais exposes.
- E083 : aucun betting, bookmaker ou stake n'est ajoute.
- E084 : les limites du preflight sont explicites.
