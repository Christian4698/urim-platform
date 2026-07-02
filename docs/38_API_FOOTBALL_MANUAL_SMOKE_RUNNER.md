# API-Football Manual Smoke Runner

La Phase 19 ajoute un runner API-Football local/manual-only pour preparer l'execution controlee du smoke client
Phase 18 depuis le terminal ou un appel Python local.

## Resultat safe
Le runner retourne uniquement un resume public-safe :

- `status`
- `executed=false` par defaut
- `provider=api-football`
- `mode=manual_smoke_only`
- `db_writes=false`
- `prediction_created=false`
- `betting_created=false`
- `payload_hash` optionnel

Aucun payload brut provider, credential, cle, URL provider, nom de variable locale ou valeur locale sensible ne
doit apparaitre dans la sortie.

## Conditions d'execution
Le runner refuse toute execution si une des conditions suivantes manque :

- mode smoke explicitement active localement ;
- environnement non-production ;
- materiel d'authentification local present hors depot ;
- transport explicitement injecte ;
- read-only confirme ;
- non-production confirme ;
- gate final provider consulte et toujours bloque ;
- sortie validee sans secret, URL ou credential.

## Garde-fous
- Aucun endpoint FastAPI ne lance le runner.
- Aucun appel reseau n'est automatique.
- Aucun write DB, ingestion fixtures/results/stats, prediction, ML, bookmaker, cote, stake ou betting.
- Aucun secret n'est affiche, logge ou documente avec une valeur.
- Aucun fallback mock silencieux en production.

## Risques couverts
- E001-E005 : provenance et temporalite restent bloquees avant toute activation.
- E026 : aucune prediction ou decision forcee n'est creee.
- E037-E039 : aucun resultat, lineup ou statistique smoke ne peut alimenter une prediction.
- E065-E074 : provider, fallback, logs et secrets restent gates et redacted.
- E083-E084 : aucun betting reel et limites produit explicites.
