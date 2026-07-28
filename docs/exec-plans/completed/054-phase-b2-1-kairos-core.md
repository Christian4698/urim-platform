# Phase B2.1 — Kairos Core backend-only

## Objectif

Ajouter une analyse pré-match 1X2 explicable à partir des observations
API-Football déjà présentes dans PostgreSQL, sans appel fournisseur, écriture
en base, frontend, cote, bookmaker, pari ou automatisation live.

## Architecture retenue

1. Un repository Kairos construit un dataset strictement `as_of` depuis les
   tables B1 append-only.
2. Des modèles de domaine conservent chaque observation source et ses
   horodatages de provenance.
3. Un service déterministe calcule les profils récents des deux équipes sur une
   fenêtre fixe de cinq matchs terminés dans la même compétition et la même
   saison.
4. Une baseline Poisson 1X2 combine buts marqués/encaissés et modificateurs
   bornés pour la forme, le classement, domicile/extérieur, tirs, possession,
   corners et cartons.
5. Les schémas Pydantic exposent probabilités, qualité, confiance technique,
   raisons, avertissements, snapshot reproductible et restrictions produit.
6. Deux routes GET exposent la méthodologie et l’analyse d’un match. Aucune
   route mutante n’est ajoutée.

## Garde-fous

- `available_at`, `fetched_at` et `created_at` doivent être antérieurs ou égaux
  à `as_of`.
- chaque match historique doit aussi avoir `kickoff_at < as_of`, même si son
  statut fournisseur est terminé;
- Le match cible est exclu de son propre historique.
- Une analyse est refusée à partir du coup d’envoi.
- `NULL` reste manquant; zéro reste une observation valide.
- Moins de trois résultats complets par équipe produit
  `INSUFFICIENT_DATA` et des probabilités nulles.
- La confiance n’est pas une probabilité et reste plafonnée tant que la
  baseline n’est pas calibrée hors échantillon.
- La décision est toujours `NO_BET` ou `INSUFFICIENT_DATA`.
- Les appels fournisseur, bookmakers, cotes, mises, paris réels et live
  automatique restent absents.
- Les IDs HTTP, hashes, fournisseurs, valeurs numériques et volumes de lignes
  sont validés ou bornés avant calcul.

## Validation prévue

- tests unitaires du calcul et des données manquantes;
- tests adversariaux d’invariance aux observations et matchs futurs;
- tests de contrat Pydantic et de somme des probabilités;
- tests des routes GET et absence de routes mutantes;
- tests de compilation des requêtes `as_of`;
- suite API complète, Ruff, build Python;
- validation des contrats, lint, types, tests et build web;
- audit des dépendances, secrets et `git diff --check`.

## Migration

Aucune migration n’est prévue : B2.1 calcule un snapshot reproductible en
mémoire et les endpoints restent réellement en lecture seule. La persistance
append-only d’analyses publiées appartient à une phase ultérieure avec release
gate, calibration et ledger dédiés.

## Erreurs du catalogue couvertes

E001, E002, E005, E008, E009, E011, E013, E016, E021, E025, E026, E028,
E039, E042, E049, E064, E066, E069, E070, E071, E074, E075, E076, E077 et E084.

## Résultat

Statut : terminé.

- module `app/modules/kairos` créé avec modèles, repository, services et
  schémas;
- deux endpoints GET read-only ajoutés;
- aucune migration, écriture DB ou activation fournisseur ajoutée;
- revue indépendante : garde `kickoff_at < as_of`, provenance, valeurs
  aberrantes, bornes de requêtes et validation HTTP renforcées;
- `.env.example` vérifié neutre : clé, compétitions et saison vides,
  fournisseur désactivé;
- 37 tests B2.1 ciblés réussis;
- suite API : 1277 réussis, 3 tests PostgreSQL sautés faute de base jetable;
- Ruff, build Python et `pip check` réussis;
- contrats : 6 schémas validés;
- frontend : lint, types, 25 tests et build réussis;
- audit pnpm production : aucune vulnérabilité connue après mise à jour de
  PostCSS 8.5.18;
- audit Python : aucune vulnérabilité connue parmi 64 distributions après
  mise à jour locale de l'outil `pip`; `urim-api` est ignoré car paquet local
  absent de PyPI;
- `git diff --check` réussi.

## Risques restants

- calibration walk-forward et suivi du drift absents;
- fournisseur unique;
- force d'opposition, blessures pondérées, compositions et changements de
  régime non modélisés;
- tests PostgreSQL réels non exécutés sans `B1_TEST_DATABASE_URL`;
- sortie non persistée : aucun ledger officiel B2.1.
