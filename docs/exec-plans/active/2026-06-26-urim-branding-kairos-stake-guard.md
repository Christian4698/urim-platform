# Plan actif — URIM Branding, Kairos Engine et Kairos Stake Guard

Date : 2026-06-26
Statut : actif
Portée : spécifications documentaires et skills locaux
Produit : `URIM`
Moteur analytique : `Kairos`
Module prudent : `Kairos Stake Guard`

## Objectif
Formaliser le branding `URIM`, le moteur `Kairos`, le statut d'interface `Kairos éveillé` et les intervalles prudents de mise en `CDF`, sans ajouter de connecteur réel ni de logique métier exécutable.

## Contraintes
- Ne jamais promettre un gain.
- Ne jamais présenter une mise comme garantie.
- Ne jamais utiliser la martingale.
- Ne jamais conseiller de récupérer les pertes.
- Ne jamais dépasser les limites de risque définies.
- Ne jamais calculer une mise uniquement avec la probabilité.
- Retourner `NO_BET` ou `INSUFFICIENT_DATA` si les données sont insuffisantes.
- Afficher les montants en intervalles `CDF`, jamais comme ordre fixe.
- Conserver l'interdiction d'exécuter une mise réelle dans le MVP.

## Fichiers à créer
- `docs/34_URIM_BRANDING_AND_KAIROS_ENGINE.md`
- `docs/35_KAIROS_STAKE_GUARD.md`
- `.agents/skills/kairos-stake-guard/SKILL.md`
- `.claude/skills/kairos-stake-guard/SKILL.md`

## Fichiers à mettre à jour
- `docs/index.md`
- `docs/01_PRODUCT_SPEC.md`
- `docs/13_NO_BET_AND_RISK_ENGINE.md`
- `docs/15_ODDS_AND_VALUE.md`
- `docs/22_RESPONSIBLE_USE.md`
- `prompts/00_MASTER_CODEX_PROMPT.md`
- `KIT_TREE.md`
- `CLAUDE.md`

## Décisions retenues
- `bankroll_cdf` est un budget utilisateur explicitement déclaré pour l'analyse `URIM`.
- `stake_interval_cdf` est calculé comme intervalle de pourcentage du bankroll, puis affiché en `CDF`.
- Plafond par match : `0.5 %` du bankroll.
- Exposition journalière maximale : `1.0 %` du bankroll.
- Nombre maximal de rencontres recommandé : 3 par jour.
- Fourchette prudente initiale en statut `KAIROS_AWAKENED` : `0.10 %` à `0.30 %` du bankroll.
- `Kairos éveillé` est un statut d'interface, pas une promesse de résultat.

## Validation
- Rechercher `URIM`, `Kairos`, `Kairos éveillé`, `Kairos Stake Guard`, `CDF`, `bankroll_cdf`, `stake_interval_cdf`, `NO_BET`, `martingale` et `surmise`.
- Vérifier qu'aucun langage de garantie ou de récupération des pertes n'est ajouté comme recommandation.
- Exécuter `git diff --check`.
- Valider les skills si l'environnement Python dispose de `yaml`; sinon vérifier le frontmatter manuellement.

## Erreurs E001–E084 concernées
- E026 : absence de `NO_BET`.
- E041–E062 : métriques, valeur, cote et risque financier.
- E055–E059 : martingale, surmise, exposition et Kelly.
- E067–E069 : immutabilité et versionnement des sorties publiées.
- E075–E084 : langage responsable, limites et absence de garanties.
