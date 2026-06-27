# Phase 2 URIM Database + Migrations

## Objectif
Mettre en place la fondation PostgreSQL d'URIM avec Alembic et SQLAlchemy, sans connecter de fournisseur sportif, bookmaker, modèle ML, table live avancée ou donnée seed de production.

## Portée
- Créer une structure de migrations Alembic dans `apps/api`.
- Ajouter une couche database minimale au backend FastAPI.
- Créer uniquement les tables fondation nécessaires à la provenance, aux utilisateurs, au Bet Center virtuel, aux tickets internes, aux entités canoniques, aux snapshots, aux prédictions append-only, aux résultats post-match futurs, aux audits et aux incidents.
- Ajouter les contraintes d'audit, d'immuabilité, de temporalité, de sécurité et de désactivation du betting réel.

## Hors portée
- Aucun connecteur API-Football.
- Aucun import de match réel.
- Aucun modèle Kairos réel.
- Aucune logique de mise réelle.
- Aucune donnée seed de production.
- Aucune table live avancée.
- Aucune UI Bet Center avancée.
- Aucun moteur Kairos Analysis.
- Aucune auth complète ni politique RLS complète.

## Hypothèses
- La table utilisateur fondation s'appelle `app_users`.
- PostgreSQL local est fourni par Docker Compose.
- `DATABASE_URL` reste vide dans `.env.example`.
- `ENABLE_LIVE=false`, `ENABLE_REAL_BETTING=false`, `ALLOW_PRODUCTION_MOCKS=false`.
- La devise par défaut est `CDF`.
- `uv` peut être absent localement; les tests backend peuvent utiliser un venv temporaire hors dépôt si nécessaire.

## Sources de données concernées
Aucune donnée sportive réelle n'est ingérée. Les tables providers, observations, payloads et mappings sont seulement préparées pour les phases futures.

## Risques de fuite temporelle
Les champs `available_at`, `fetched_at`, `observed_at`, `prediction_time`, `as_of` et `max_available_at` sont obligatoires là où ils protègent les futures prédictions. Les migrations doivent empêcher qu'un snapshot ou une observation postérieure soit utilisé comme disponible avant l'heure de prédiction.

## Schémas ou migrations
- Ajouter Alembic dans `apps/api/alembic`.
- Créer une migration initiale avec les tables fondation.
- Utiliser UUID PostgreSQL via `pgcrypto` et `gen_random_uuid()`.
- Utiliser `timestamptz`, `jsonb`, clés étrangères, index temporels et contraintes d'unicité.
- Préparer les triggers append-only pour les tables immuables.

## Étapes
1. Créer ce plan actif avant tout autre changement de code.
2. Ajouter les dépendances SQLAlchemy, Alembic et psycopg au backend.
3. Ajouter la configuration database et les helpers de connexion sans forcer une connexion dans `/readiness`.
4. Ajouter les modèles SQLAlchemy déclaratifs pour les tables fondation.
5. Ajouter Alembic et la migration initiale.
6. Ajouter les tests d'invariants Phase 2.
7. Exécuter les validations backend, contrats, frontend et migration Docker si possible.

## Tests
- `pnpm contracts:validate`
- `pnpm web:lint`
- `pnpm web:typecheck`
- `pnpm web:build`
- `pip install -e ".[dev]"` depuis `apps/api` pour installer le CLI Alembic, pytest, httpx et ruff via l'extra `dev`.
- `pytest` depuis `apps/api`; les tests PostgreSQL d'invariants sont actifs quand `DATABASE_URL` pointe vers une base locale migree.
- Docker PostgreSQL local : `docker compose -f infra/docker/docker-compose.yml up -d postgres`, `alembic upgrade head`, `alembic current`, inspection des tables, puis arrêt propre des services démarrés par le test.

## Sécurité
- Aucun secret dans les migrations.
- Aucun appel fournisseur côté frontend ou backend.
- Aucun fallback mock en production.
- Bet Center uniquement virtuel/interne.
- Tickets internes sans exécution de mise réelle.
- Audit logs présents pour actions futures.
- RLS seulement préparé via colonnes utilisateur/audit; pas de politique auth complète en Phase 2.

## Critères d'acceptation
- Le plan actif existe.
- Les migrations se chargent.
- Les tables fondation existent.
- Les champs provenance/temporalité critiques existent.
- Les prédictions et snapshots sont append-only par conception DB.
- Live et real betting restent désactivés.
- Aucun connecteur API-Football, bookmaker, modèle ML, seed de production ou table live avancée n'est ajouté.

## Erreurs E001-E084 concernées
Phase 2 encadre surtout E001-E005, E026, E049, E066-E074, E079, E083 et E084.

## État d'avancement
Implémenté sur la branche `phase-2/database-foundation-recovered-v2`. Le plan reste actif jusqu'à revue finale puis déplacement éventuel vers `docs/exec-plans/completed/`.
