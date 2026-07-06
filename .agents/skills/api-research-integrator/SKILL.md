---
name: api-research-integrator
description: Rechercher et comparer des APIs publiques (via _references/public-apis) pour un besoin précis d'URIM; déclencher avant tout ajout de fournisseur de données externe.
---

# api-research-integrator

1. Lire `docs/api-catalog.md` (annexe) avant toute recherche — ne pas dupliquer une entrée déjà cataloguée.
2. Chercher dans `_references/public-apis/README.md` (dépôt de référence, jamais copié dans le code applicatif).
3. Comparer les candidats sur : auth, HTTPS, CORS, quota, stabilité de la documentation, licence.
4. Refuser toute API sans HTTPS pour un usage production.
5. Refuser toute API instable, non documentée, ou sans historique d'usage vérifiable.
6. Toute API avec `apiKey`/`OAuth` exige une variable déclarée dans `.env.example`, jamais une clé en dur.
7. Toute API jugée critique doit avoir un mode mock avant tout mode réel.
8. Ne jamais intégrer une API réelle sans validation humaine explicite — produire d'abord un connecteur mock/demo, puis proposer un adaptateur réel séparé si validé.
9. Toute intégration réelle passe par un service adapter (ex. `apps/api/app/modules/providers/` pour URIM) — jamais un appel direct depuis un composant UI.
10. Pour URIM spécifiquement, suivre en plus `docs/04_REAL_DATA_SOURCES.md`, `docs/05_PROVIDER_CONNECTOR_CONTRACT.md` et `docs/28_PROVIDER_ONBOARDING_CHECKLIST.md`.
11. Mettre à jour `docs/api-catalog.md` si une nouvelle API pertinente est découverte, sans renuméroter la séquence de phases.

## Sortie attendue
- API(s) proposée(s) avec justification
- Niveau de risque et statut MVP/prod
- Variables .env nécessaires (non renseignées)
- Mode mock proposé avant tout mode réel
- Rappel explicite : aucune intégration réelle sans validation humaine
