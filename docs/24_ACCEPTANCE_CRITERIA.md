# Critères d’acceptation

## Données
- 100 % des prédictions ont un snapshot de provenance.
- Aucun futur dans les tests adversariaux.
- Aucun mock en production.
- Fraîcheur visible.
- Conflits critiques bloquants.

## Modèle
- Baselines comparées.
- Calibration publiée.
- Walk-forward.
- Résultats segmentés.
- Incertitude affichée.
- NO_BET opérationnel.

## Produit
- Journal immuable.
- Explication fidèle.
- Sources et versions visibles.
- Messagerie agent auditable.
- Aucun langage de garantie.

## Sécurité
- Secret scan propre.
- RBAC testé.
- Logs redacted.
- Fournisseurs appelés côté serveur.
- Threat model à jour.

Un seul bloquant de `QUALITY_SCORE.md` fait échouer la release.
