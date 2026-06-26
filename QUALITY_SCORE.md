# QUALITY_SCORE.md — URIM

Grille de score qualité pour `URIM` et `Kairos`.

| Domaine | Poids |
|---|---:|
| Intégrité temporelle | 20 |
| Provenance et qualité des données | 15 |
| Calibration et évaluation | 15 |
| Tests | 15 |
| Sécurité | 10 |
| Fiabilité / observabilité | 10 |
| Explicabilité | 5 |
| UX et accessibilité | 5 |
| Documentation | 5 |

## Bloquants indépendants du score
- Fuite temporelle connue.
- Donnée fictive présentée comme réelle.
- Secret exposé.
- Prédiction modifiable après publication.
- Absence de séparation pré-match/live.
- Garantie commerciale mensongère.
