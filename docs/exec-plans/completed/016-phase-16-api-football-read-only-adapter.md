# Phase 16 URIM API-Football Read-Only Adapter

## Objectif
Preparer une structure d'adaptateur API-Football strictement read-only, desactivee par defaut et bloquee
par le gate Phase 15. Cette phase ne connecte pas API-Football et ne permet aucun appel reseau accidentel.

## Portee / hors portee
- Portee : adapter Python bloque, statut public safe dans `GET /api/v1/providers/readiness`, tests et docs.
- Hors portee : URL provider, endpoint reel, cle API, client HTTP, socket, ingestion DB, migration Alembic,
  modele DB, prediction, ML, bookmaker, betting, fixtures/resultats/stats en base, frontend/design.

## Hypotheses
- Le gate Phase 15 reste l'autorite bloquante avant toute activation provider.
- Les noms et valeurs de secrets provider ne sont pas ajoutes ou exposes.
- Les donnees API-Football futures resteront `missing` tant qu'aucun provider n'est approuve et active.

## Sources de donnees concernees
- API-Football est reference uniquement comme fournisseur futur read-only.
- Aucune donnee reelle provider, fixture, resultat, statistique, lineup, event, cote ou bookmaker n'est recuperee.

## Risques de fuite temporelle
- Aucun payload provider n'est lu, normalise ou stocke en Phase 16.
- Les methodes de fetch refusent l'execution avant toute observation, donc aucune information future ne peut
  alimenter une prediction passee.

## Schemas ou migrations
- Aucun changement Alembic.
- Aucun changement SQLAlchemy.
- Ajout d'un schema Pydantic public-safe `ProviderApiFootballReadOnlyAdapterStatus`, tous les flags dangereux
  verrouilles a `false`.

## Etapes
- Ajouter `ApiFootballReadOnlyAdapter` et `ApiFootballProviderDisabledError`.
- Bloquer `fetch_fixtures`, `fetch_results`, `fetch_team_statistics`, `fetch_standings`, `fetch_lineups` et
  `fetch_events`.
- Exposer `api_football_read_only_adapter_status` dans `/api/v1/providers/readiness`.
- Mettre a jour les metadonnees runtime vers `phase-16-api-football-read-only-adapter`.
- Documenter Phase 16 dans les specs et l'index.

## Tests
- Adapter desactive par defaut.
- Toutes les methodes API-Football refusent l'execution.
- Le guard ne touche pas `socket.create_connection`.
- Readiness expose un statut safe.
- Methodes dangereuses sur `/api/v1/providers/readiness` restent `405`.
- Aucune fuite de secret, URL provider, credential, bookmaker, score ou resultat sportif.

## Observabilite
- Le statut public indique explicitement `disabled_until_provider_activation_gate_approved`.
- Aucun monitoring provider reel n'est ajoute car aucun provider n'est active.

## Securite
- Aucun secret ajoute a `.env.example`.
- Aucun nom de secret provider supplementaire expose publiquement.
- Aucun appel reseau, client HTTP, credential loader ou egress path.

## Plan de retour arriere
- Retirer le module `api_football_adapter.py`.
- Retirer `api_football_read_only_adapter_status` du schema readiness.
- Revenir au libelle runtime Phase 15 si la phase est abandonnee.
- Aucun rollback DB requis.

## Criteres d'acceptation
- `pip install -e ".[dev]"`, `ruff check .`, `pytest` et `git diff --check` passent.
- `alembic check` passe si une DB locale est disponible.
- Aucun commit final sans confirmation utilisateur.

## Decisions prises
- Le statut Phase 16 est minimal et ne contient pas de champs URL, endpoint ou HTTP.
- Les builders ignorent les objets dangereux construits artificiellement.
- Le gate Phase 15 reste visible et bloque toute activation provider.

## Etat d'avancement
- Implementation terminee.
- `pip install -e ".[dev]"` : passe.
- `ruff check .` : passe.
- `pytest` : passe, 146 passed, 2 skipped, 1 avertissement Starlette/TestClient existant.
- `git diff --check` : passe.
- `alembic check` : non execute car `DATABASE_URL` n'est pas defini et Docker n'est pas disponible.
