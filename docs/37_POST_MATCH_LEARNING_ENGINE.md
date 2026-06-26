# Post-Match Learning Engine

Le `Post-Match Learning Engine` compare les prédictions `Kairos` aux résultats officiels vérifiés après le match, produit des rapports d'écart et alimente la recalibration, les listes de marchés fiables et l'amélioration du `NO_BET`.

Il n'apprend jamais directement à partir d'une simple déclaration utilisateur non vérifiée.

## Résultat utilisateur vs résultat officiel
Le système distingue :
- `user_reported_result` : ce que l'utilisateur déclare dans le `Bet Center` ;
- `official_result` : le résultat officiel issu des sources réelles vérifiées ;
- `verification_status` : état de comparaison entre les deux.

Les valeurs utilisateur servent au suivi du ticket et de l'expérience utilisateur. Les valeurs officielles servent à l'évaluation du modèle et à l'apprentissage.

## Journal immuable des prédictions
Chaque prédiction `Kairos` reste append-only :
- `prediction_id`
- `model_version`
- `feature_snapshot_id`
- `prediction_time`
- `market`
- `probabilities`
- `decision`
- `immutable_hash`

Le `Post-Match Learning Engine` ne modifie jamais rétroactivement une prédiction publiée. Il ajoute des observations post-match et des évaluations dérivées.

## Vérification post-match
Après le match :
1. récupérer les résultats officiels vérifiés ;
2. valider la cohérence entre score, statut, minutes d'événements et marché ;
3. comparer avec la prédiction publiée ;
4. comparer avec la déclaration utilisateur si elle existe ;
5. marquer `MATCH_VERIFIED`, `USER_MISMATCH`, `OFFICIAL_PENDING` ou `CONFLICT_BLOCKED`.

## Comparaison prédiction vs réalité
Le moteur doit calculer :
- classe prédite ;
- classe réalisée officiellement ;
- erreur probabiliste ;
- succès/échec de la décision ;
- confiance observée vs fiabilité réelle ;
- écart entre cote, probabilité et résultat officiel.

## Apprentissage depuis les résultats officiels
L'apprentissage ne peut utiliser que :
- résultats officiels vérifiés ;
- cotes horodatées valides ;
- snapshots de features reproductibles ;
- métadonnées de provenance complètes.

Les résultats utilisateur ne sont jamais suffisants à eux seuls pour l'entraînement, la recalibration ou le reclassement d'un marché.

## Non-apprentissage depuis une déclaration non vérifiée
Si un utilisateur déclare `WON`, `LOST`, `VOID` ou `REFUNDED` sans résultat officiel correspondant :
- ne pas apprendre ;
- ne pas recalibrer ;
- ne pas mettre à jour la fiabilité du marché ;
- garder la déclaration dans le journal utilisateur ;
- attendre `official_result` ou marquer `OFFICIAL_PENDING`.

## Recalibration
Le `Post-Match Learning Engine` alimente :
- la recalibration des probabilités ;
- la revue des seuils `Kairos Stake Guard` ;
- l'évaluation de la confiance ;
- l'amélioration du `NO_BET`.

Toute recalibration doit rester :
- chronologique ;
- reproductible ;
- segmentée par marché et championnat ;
- séparée des résultats non vérifiés.

## Erreurs du modèle
Le moteur doit produire une taxonomie d'erreurs après-match :
- surconfiance ;
- sous-confiance ;
- mauvais marché recommandé ;
- edge surestimé ;
- qualité de données insuffisante ;
- dérive de championnat ;
- corrélation mal gérée ;
- `NO_BET` manqué ;
- faux positif `KAIROS_AWAKENED`.

## Marchés fiables
Le moteur doit maintenir des tableaux de fiabilité par marché :
- volume de prédictions ;
- Brier ;
- log loss ;
- calibration ;
- ROI simulé net ;
- taux de `NO_BET` ;
- stabilité hors échantillon.

## Championnats fiables
Le moteur doit segmenter la performance par championnat afin d'identifier :
- ligues suffisamment couvertes ;
- segments sous-calibrés ;
- compétitions à exclure ;
- contextes à risque élevé.

## Amélioration du NO_BET
Le `Post-Match Learning Engine` doit relever les cas où :
- `NO_BET` aurait dû être déclenché ;
- un signal `KAIROS_AWAKENED` a mal performé ;
- la confiance a été trop élevée ;
- la qualité des données a été surestimée ;
- la cote a été interprétée trop favorablement.

Ces constats alimentent les futures règles de `Kairos Stake Guard`, sans jamais réécrire l'historique.

## Rapport après-match
Chaque match vérifié peut produire un rapport contenant :
- prédiction publiée ;
- résultat officiel ;
- résultat utilisateur s'il existe ;
- statut de vérification ;
- erreurs du modèle ;
- qualité des données ;
- comportement de `NO_BET` ;
- action recommandée : recalibrer, surveiller, suspendre un segment, ou maintenir.

## Sortie JSON attendue
```json
{
  "engine_name": "Kairos",
  "module": "Post-Match Learning Engine",
  "prediction_id": "pred_001",
  "market": "HALF_GOAL_DOMINANCE",
  "official_result": {
    "verified": true,
    "outcome": "SECOND_HALF_MORE_GOALS",
    "source": "official_provider"
  },
  "user_reported_result": {
    "present": true,
    "ticket_status": "WON"
  },
  "verification_status": "MATCH_VERIFIED",
  "prediction_snapshot": {
    "model_version": "kairos-half-goals-0.1.0",
    "confidence_score": 0.74,
    "decision": "ADVICE"
  },
  "evaluation": {
    "predicted_top_class": "SECOND_HALF_MORE_GOALS",
    "official_class": "SECOND_HALF_MORE_GOALS",
    "brier_component": 0.18,
    "log_loss_component": 0.62,
    "no_bet_should_have_triggered": false
  },
  "learning_actions": [
    "CALIBRATION_UPDATE_CANDIDATE",
    "MARKET_RELIABILITY_RETAINED"
  ],
  "reason_codes": [
    "OFFICIAL_RESULT_VERIFIED",
    "USER_RESULT_NOT_USED_FOR_TRAINING"
  ]
}
```

Cet exemple est illustratif et ne doit jamais être présenté comme une donnée réelle de production.
