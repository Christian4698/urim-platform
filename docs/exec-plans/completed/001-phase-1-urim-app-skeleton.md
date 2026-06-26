# Phase 1 URIM App Skeleton

## Objectif
Créer le squelette applicatif URIM avec moteur Kairos, sans connecter de données sportives réelles, sans bookmaker, sans base de données métier et sans logique prédictive réelle.

## Portée
- Créer une structure monorepo claire : `apps/web`, `apps/api`, `packages/contracts`, `packages/config`, `packages/ui`, `infra/docker`.
- Mettre en place un dashboard Next.js en français avec pages placeholders explicitement marquées.
- Mettre en place une API FastAPI limitée aux endpoints santé/version/readiness.
- Préparer les contrats partagés et la configuration Phase 1.
- Ajouter les instructions de démarrage, scripts utiles, `.gitignore`, et Docker Compose local minimal.

## Hors portée
- Aucun connecteur sportif réel.
- Aucun bookmaker connecté.
- Aucune mise réelle exécutée.
- Aucune table ou migration métier.
- Aucun modèle ML réel.
- Aucun conseil de mise réel.
- Aucun mode live prioritaire.

## Hypothèses
- Gestionnaire JS : `pnpm`.
- Gestionnaire Python : `uv`.
- Locale par défaut : `fr-CD`.
- Devise par défaut : `CDF`.
- `ENABLE_LIVE=false`, `ENABLE_REAL_BETTING=false`, `ALLOW_PRODUCTION_MOCKS=false`.
- Les anciens documents de gouvernance restent intacts sauf besoin limité de cohérence visible URIM/Kairos.

## Sources de données concernées
Aucune source de données sportive réelle n'est concernée en Phase 1. Les modules providers existent uniquement comme structure.

## Risques de fuite temporelle
Faibles en Phase 1 car aucun dataset, connecteur, feature store, backtest ou modèle n'est implémenté. Les contrats conservent toutefois les champs requis pour préserver les invariants futurs : `prediction_time`, `available_at`, `fetched_at`, `raw_hash`, `immutable_hash`.

## Schémas ou migrations
- Ajouter les schémas JSON partagés dans `packages/contracts/schemas`.
- Conserver les schémas racine existants pour compatibilité documentaire.
- Ne créer aucune migration métier en Phase 1.

## Étapes
1. Créer ce plan actif avant tout autre changement.
2. Ajouter les fichiers de workspace `pnpm` et les scripts racine.
3. Créer `apps/web` avec layout URIM, navigation, pages placeholders, composants `Card`, `Badge`, `StatusPill`, `MetricCard`, support i18n futur et formatage CDF.
4. Créer `apps/api` avec FastAPI, configuration, sécurité placeholder, modules vides et tests santé.
5. Créer `packages/contracts`, `packages/config` et `packages/ui`.
6. Mettre à jour `.env.example`, `.gitignore`, README et infra Docker locale.
7. Exécuter les validations possibles : tests backend, validation contrats, lint/build frontend si les dépendances sont disponibles.

## Tests
- Backend : `uv run pytest` dans `apps/api`.
- Frontend : `pnpm --filter @urim/web lint` et `pnpm --filter @urim/web build` si les dépendances sont installées.
- Contrats : `pnpm --filter @urim/contracts validate`.
- Sécurité : vérifier l'absence de secrets et d'appels fournisseurs frontend.
- Temporalité/risque : vérifier qu'aucun calcul prédictif, aucune donnée future, aucun live et aucun betting réel ne sont implémentés.

## Observabilité
Phase 1 expose uniquement les endpoints santé/version/readiness. L'observabilité complète sera traitée plus tard avec métriques, logs redacted et audit.

## Sécurité
- Aucune clé réelle.
- Aucune clé fournisseur côté frontend.
- Pas de fallback mock en production.
- `ENABLE_REAL_BETTING=false`.
- `ALLOW_PRODUCTION_MOCKS=false`.

## Plan de retour arrière
Revenir uniquement les fichiers ajoutés ou modifiés par cette phase. Aucun état externe, migration ou donnée de production n'est créé.

## Critères d'acceptation
- Plan actif présent.
- Monorepo créé sans casser les docs existantes.
- Dashboard URIM visible avec placeholders français explicites.
- API santé fonctionnelle.
- Contrats partagés présents.
- `.env.example` cohérent URIM/Kairos.
- Docker Compose local minimal présent sans tables métier.
- Tests smoke exécutés ou commandes manuelles documentées si dépendances indisponibles.

## Erreurs E001-E084 concernées
Phase 1 prévient ou encadre surtout E005, E026, E049, E066, E071, E074, E075, E076, E077, E083 et E084 en désactivant données réelles, live, betting réel et recommandations, et en marquant les placeholders.

## État d'avancement
Implémenté en Phase 1. Le plan reste actif jusqu'à revue finale puis déplacement éventuel vers `docs/exec-plans/completed/`.
