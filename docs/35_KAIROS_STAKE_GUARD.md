# Kairos Stake Guard

`Kairos Stake Guard` est le module de mise prudente de `URIM`. Il transforme un signal de `Kairos` en décision de risque et, lorsque les conditions sont réunies, en fourchette indicative de mise en `CDF`.

Il ne place jamais de pari réel, ne promet jamais de gain et peut toujours retourner `NO_BET` ou `INSUFFICIENT_DATA`.

**`Kairos Stake Guard` peut bloquer `Kairos`. `Kairos` ne peut jamais le contourner. Cette règle est absolue et non négociable.**

## Bankroll utilisateur
`bankroll_cdf` désigne un budget utilisateur explicitement déclaré pour l'analyse `URIM`.

Ce budget :
- est exprimé en `CDF` ;
- ne représente pas le solde complet d'un compte ;
- ne constitue pas une autorisation de mise ;
- ne doit pas être augmenté pour récupérer une perte ;
- doit pouvoir être absent, auquel cas aucune fourchette de mise n'est affichée.

## Devise CDF
La devise principale est `CDF`.

Tous les montants de mise doivent être affichés avec :
- `min`
- `max`
- `currency: "CDF"`
- `basis`
- `rounding_rule`

Les montants doivent être des intervalles, jamais un ordre fixe.

## Exposition par match
L'exposition par match est plafonnée à `0.5 %` de `bankroll_cdf`.

La fourchette prudente initiale en état `KAIROS_AWAKENED` est :
- minimum : `0.10 %` du bankroll ;
- maximum : `0.30 %` du bankroll ;
- plafond dur : `0.50 %` du bankroll.

La fourchette doit être réduite ou annulée si la confiance, la calibration, la qualité des données, la fraîcheur de cote ou l'exposition globale se dégrade.

## Exposition journalière
L'exposition journalière maximale est `1.0 %` de `bankroll_cdf`.

Si l'exposition restante du jour est insuffisante, `Kairos Stake Guard` retourne `KAIROS_LOCKED`, `NO_BET` ou `SUSPENDED` avec `stake_interval_cdf` à `0 CDF`.

## Nombre maximal de rencontres
Le nombre maximal recommandé est 3 rencontres par jour.

Au-delà, le système doit réduire l'exposition restante ou retourner `NO_BET`, même si chaque match semble individuellement acceptable.

## Probabilité vs confiance
La probabilité estime la chance d'un scénario.

La confiance mesure la fiabilité de l'analyse selon :
- qualité des données ;
- fraîcheur ;
- calibration ;
- couverture historique ;
- séparation entre scénarios ;
- stabilité du modèle ;
- cohérence entre fournisseurs.

Une probabilité élevée avec confiance faible ne doit pas produire de fourchette de mise.

## Cote et valeur attendue
`Kairos Stake Guard` ne calcule jamais une fourchette avec la probabilité seule.

Il doit prendre en compte :
- probabilité calibrée ;
- cote disponible `as_of prediction_time` ;
- probabilité implicite corrigée de la marge ;
- valeur attendue ajustée ;
- confiance ;
- calibration ;
- qualité des données ;
- nombre de rencontres déjà retenues ;
- exposition par match et exposition journalière ;
- risque de corrélation entre recommandations.

Une cote stale ou absente bloque la fourchette si la décision dépend du prix.

## Seuils Kairos
- `KAIROS_DORMANT` : pas de signal exploitable, `stake_interval_cdf = 0 CDF`.
- `KAIROS_ATTENTIVE` : signal à surveiller, décision `WATCH`, `stake_interval_cdf = 0 CDF`.
- `KAIROS_AWAKENED` : autorise l'affichage `Kairos éveillé` si toutes les conditions conservatrices sont vraies.
- `KAIROS_LOCKED` : garde-fou activé, décision `NO_BET` ou `SUSPENDED`, `stake_interval_cdf = 0 CDF`.
- `NO_BET` : refus explicite, aucune fourchette.

Conditions initiales pour `KAIROS_AWAKENED` :
- `confidence_score >= 0.70`
- `calibration_score >= 0.70`
- `data_quality_score >= 0.75`
- `adjusted_edge >= 0.03`
- cote fraîche ;
- exposition restante par match et par jour suffisante ;
- aucune règle bloquante `NO_BET`.

Ces seuils sont conservateurs et doivent être recalibrés par backtest walk-forward avant production.

## Fourchettes de mise prudentes
La fourchette par défaut pour `KAIROS_AWAKENED` est `0.10 %` à `0.30 %` de `bankroll_cdf`.

Règles :
- arrondir en `CDF` selon une règle documentée ;
- ne jamais dépasser `0.50 %` par match ;
- ne jamais dépasser `1.0 %` par jour ;
- afficher `0 CDF` si une donnée critique est manquante ;
- afficher `0 CDF` si la décision est `WATCH`, `NO_BET`, `INSUFFICIENT_DATA` ou `SUSPENDED`.

## Règles anti-martingale (E055)

La martingale et toute stratégie de doublement ou de progression de mise après perte sont **formellement interdites** dans `URIM`.

- Ne jamais augmenter une fourchette après une perte.
- Ne jamais conseiller de récupérer les pertes.
- Ne jamais multiplier l'exposition pour compenser un historique négatif.
- Ne jamais utiliser la perte précédente comme entrée positive dans le calcul de mise.
- Bloquer toute stratégie progressive liée au résultat précédent.
- Toute tentative de calcul de mise intégrant la récupération de pertes doit être rejetée avec le reason code `MARTINGALE_BLOCKED`.

## Règles anti-surmise
- Bloquer si l'exposition journalière dépasse `1.0 %`.
- Bloquer si l'exposition par match dépasse `0.5 %`.
- Réduire ou bloquer les recommandations corrélées.
- Bloquer si plus de 3 rencontres sont déjà retenues pour la journée.
- Bloquer si la calibration est insuffisante ou si la confiance est faible.
- Bloquer si l'utilisateur réduit son bankroll disponible et rend l'exposition excessive.

## Sortie JSON attendue
```json
{
  "engine_name": "Kairos",
  "module": "Kairos Stake Guard",
  "currency": "CDF",
  "bankroll_cdf": 1000000,
  "kairos_state": "KAIROS_AWAKENED",
  "kairos_status_label": "Kairos éveillé",
  "decision": "ADVICE",
  "probability": 0.428,
  "confidence_score": 0.74,
  "calibration_score": 0.72,
  "data_quality_score": 0.81,
  "adjusted_edge": 0.034,
  "risk_level": "LOW_CONTROLLED",
  "stake_interval_cdf": {
    "min": 1000,
    "max": 3000,
    "currency": "CDF",
    "basis": "0.10% to 0.30% of bankroll_cdf",
    "rounding_rule": "round_down_to_nearest_500_cdf"
  },
  "exposure_limits": {
    "per_match_max_pct": 0.005,
    "daily_max_pct": 0.01,
    "max_recommended_matches_per_day": 3
  },
  "reason_codes": [
    "KAIROS_AWAKENED",
    "EDGE_AFTER_MARGIN",
    "RISK_LIMITS_OK"
  ],
  "responsible_warning": "Fourchette prudente indicative. URIM n'exécute aucune mise réelle."
}
```

Cet exemple est illustratif et ne doit jamais être présenté comme une prédiction réelle.

## Exemples dashboard
- `Kairos endormi` : signal absent, décision informative, `0 CDF`.
- `Kairos attentif` : signal à surveiller, décision `WATCH`, `0 CDF`.
- `Kairos éveillé` : signal fort et limites respectées, fourchette prudente en `CDF`.
- `Kairos verrouillé` : risque ou limite dépassée, `NO_BET` ou `SUSPENDED`, `0 CDF`.

## Avertissements responsables obligatoires (E075–E084)

Toute décision `ADVICE` ou `WATCH` affichée dans `URIM Dashboard` ou `Bet Center` doit être accompagnée des avertissements suivants, non masquables :

- `Probabilités ≠ garanties. Les résultats passés ne préjugent pas des résultats futurs.`
- `Une analyse de qualité ne signifie pas un résultat certain.`
- `Misez uniquement ce que vous êtes prêt à perdre entièrement.`
- `Ne pariez jamais pour récupérer des pertes.`
- `URIM n'exécute aucun pari réel dans le MVP.`

Les périodes de résultats négatifs doivent être publiées et visibles. Les prédictions perdantes ne peuvent jamais être supprimées ou masquées (E067, E068, E078).

## Limites et avertissements

- Une fourchette en `CDF` n'est pas un ordre de pari.
- Une valeur attendue positive simulée peut être fausse si la calibration dérive.
- Une probabilité élevée ne suffit jamais à déterminer une mise.
- Les seuils initiaux doivent être validés hors échantillon.
- Les coûts, limites, annulations, suspensions et indisponibilités peuvent rendre une analyse non exploitable.
- Le MVP n'exécute aucune mise réelle.

## Erreurs E001–E084 directement couvertes

- **E016, E017** : déséquilibre de classes → réduire la confiance, possible blocage.
- **E025** : incertitude → `confidence_score` obligatoire.
- **E026** : NO_BET obligatoire → jamais de conseil forcé.
- **E040** : petit volume → intervalle de confiance requis.
- **E046** : marge bookmaker → toujours retirée avant comparaison.
- **E053** : taux de réussite ≠ rentabilité → affiché séparément.
- **E055** : martingale → formellement interdite, `MARTINGALE_BLOCKED`.
- **E056** : surmise → plafond 0,5 % par match.
- **E057** : exposition journalière → plafond 1,0 %.
- **E058** : paris corrélés → exposition agrégée limitée.
- **E059** : Kelly non calibré → jamais utilisé directement.
- **E067, E068** : ledger immuable → décisions non modifiables.
- **E075–E084** : langage responsable → avertissements obligatoires non masquables.
