# Branding URIM et moteur Kairos

## Nomenclature
- Application : `URIM`
- Nom court produit : `Urim`
- Moteur technique d'analyse : `Kairos`
- Dashboard : `URIM Dashboard`
- Centre de mise : `Bet Center`
- Moteur de mise prudente : `Kairos Stake Guard`
- Propriétaire possible : `General Tech Consult` / `GTC`

`GTC` peut désigner l'organisation propriétaire ou créatrice. `GTC` ne doit pas redevenir le nom du produit.

## Rôle de Kairos
`Kairos` transforme des données réelles, horodatées et traçables en probabilités, confiance, risques, raisons et décisions prudentes. Il ne garantit jamais un résultat.

`Kairos` doit toujours distinguer :
- `probabilities` : estimation probabiliste des scénarios ;
- `confidence_score` : fiabilité de l'analyse selon qualité, fraîcheur, calibration, couverture et séparation des scénarios ;
- `risk_level` : niveau de risque produit par `Kairos Stake Guard` ;
- `decision` : `ADVICE`, `WATCH`, `NO_BET`, `INSUFFICIENT_DATA` ou `SUSPENDED`.

## Statut Kairos éveillé
L'interface peut afficher `Kairos éveillé` uniquement lorsque `Kairos Stake Guard` classe l'analyse en `KAIROS_AWAKENED`.

Ce statut signifie :
- signal analytique fort ;
- données suffisamment fraîches et traçables ;
- calibration acceptable ;
- cote fraîche si une fourchette de mise est affichée ;
- exposition restante compatible avec les limites de risque.

Ce statut ne signifie pas :
- résultat certain ;
- gain attendu garanti ;
- mise obligatoire ;
- autorisation d'exécuter un pari réel ;
- récupération des pertes.

## Champs dashboard attendus
Les cartes du `URIM Dashboard` et du `Bet Center` peuvent afficher :
- `market`
- `probabilities`
- `confidence_score`
- `risk_level`
- `kairos_state`
- `kairos_status_label`
- `decision`
- `reason_codes`
- `data_freshness`
- `odds_snapshot_id`
- `stake_interval_cdf`
- `responsible_warning`

`stake_interval_cdf` doit être un intervalle, jamais un ordre fixe. Si la décision est `NO_BET`, `INSUFFICIENT_DATA`, `SUSPENDED`, `WATCH` ou `KAIROS_LOCKED`, l'intervalle affiché doit être `0 CDF`.

## États Kairos
- `KAIROS_DORMANT` : aucun signal exploitable ; afficher une analyse informative et `0 CDF`.
- `KAIROS_ATTENTIVE` : signal à surveiller ; décision `WATCH` et `0 CDF`.
- `KAIROS_AWAKENED` : signal fort ; l'interface peut afficher `Kairos éveillé` et une fourchette prudente si toutes les limites sont respectées.
- `KAIROS_LOCKED` : garde-fou activé ; décision `NO_BET` ou `SUSPENDED`, `0 CDF`.
- `NO_BET` : refus explicite ; aucune fourchette de mise.

## Langage autorisé
- "Probabilité estimée"
- "Confiance de l'analyse"
- "Risque"
- "Fourchette prudente"
- "Signal Kairos"
- "`NO_BET`"
- "`INSUFFICIENT_DATA`"

## Langage interdit
- "gain garanti"
- "mise sûre"
- "pari sûr"
- "sans risque"
- "récupérer les pertes"
- "taux de réussite garanti"
- "score exact garanti"
- "ordre de mise"

## Exemple JSON
```json
{
  "app_name": "URIM",
  "engine_name": "Kairos",
  "market": "HALF_GOAL_DOMINANCE",
  "kairos_state": "KAIROS_AWAKENED",
  "kairos_status_label": "Kairos éveillé",
  "probabilities": {
    "FIRST_HALF_MORE_GOALS": 31.4,
    "SECOND_HALF_MORE_GOALS": 42.8,
    "EQUAL_HALF_GOALS": 25.8
  },
  "confidence_score": 0.74,
  "risk_level": "LOW_CONTROLLED",
  "decision": "ADVICE",
  "stake_interval_cdf": {
    "min": 1000,
    "max": 3000,
    "currency": "CDF",
    "basis": "0.10% to 0.30% of bankroll_cdf"
  },
  "responsible_warning": "Fourchette prudente indicative. URIM n'exécute aucune mise réelle."
}
```

Cet exemple est illustratif et ne doit jamais être présenté comme une prédiction réelle.

## Limites
- `Kairos éveillé` peut disparaître si les données, la cote, la calibration ou l'exposition changent.
- Une probabilité élevée ne suffit jamais à afficher une fourchette de mise.
- Une confiance élevée ne garantit pas le résultat.
- Les montants en `CDF` restent des intervalles prudents, pas des instructions d'exécution.

Voir `docs/35_KAIROS_STAKE_GUARD.md` pour la spécification complète des seuils, intervalles en `CDF`, règles anti-martingale, anti-surmise, avertissements responsables et erreurs E couvertes.
