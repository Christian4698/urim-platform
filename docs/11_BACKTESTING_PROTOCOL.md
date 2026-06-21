# Protocole de backtesting

1. Walk-forward validation.
2. Fenêtres datées.
3. Snapshot des données tel qu’il existait à l’époque.
4. Aucun réglage après lecture du test sans nouveau test vierge.
5. Frais, marge, indisponibilité et latence simulés.
6. Résultats segmentés.

## Métriques
Brier, log loss, calibration error, accuracy équilibrée, precision/recall, couverture, ROI simulé net, drawdown, closing line value, stabilité et intervalles bootstrap.

Tous les essais, y compris les échecs, sont journalisés.
