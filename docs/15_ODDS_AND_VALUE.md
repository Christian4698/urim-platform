# Cotes, valeur et Bet Center

1. Capturer la cote avec bookmaker, marché et heure.
2. Convertir en probabilité implicite.
3. Retirer la marge.
4. Comparer au modèle calibré.
5. Appliquer une marge de sécurité.
6. Refuser un prix stale.

## Indicateurs
Edge brut/ajusté, expected value simulée, closing line value, cote moyenne et sensibilité à la calibration.

Le `Bet Center` consomme les signaux de `Kairos` et applique les garde-fous de `Kairos Stake Guard`.

Un fort taux de réussite peut rester déficitaire avec de faibles cotes.

## Fourchettes CDF
`Kairos Stake Guard` peut afficher une fourchette prudente `stake_interval_cdf` seulement si la probabilité calibrée, la cote, la confiance, la calibration, la qualité des données, l'exposition par match, l'exposition journalière et le risque global sont acceptables.

Règles :
- devise principale : `CDF` ;
- afficher un intervalle, jamais un ordre fixe ;
- plafond par match : `0.5 %` de `bankroll_cdf` ;
- exposition journalière maximale : `1.0 %` de `bankroll_cdf` ;
- fourchette initiale `KAIROS_AWAKENED` : `0.10 %` à `0.30 %` du bankroll ;
- `WATCH`, `NO_BET`, `INSUFFICIENT_DATA`, `SUSPENDED` ou `KAIROS_LOCKED` affichent `0 CDF`.

La probabilité seule ne suffit jamais à calculer une fourchette.
