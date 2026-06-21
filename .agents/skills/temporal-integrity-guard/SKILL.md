---
name: temporal-integrity-guard
description: Détecter et prévenir data leakage, target leakage et look-ahead bias dans features, datasets, backtests ou prédictions.
---

# temporal-integrity-guard


1. Lire `docs/07_TEMPORAL_INTEGRITY.md` et E005, E029–E031, E037–E039.
2. Identifier l’heure exacte T.
3. Vérifier `available_at <= T`.
4. Vérifier splits chronologiques et transformations fit sur train.
5. Ajouter un test adversarial.
6. Bloquer la PR si une fuite est plausible.
7. Exiger un snapshot reproductible et ses hashes.


## Sortie attendue
- Résumé
- Fichiers modifiés
- Tests exécutés
- Risques restants
- IDs E001–E084 concernés
