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
