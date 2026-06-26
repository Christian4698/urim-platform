# Plan actif — Half Goals Intelligence Engine

Date : 2026-06-26
Statut : actif
Portée : spécifications documentaires et skill local
Produit : `URIM`
Cerveau analytique : `Kairos`
Module principal : `Half Goals Intelligence Engine`

## Objectif
Faire du `Half Goals Intelligence Engine` le cœur produit de `URIM`, avec le marché principal `HALF_GOAL_DOMINANCE`.

Le marché principal doit toujours produire ensemble :
- `FIRST_HALF_MORE_GOALS`
- `SECOND_HALF_MORE_GOALS`
- `EQUAL_HALF_GOALS`

Les trois probabilités doivent être normalisées ensemble et totaliser 100 % après normalisation.

## Contraintes
- Ne pas créer de connecteur API réel.
- Ne pas promettre de taux de réussite garanti.
- Ne jamais présenter de données fictives comme données réelles en production.
- Ne pas supprimer les autres marchés ; les rendre secondaires.
- Distinguer clairement probabilité et confiance.
- Préserver `NO_BET`, `INSUFFICIENT_DATA`, temporal guard, provenance et ledger immuable.

## Fichiers à créer ou modifier
- Créer `docs/29_HALF_GOALS_INTELLIGENCE_ENGINE.md`.
- Mettre à jour `docs/index.md`.
- Mettre à jour `docs/01_PRODUCT_SPEC.md`.
- Mettre à jour `docs/10_MODELING_SPEC.md`.
- Mettre à jour `docs/12_CALIBRATION_AND_EVALUATION.md`.
- Mettre à jour `docs/13_NO_BET_AND_RISK_ENGINE.md`.
- Créer `.agents/skills/half-goals-intelligence/SKILL.md`.
- Mettre à jour `prompts/00_MASTER_CODEX_PROMPT.md`.

## Contenu attendu
- Définition de `HALF_GOAL_DOMINANCE`.
- Sorties attendues et exemples JSON.
- Données nécessaires et features spécifiques.
- Méthodes statistiques : Poisson ou Negative Binomial par mi-temps.
- Distribution de différence de buts entre première et deuxième mi-temps.
- Permutations possibles, simulation Monte Carlo et normalisation.
- Calibration spécifique aux trois classes.
- Confidence score séparé de la probabilité.
- Reason codes.
- Règles `NO_BET`.
- Limites du modèle.

## Erreurs E001–E084 à surveiller
- E001–E004 : qualité, complétude et multi-source.
- E005, E029–E031, E037–E039 : fuite temporelle et `as_of`.
- E013–E028 : robustesse modèle, surapprentissage, incertitude, absence de `NO_BET`.
- E041–E049 : calibration, métriques probabilistes, comparaison marché.
- E053–E062 : confusion entre taux de réussite, valeur et risque financier.
- E067–E069 : immutabilité, versionnement et reproductibilité.
- E075–E084 : langage produit responsable et limites.

## Validation
- Rechercher les références `HALF_GOAL_DOMINANCE` et `Half Goals Intelligence Engine`.
- Vérifier que les trois classes sont citées ensemble.
- Vérifier qu'aucun connecteur réel, secret ou promesse de performance n'a été ajouté.
- Vérifier le diff documentaire avant le rapport final.
