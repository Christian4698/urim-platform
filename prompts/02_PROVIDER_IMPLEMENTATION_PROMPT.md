# Prompt — Premier fournisseur réel pour URIM

Active `data-source-onboarding`, `provider-reconciliation` et `security-review`.

Implémente un connecteur réel seulement après :
- vérification de la documentation officielle ;
- capability matrix ;
- configuration par variables d’environnement ;
- tests de contrat ;
- quotas, timeouts, retries et circuit breaker ;
- mapping canonique ;
- provenance et raw hash ;
- refus du fallback mock en production.

N’écris aucune clé réelle dans un fichier commité. Utilise `.env.example` avec valeurs vides.
