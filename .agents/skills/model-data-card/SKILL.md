---
name: model-data-card
description: Creer, auditer ou mettre a jour les model cards et data cards URIM, incluant version modele, marche, sources, licence, couverture, calibration, qualite, limites, erreurs E001-E084 et statut de promotion.
---

# model-data-card

1. Lire `docs/43_MODEL_CARD_TEMPLATE.md`, `docs/44_DATA_CARD_TEMPLATE.md`, `docs/11_BACKTESTING_PROTOCOL.md`, `docs/12_CALIBRATION_AND_EVALUATION.md` et `docs/40_DATA_QUALITY_GATE.md`.
2. Documenter usage prevu, marche, version, donnees, features, evaluation, calibration et limites.
3. Relier chaque model card aux data cards utilisees.
4. Refuser une promotion sans metriques, couverture, limites et erreurs E001-E084.
5. Ne jamais masquer les segments faibles, periodes negatives ou donnees manquantes.
6. Distinguer performance probabiliste, valeur simulee et absence de garantie.
7. Conserver les cards versionnees et auditables.

## Sortie attendue
- Resume
- Fichiers modifies
- Tests executes
- Risques restants
- IDs E001-E084 concernes
