# Instructions Codex — usage du catalogue d'APIs (annexe, hors séquence de phases)

> Ce document ne fait pas partie de la séquence numérotée `docs/00_...` à `docs/43_...` et ne constitue pas une nouvelle phase de travail. Il encadre l'usage du catalogue `docs/api-catalog.md` par Codex, une fois que l'humain aura validé les APIs à retenir.

## Ce que Codex doit faire
1. Lire `docs/api-catalog.md` avant toute décision d'intégration d'API externe.
2. Ne jamais coder une intégration directement depuis `_references/public-apis/` sans validation humaine explicite du catalogue.
3. Pour chaque API validée, créer un adapter propre derrière l'interface canonique existante :
   - URIM : suivre le pattern déjà en place dans `apps/api/app/modules/providers/` (voir `contracts.py`, `api_football_adapter.py`) et respecter `docs/05_PROVIDER_CONNECTOR_CONTRACT.md`.
   - Ne pas créer de deuxième pattern de provider concurrent.
4. Créer des types (TypeScript côté `apps/web`, ou Pydantic côté `apps/api`) qui reflètent fidèlement le contrat de données du fournisseur, pas une copie brute de sa réponse JSON.
5. Créer un mock/demo provider avant tout provider réel, activable par défaut.
6. Créer un provider réel désactivé par défaut (feature flag / variable d'environnement), jamais actif tant que la validation humaine n'a pas eu lieu.
7. Respecter strictement le principe DEMO ON / LIVE OFF déjà en vigueur dans le dépôt (No Bet, bankroll, Kazon/Razon le cas échéant) : aucune bascule vers un mode réel sans validation explicite.
8. Ne jamais exposer une clé API côté frontend (`apps/web`) — tout appel à un fournisseur tiers passe par le backend (`apps/api`).
9. Documenter chaque nouvelle variable d'environnement dans `.env.example`, avec un commentaire indiquant le fournisseur et son usage — jamais de valeur réelle committée.
10. Ajouter les tests attendus par `AGENTS.md` (contrat, provenance, temporalité) pour tout nouveau connecteur de données réelles.

## Ce que Codex ne doit pas faire
- Ne pas renommer ou renuméroter les documents `docs/00_...` à `docs/43_...` pour y insérer ce catalogue.
- Ne pas démarrer de nouvelle phase Codex à partir de ce document seul — il sert de préparation, pas de déclencheur de phase.
- Ne pas dupliquer l'arborescence de providers existante sous un autre nom.
- Ne pas activer un mode LIVE, un pari réel, un paiement réel ou un trade réel sans validation explicite distincte de la validation du catalogue.

## Prérequis avant toute intégration réelle
- Catalogue validé par l'humain (voir `docs/api-catalog.md`).
- Gate d'onboarding provider respecté pour URIM : `docs/28_PROVIDER_ONBOARDING_CHECKLIST.md`, `docs/29_PROVIDER_READINESS_CONTRACTS.md`, `docs/30_PROVIDER_ONBOARDING_GATE.md`, `docs/34_PROVIDER_ACTIVATION_READINESS_FINAL_GATE.md`.
- Variables d'environnement documentées dans `.env.example`, aucune clé réelle committée.
