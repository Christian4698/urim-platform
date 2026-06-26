# Spécification produit URIM

## Nomenclature officielle
- Application : `URIM`
- Nom court produit : `Urim`
- Cerveau analytique : `Kairos`
- Dashboard : `URIM Dashboard`
- Centre de mise : `Bet Center`
- Moteur de mise prudente : `Kairos Stake Guard`
- Propriétaire / créateur possible : `General Tech Consult` / `GTC`

## Identité canonique
```json
{
  "app_name": "URIM",
  "product_short_name": "Urim",
  "engine_name": "Kairos",
  "dashboard_name": "URIM Dashboard",
  "bet_center_name": "Bet Center",
  "stake_guard_name": "Kairos Stake Guard",
  "kairos_awakened_label": "Kairos éveillé",
  "currency": "CDF",
  "default_locale": "fr-CD",
  "primary_language": "fr",
  "secondary_language": "en",
  "owner": "General Tech Consult"
}
```

## Modules nommés
- `URIM` : application principale.
- `Kairos` : cerveau analytique principal.
- `Half Goals Intelligence Engine` : cœur produit principal pour `HALF_GOAL_DOMINANCE`.
- `Bet Center` : centre de budget hebdomadaire, tickets, performance et décision utilisateur.
- `Kairos Stake Guard` : moteur de mise prudente, d'exposition et de protection contre la surmise.
- `Post-Match Learning Engine` : moteur d'apprentissage post-match.
- `Corners Intelligence Engine` : module spécialisé corners.
- `Fouls & Cards Intelligence Engine` : module spécialisé fautes et cartons.
- `NO_BET Engine` : moteur de refus explicite.

## Utilisateurs
- Analyste sportif
- Opérateur de données
- Administrateur
- Utilisateur final

## Écrans MVP
1. `URIM Dashboard` : matchs à venir.
2. Fiche match et provenance.
3. Probabilités `HALF_GOAL_DOMINANCE` : `FIRST_HALF_MORE_GOALS`, `SECOND_HALF_MORE_GOALS`, `EQUAL_HALF_GOALS`.
4. Scénarios probables.
5. Facteurs favorables, défavorables et manquants.
6. `Bet Center` : décision `ADVICE`, `WATCH`, `NO_BET` ou `INSUFFICIENT_DATA`, avec probabilité, confiance, risque et fourchette prudente en `CDF`.
7. Budget hebdomadaire, solde virtuel, tickets ouverts et réglés.
8. Historique : `WON`, `LOST`, `VOID`, `REFUNDED`, profit net et ROI.
9. Tableau de calibration `Kairos` et retour post-match.
10. Journal immuable et santé des fournisseurs.

## Sortie d’une analyse
Heure, mode, fraîcheur, probabilités complètes, confiance, risque, facteurs, sources, version du modèle, version de `Kairos`, état Kairos, décision de risque, fourchette prudente `stake_interval_cdf`, budget hebdomadaire, solde virtuel, statut ticket et avertissement responsable.

L'interface peut afficher `Kairos éveillé` uniquement si `Kairos Stake Guard` retourne `KAIROS_AWAKENED`. Ce libellé indique un signal analytique fort, jamais un résultat certain.

Le `Bet Center` doit distinguer les sélections `Kairos` et les sélections utilisateur `USER_UNVALIDATED`. Le `Post-Match Learning Engine` apprend uniquement depuis des résultats officiels vérifiés.

## Hors portée MVP
Exécution de mise, martingale, récupération des pertes, connexion à un compte bookmaker, bankroll réelle imposée, tickets automatiques, promesse de gains et score exact comme produit principal.
