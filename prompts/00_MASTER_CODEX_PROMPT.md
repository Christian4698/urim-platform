# Prompt maître à envoyer à Codex

Tu travailles dans un dépôt destiné à créer `URIM`, une application d’intelligence et d’analyse prédictive sportive reposant exclusivement sur des données réelles en production. Son cerveau analytique est `Kairos`.

## Première obligation
Avant d’écrire du code :
1. Lis `AGENTS.md`.
2. Lis `docs/index.md` et les documents obligatoires.
3. Charge les skills pertinents sous `.agents/skills/`.
4. Résume les contraintes non négociables.
5. Audite l’état du dépôt.
6. Crée un plan dans `docs/exec-plans/active/`.
7. Indique les outils et extensions nécessaires. Pour la phase documentaire, précise qu’aucune extension supplémentaire n’est obligatoire.

## But
Créer `URIM` avec :
- `Kairos` comme moteur pré-match ;
- `Half Goals Intelligence Engine` comme cœur produit principal ;
- `HALF_GOAL_DOMINANCE` comme marché principal, avec `FIRST_HALF_MORE_GOALS`, `SECOND_HALF_MORE_GOALS` et `EQUAL_HALF_GOALS` calculés ensemble et normalisés à 100 % ;
- plus tard un moteur live séparé ;
- une couche multi-fournisseurs dynamique ;
- une base canonique avec provenance par champ ;
- un feature store temporel ;
- des modèles probabilistes calibrés ;
- `Kairos Stake Guard` et un `NO_BET Engine` ;
- le statut d'interface `Kairos éveillé` uniquement quand `Kairos Stake Guard` retourne `KAIROS_AWAKENED` ;
- des fourchettes prudentes `stake_interval_cdf` en `CDF`, jamais des mises fixes ;
- un ledger immuable ;
- une API ;
- `URIM Dashboard` ;
- `Bet Center` ;
- une messagerie entre agents spécialisés.

Les marchés 1X2, totaux de buts, Both Teams To Score, score exact, corners, fautes et cartons restent secondaires tant qu'ils ne renforcent pas le cœur `HALF_GOAL_DOMINANCE`.

## Contraintes absolues
- Pas de donnée illustrative en production.
- Pas de fallback silencieux vers un mock.
- Pas de clé API dans frontend, logs ou Git.
- Pas de données futures.
- Pas de split aléatoire pour l’évaluation temporelle.
- Pas de modification rétroactive.
- Pas de garantie de 80 %, score exact ou gain.
- Pas de recommandation forcée.
- Pas d’exécution de paris dans le MVP.
- Pas de martingale.
- Pas de récupération des pertes.
- Pas de calcul de mise fondé uniquement sur la probabilité.
- Missing reste missing.
- Toute source réelle est horodatée et traçable.
- Distinguer probabilité et confiance : une probabilité élevée n'est pas une garantie, et un `confidence_score` faible peut déclencher `NO_BET`.
- Afficher les montants en `CDF` sous forme d'intervalles prudents, jamais comme ordre fixe.

## Phases
1. Gouvernance et contrats.
2. Base et migrations.
3. SDK connecteurs.
4. Premier connecteur réel.
5. Second connecteur et réconciliation.
6. Snapshots temporels.
7. Baselines `Half Goals Intelligence Engine` et walk-forward.
8. Calibration multiclasses `HALF_GOAL_DOMINANCE` et `Kairos Stake Guard`.
9. API et ledger.
10. `URIM Dashboard`, `Bet Center` et messagerie.
11. Observabilité.
12. Sécurité et release gate.

Après chaque phase :
- exécute les tests ;
- relis le diff ;
- mets les docs à jour ;
- indique les erreurs E001–E084 prévenues ;
- corrige tout bloquant avant de poursuivre.
