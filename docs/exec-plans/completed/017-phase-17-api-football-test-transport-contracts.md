# Phase 17 URIM API-Football Test Transport & Response Contracts

## Objectif
Preparer les contrats de transport et de reponse API-Football avec un transport test-only controle, sans
connecter API-Football et sans permettre d'appel reseau accidentel.

## Portee / hors portee
- Portee : protocole de transport interne, faux transport `TEST_ONLY` / `DEMO_NON_PROD`, contrats de reponse,
  injection explicite dans l'adaptateur read-only pour tests, statut readiness safe, tests et documentation.
- Hors portee : endpoint public test transport, URL provider, cle API, client HTTP, socket, ingestion DB,
  migration Alembic, modele DB, prediction, ML, bookmaker, betting, fixtures/resultats/stats en base,
  frontend/design.

## Hypotheses
- Le comportement par defaut de l'adaptateur API-Football reste disabled.
- Le transport test-only n'est utilisable que par injection explicite dans les tests.
- Les payloads placeholders ne representent jamais une donnee sportive reelle.

## Sources de donnees concernees
- API-Football est reference uniquement comme contrat futur.
- Les payloads Phase 17 sont en memoire, marques `TEST_ONLY`, `DEMO_NON_PROD` et `PLACEHOLDER`.

## Risques de fuite temporelle
- Les timestamps test-only sont timezone-aware et satisfont `observed_at <= available_at <= fetched_at`.
- Aucune prediction n'est creee et aucun snapshot feature n'est produit.
- Les donnees test-only ne peuvent pas servir de fallback production.

## Schemas ou migrations
- Aucun changement Alembic.
- Aucun changement SQLAlchemy.
- Ajout de modeles Pydantic internes pour les contrats de reponse test transport.
- Ajout d'un statut readiness public-safe pour les contrats Phase 17.

## Etapes
- Ajouter `ApiFootballTransportProtocol` et `ApiFootballTestTransport`.
- Ajouter les reponses `fixtures`, `results`, `team_statistics`, `standings`, `lineups` et `events`.
- Calculer `raw_hash` depuis JSON canonique ASCII trie.
- Ajouter les validateurs markers, provider_name, timestamps, hash, no production sports data, no credentials,
  no real URLs.
- Adapter `ApiFootballReadOnlyAdapter` pour accepter un transport test-only uniquement avec opt-in explicite.
- Mettre a jour docs et metadata Phase 17.

## Tests
- Transport fake marque `TEST_ONLY` / `DEMO_NON_PROD`.
- Aucun socket appele.
- Aucun import provider `requests`, `httpx` ou `aiohttp`.
- Payloads placeholders et sans vrai club, score, cote, bookmaker, competition, URL ou credential.
- `raw_hash` stable et timestamps timezone-aware.
- Adapter disabled par defaut, opt-in test explicite transforme en `ProviderObservation` memoire.
- Readiness safe et methodes dangereuses toujours `405`.

## Observabilite
- Readiness expose uniquement que les contrats test transport existent sans runtime public.
- Aucun monitoring provider reel n'est ajoute car aucun provider n'est active.

## Securite
- Aucun secret ajoute.
- Aucun nom de secret provider supplementaire expose publiquement.
- Aucun client HTTP provider ou egress path.
- Aucune modification frontend.

## Plan de retour arriere
- Retirer le module `api_football_transport.py`.
- Retirer l'opt-in test transport de l'adaptateur.
- Retirer `api_football_test_transport_contracts_status` de la readiness.
- Revenir au libelle runtime Phase 16 si la phase est abandonnee.
- Aucun rollback DB requis.

## Criteres d'acceptation
- `pip install -e ".[dev]"`, `ruff check .`, `pytest` et `git diff --check` passent.
- `alembic check` passe si une DB locale est disponible.
- Aucun commit final sans confirmation utilisateur.

## Decisions prises
- Pas de nouvel endpoint public.
- Pas de dependance HTTP provider.
- Les contrats test-only restent separes du sandbox provider generique.
- Le gate Phase 15 et le statut Phase 16 restent bloques.

## Etat d'avancement
- Implementation terminee.
- `pip install -e ".[dev]"` : passe.
- `ruff check .` : passe.
- `pytest` : passe, 159 passed, 2 skipped, 1 avertissement Starlette/TestClient existant.
- `git diff --check` : passe.
- `docker compose -f infra/docker/docker-compose.yml up -d` : passe.
- `alembic upgrade head` : passe avec migrations existantes uniquement.
- `alembic check` : passe, `No new upgrade operations detected.`
- `docker compose -f infra/docker/docker-compose.yml stop` : passe, sans suppression de volume.
