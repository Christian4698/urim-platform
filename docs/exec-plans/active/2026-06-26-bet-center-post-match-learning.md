# Plan actif — Bet Center et Post-Match Learning Engine

Date : 2026-06-26
Statut : actif
Portée : spécifications documentaires et skills locaux
Produit : `URIM`
Moteur analytique : `Kairos`
Interface : `Bet Center`
Module d'apprentissage : `Post-Match Learning Engine`

## Objectif
Spécifier le `Bet Center` de `URIM` comme interface de budget hebdomadaire, bankroll virtuelle, tickets, performances et retour utilisateur, ainsi que le `Post-Match Learning Engine` comme moteur d'apprentissage fondé sur des résultats officiels vérifiés.

## Contraintes
- Ne jamais connecter le `Bet Center` à un compte bookmaker dans le MVP.
- Ne jamais exécuter une mise réelle.
- Ne jamais promettre un gain.
- Ne jamais utiliser la martingale.
- Ne jamais recommander de récupérer les pertes.
- Ne jamais apprendre directement depuis une déclaration utilisateur non vérifiée.
- Ne jamais modifier rétroactivement une prédiction `Kairos`.
- Retourner `NO_BET` ou `INSUFFICIENT_DATA` si la qualité des données est insuffisante.
- Afficher les montants en `CDF`.
- Afficher des intervalles prudents, jamais des ordres fixes.

## Fichiers à créer
- `docs/36_BET_CENTER_SPEC.md`
- `docs/37_POST_MATCH_LEARNING_ENGINE.md`
- `.agents/skills/bet-center/SKILL.md`
- `.agents/skills/post-match-learning/SKILL.md`
- `.claude/skills/bet-center/SKILL.md`
- `.claude/skills/post-match-learning/SKILL.md`

## Fichiers à mettre à jour
- `docs/index.md`
- `docs/01_PRODUCT_SPEC.md`
- `docs/13_NO_BET_AND_RISK_ENGINE.md`
- `docs/15_ODDS_AND_VALUE.md`
- `docs/22_RESPONSIBLE_USE.md`
- `docs/23_FAILURE_CATALOG_84.md`
- `docs/35_KAIROS_STAKE_GUARD.md`
- `prompts/00_MASTER_CODEX_PROMPT.md`
- `KIT_TREE.md`
- `CLAUDE.md`

## Décisions retenues
- Langue principale : français.
- Langue secondaire optionnelle : anglais.
- Locale par défaut : `fr-CD`.
- Devise par défaut : `CDF`.
- `Bet Center` enregistre un budget betting hebdomadaire utilisateur et un solde virtuel interne `URIM`.
- Les tickets recommandés sont limités à 5 matchs maximum.
- Les sélections ajoutées par l'utilisateur sont autorisées mais marquées `USER_UNVALIDATED`.
- Les résultats utilisateur `gagné`, `perdu`, `annulé`, `remboursé` n'alimentent pas directement l'apprentissage sans vérification officielle.
- Le plafond de 5 matchs maximum doit remplacer le plafond documentaire précédent de 3 rencontres recommandé afin de garder une seule règle produit cohérente.

## Validation
- Rechercher `Bet Center`, `bankroll_cdf`, `weekly_budget_cdf`, `stake_interval_cdf`, `USER_UNVALIDATED`, `won/lost/void/refunded`, `profit_net`, `ROI`, `official_result`, `Post-Match Learning Engine`.
- Vérifier qu'aucun langage de garantie, martingale ou récupération des pertes n'est introduit comme conseil.
- Vérifier que `Kairos Stake Guard` et `Bet Center` utilisent le même plafond de tickets recommandé.
- Exécuter `git diff --check`.
- Valider les skills si l'environnement Python dispose de `yaml`; sinon vérifier manuellement le frontmatter.

## Erreurs E001–E084 concernées
- E026 : absence de `NO_BET`.
- E041–E062 : valeur, ROI, cotes, exposition et risque financier.
- E051, E067–E069, E078, E079 : historique, immutabilité, auditabilité et non-réécriture.
- E055–E059 : martingale, surmise, exposition, corrélation et Kelly.
- E075–E084 : langage responsable, limites et avertissements.
