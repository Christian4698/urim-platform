---
name: data-source-onboarding
description: Intégrer ou auditer un fournisseur réel de données sportives; déclencher pour API, couverture, quotas, licence, mapping ou connecteur.
---

# data-source-onboarding


1. Lire `docs/04_REAL_DATA_SOURCES.md`, `05_PROVIDER_CONNECTOR_CONTRACT.md` et `28_PROVIDER_ONBOARDING_CHECKLIST.md`.
2. Refuser tout scraping non autorisé.
3. Documenter couverture, fraîcheur, quotas, licence et limites.
4. Implémenter derrière l’interface canonique.
5. Ajouter tests de contrat, golden payloads, health checks et redaction.
6. Ne jamais mettre la clé côté client.
7. Ne jamais faire de fallback vers un mock en production.
8. Produire un rapport de lacunes avant activation.


## Sortie attendue
- Résumé
- Fichiers modifiés
- Tests exécutés
- Risques restants
- IDs E001–E084 concernés
