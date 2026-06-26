---
name: prediction-release-gate
description: Décider si une version du bot peut être livrée en staging ou production.
---

# prediction-release-gate


1. Lire `QUALITY_SCORE.md` et `docs/24_ACCEPTANCE_CRITERIA.md`.
2. Vérifier les bloquants avant le score.
3. Exiger rapports data, temporalité, calibration, sécurité et observabilité.
4. Vérifier que production refuse les fixtures.
5. Vérifier que le ledger est immuable.
6. Rendre un verdict PASS/FAIL avec preuves.


## Sortie attendue
- Résumé
- Fichiers modifiés
- Tests exécutés
- Risques restants
- IDs E001–E084 concernés
