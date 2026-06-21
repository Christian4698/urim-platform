# Prompt maître à envoyer à Codex

Tu travailles dans un dépôt destiné à créer un bot d’intelligence et d’analyse prédictive sportive reposant exclusivement sur des données réelles en production.

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
Créer :
- un moteur pré-match ;
- plus tard un moteur live séparé ;
- une couche multi-fournisseurs dynamique ;
- une base canonique avec provenance par champ ;
- un feature store temporel ;
- des modèles probabilistes calibrés ;
- un moteur NO_BET ;
- un ledger immuable ;
- une API ;
- un dashboard ;
- une messagerie entre agents spécialisés.

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
- Missing reste missing.
- Toute source réelle est horodatée et traçable.

## Phases
1. Gouvernance et contrats.
2. Base et migrations.
3. SDK connecteurs.
4. Premier connecteur réel.
5. Second connecteur et réconciliation.
6. Snapshots temporels.
7. Baselines et walk-forward.
8. Calibration et NO_BET.
9. API et ledger.
10. Dashboard et messagerie.
11. Observabilité.
12. Sécurité et release gate.

Après chaque phase :
- exécute les tests ;
- relis le diff ;
- mets les docs à jour ;
- indique les erreurs E001–E084 prévenues ;
- corrige tout bloquant avant de poursuivre.
