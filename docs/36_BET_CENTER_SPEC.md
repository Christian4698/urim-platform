# Bet Center

Le `Bet Center` est l'interface de `URIM` où l'utilisateur déclare son budget betting hebdomadaire en `CDF`, suit un solde virtuel interne, consulte les sélections `Kairos`, voit les fourchettes prudentes de mise et renseigne les résultats de ses tickets.

Le `Bet Center` ne se connecte jamais directement à un compte bookmaker dans le MVP et n'exécute jamais de mise réelle.

## Rôle du Bet Center
- enregistrer le budget betting hebdomadaire utilisateur ;
- maintenir un solde virtuel interne `URIM` ;
- afficher les sélections `Kairos` recommandées ;
- afficher les fourchettes prudentes `stake_interval_cdf` ;
- permettre des sélections utilisateur non validées par `Kairos` ;
- enregistrer le statut des tickets et leurs performances ;
- alimenter le `Post-Match Learning Engine` uniquement avec des résultats officiels vérifiés.

## Langues et locale
- langue principale : français ;
- langue secondaire optionnelle : anglais ;
- locale par défaut : `fr-CD` ;
- devise par défaut : `CDF`.

## Budget hebdomadaire
`weekly_budget_cdf` est le budget betting déclaré par l'utilisateur pour la semaine courante.

Règles :
- exprimé en `CDF` ;
- saisi manuellement par l'utilisateur ;
- modifiable pour les semaines futures ou avant le premier ticket de la semaine ;
- toute modification après activité doit être journalisée ;
- ne correspond jamais à un solde bookmaker réel.

## Bankroll virtuelle
Le `Bet Center` maintient un `virtual_balance_cdf` interne.

Ce solde :
- démarre à `weekly_budget_cdf` ;
- diminue lors d'une mise virtuelle enregistrée ;
- augmente ou diminue lorsque le ticket est réglé ;
- n'est jamais synchronisé avec un bookmaker ;
- sert de base opérationnelle à `bankroll_cdf` pour `Kairos Stake Guard`.

Par défaut :
- `bankroll_cdf = virtual_balance_cdf` ;
- si `virtual_balance_cdf <= 0`, aucune recommandation de mise n'est affichée.

## Devise CDF
Tous les montants affichés dans le `Bet Center` utilisent `CDF` :
- budget hebdomadaire ;
- solde virtuel ;
- montant misé ;
- fourchette prudente ;
- gain reçu ;
- profit net.

## Règles de mise minimum / maximum
- minimum affichable : `0 CDF` ;
- les mises sont des intervalles `stake_interval_cdf`, jamais des ordres fixes ;
- plafond par match : `0.5 %` de `bankroll_cdf` ;
- exposition journalière maximale : `1.0 %` de `bankroll_cdf` ;
- exposition hebdomadaire maximale : `2.5 %` de `weekly_budget_cdf` ;
- si les limites sont atteintes, retourner `NO_BET`, `WATCH`, `SUSPENDED` ou `KAIROS_LOCKED`.

## Exposition journalière
`daily_exposure_cdf` est la somme des montants virtuels engagés sur les tickets ouverts ou recommandés du jour.

Le système doit :
- calculer l'exposition avant d'afficher une nouvelle fourchette ;
- refuser ou réduire la fourchette si la limite journalière est dépassée ;
- afficher une alerte de risque si l'utilisateur ajoute manuellement trop de tickets.

## Exposition hebdomadaire
`weekly_exposure_cdf` est la somme des montants virtuels engagés sur la semaine active.

Le système doit :
- plafonner l'exposition à `2.5 %` de `weekly_budget_cdf` pour les recommandations `Kairos` ;
- continuer à tracer les tickets utilisateur ajoutés manuellement, même s'ils dépassent les limites ;
- marquer les dépassements avec des reason codes et des alertes.

## Nombre maximum de matchs recommandé
- un ticket recommandé `Kairos` contient de 1 à 5 matchs maximum ;
- la liste quotidienne des recommandations `Kairos` ne doit pas contenir plus de 5 sélections actives ;
- au-delà, scinder en plusieurs tickets ou retourner `NO_BET`.

## Sélections Kairos
Une sélection `Kairos` doit afficher :
- marché ;
- probabilité ;
- `confidence_score` ;
- `risk_level` ;
- `kairos_state` ;
- `stake_interval_cdf` ;
- raison principale ;
- fraîcheur des données ;
- cote disponible et valeur attendue ajustée.

## Sélections utilisateur
L'utilisateur peut ajouter ses propres sélections.

Règles :
- elles sont autorisées sans validation `Kairos` ;
- elles doivent être marquées `USER_UNVALIDATED` ;
- elles ne modifient pas la calibration de `Kairos` ;
- elles peuvent être suivies dans l'historique et le ROI utilisateur ;
- elles ne doivent jamais être présentées comme recommandées par `Kairos`.

## Tickets
Un ticket contient :
- une ou plusieurs sélections ;
- un type d'origine : `KAIROS_RECOMMENDED`, `KAIROS_WATCHLIST` ou `USER_UNVALIDATED` ;
- un montant misé ;
- la cote jouée ;
- une date/heure de création ;
- un statut de règlement ;
- un profit net.

## Statuts gagné / perdu / annulé / remboursé
Les statuts utilisateur supportés sont :
- `WON`
- `LOST`
- `VOID`
- `REFUNDED`

Ils doivent rester distincts du résultat officiel vérifié.

## Gain reçu et profit net
- `gross_return_cdf` : montant total reçu ;
- `stake_placed_cdf` : montant total virtuellement engagé ;
- `profit_net_cdf = gross_return_cdf - stake_placed_cdf`.

Un ticket `VOID` ou `REFUNDED` a un `profit_net_cdf` nul ou documenté selon la règle du bookmaker déclarée par l'utilisateur.

## ROI
`roi_pct = profit_net_cdf / stake_placed_cdf` lorsque `stake_placed_cdf > 0`.

Le `Bet Center` doit distinguer :
- ROI global ;
- ROI des tickets `Kairos` ;
- ROI des tickets `USER_UNVALIDATED`.

## Dashboard
Le `URIM Dashboard` / `Bet Center` peut afficher :
- budget hebdomadaire ;
- solde virtuel courant ;
- exposition du jour ;
- exposition de la semaine ;
- sélections `Kairos` du jour ;
- tickets ouverts ;
- tickets réglés ;
- profit net ;
- ROI ;
- statut `Kairos éveillé` si applicable ;
- alertes de risque.

## Historique
L'historique doit conserver :
- tickets créés ;
- montants virtuels joués ;
- cotes saisies ;
- statuts utilisateur ;
- résultats officiels vérifiés ;
- écarts entre prédiction, ticket et résultat ;
- horodatages et acteur de chaque modification.

## Performance par marché
Le `Bet Center` doit agréger les performances par marché, par exemple :
- `HALF_GOAL_DOMINANCE`
- `1X2`
- `TOTAL_GOALS`
- autres marchés secondaires disponibles.

Chaque vue doit afficher volume, ROI, profit net, taux de `NO_BET`, calibration et couverture.

## Performance par championnat
Le `Bet Center` doit segmenter les performances par championnat pour isoler les segments fiables ou instables.

## Performance par statut Kairos
Les performances doivent être comparées par statut :
- `KAIROS_DORMANT`
- `KAIROS_ATTENTIVE`
- `KAIROS_AWAKENED`
- `KAIROS_LOCKED`
- `NO_BET`

L'objectif est de vérifier si les seuils de confiance et de risque améliorent réellement les résultats hors échantillon.

## Alertes de risque
Alertes minimales :
- budget hebdomadaire presque épuisé ;
- exposition journalière dépassée ;
- exposition hebdomadaire dépassée ;
- plus de 5 sélections recommandées ;
- ajout excessif de tickets `USER_UNVALIDATED` ;
- cote stale ;
- manque de résultat officiel vérifié ;
- divergence entre déclaration utilisateur et résultat officiel.

## Protection contre martingale
- interdire toute progression de mise liée aux pertes précédentes ;
- ne jamais recommander de récupérer les pertes ;
- bloquer les tickets qui augmentent la mise uniquement après un échec ;
- afficher une alerte `MARTINGALE_BLOCKED`.

## Protection contre surmise
- bloquer les recommandations qui dépassent les limites d'exposition ;
- alerter sur les tickets trop corrélés ;
- réduire ou bloquer les fourchettes si trop de sélections sont ouvertes ;
- tracer les dépassements utilisateur sans les faire passer pour validés par `Kairos`.

## UX français / anglais optionnel
Le français est la langue par défaut.

L'anglais peut être activé comme langue secondaire pour :
- labels d'état ;
- statuts de ticket ;
- alertes ;
- tableaux de performance ;
- avertissements responsables.

Les valeurs chiffrées restent en `CDF`.

## Sortie JSON attendue
```json
{
  "app_name": "URIM",
  "module": "Bet Center",
  "locale": "fr-CD",
  "currency": "CDF",
  "weekly_budget_cdf": 250000,
  "virtual_balance_cdf": 243500,
  "bankroll_cdf": 243500,
  "daily_exposure_cdf": 1500,
  "weekly_exposure_cdf": 6500,
  "max_recommended_matches": 5,
  "recommended_selections": [
    {
      "source": "KAIROS_RECOMMENDED",
      "market": "HALF_GOAL_DOMINANCE",
      "kairos_state": "KAIROS_AWAKENED",
      "probabilities": {
        "FIRST_HALF_MORE_GOALS": 31.4,
        "SECOND_HALF_MORE_GOALS": 42.8,
        "EQUAL_HALF_GOALS": 25.8
      },
      "confidence_score": 0.74,
      "stake_interval_cdf": {
        "min": 500,
        "max": 1500,
        "currency": "CDF"
      }
    }
  ],
  "user_selections": [
    {
      "source": "USER_UNVALIDATED",
      "market": "1X2",
      "status": "OPEN"
    }
  ],
  "tickets": [
    {
      "ticket_id": "ticket_001",
      "source": "KAIROS_RECOMMENDED",
      "selection_count": 2,
      "stake_placed_cdf": 1500,
      "odds_played": 2.15,
      "settlement_status": "WON",
      "gross_return_cdf": 3225,
      "profit_net_cdf": 1725,
      "roi_pct": 1.15
    }
  ]
}
```

Cet exemple est illustratif et ne doit jamais être présenté comme une donnée réelle de production.
