# Programme B1 — Fondation des données sportives réelles

## Objectif

Connecter le backend URIM à API-Football pour acquérir, normaliser, versionner,
stocker et exposer en lecture seule des données sportives réelles, sans activer
Kairos, les bookmakers, le live automatique, les conseils ou les paris.

## Audit initial

- Les contrats de provenance, de temporalité et de redaction existent.
- Les builders et normaliseurs API-Football historiques sont test-only.
- Une table `api_football_fixture_staging` existe, sans pipeline d'écriture.
- Les tables génériques `providers`, `provider_observations`,
  `canonical_entities` et `fixtures` ne couvrent pas le périmètre B1 complet.
- Aucun client HTTP provider de production, job contrôlé, modèle de
  compétition/saison/classement/statistique ou endpoint public sportif réel
  n'existe.
- Le frontend Programme A ne consomme que `/health` et `/readiness`.

## Architecture cible

```text
API-Football (HTTPS, clé backend)
        |
        v
Client allowlisté
timeout + retry borné + quota + rate limit + validation
        |
        v
Normalisation B1 sans payload brut ni média
        |
        v
Service de synchronisation contrôlé
budget de requêtes + run + checkpoints + erreurs neutralisées
        |
        v
PostgreSQL / Supabase
observations versionnées + contraintes d'idempotence + RLS
        |
        v
FastAPI read-only /api/v1/sports/*
        |
        v
Next.js /donnees-sportives
```

## Travaux

1. Ajouter la configuration backend secret-safe et les limites B1.
2. Implémenter le client API-Football et les contrats normalisés.
3. Créer les tables B1, contraintes, index, RLS et migration Alembic.
4. Implémenter le dépôt append-only/idempotent et les synchronisations.
5. Ajouter les commandes compétitions, saisons, date, upcoming, résultats et
   statistiques.
6. Ajouter les endpoints lecture seule et les états provider/fraîcheur.
7. Ajouter l'interface frontend lecture seule responsive.
8. Ajouter les tests client, contrats, normalisation, temporalité,
   idempotence, migration, endpoints, erreurs, secrets et frontend.
9. Exécuter migrations test, Ruff, tests, lint, types, build, audits et Git.
10. Documenter l'exploitation Render, les limites de licence et la suite B2.

## Invariants

- `API_FOOTBALL_KEY` reste exclusivement backend et n'est jamais loggée,
  retournée, committée ou demandée dans la conversation.
- Le provider est désactivé si la clé est absente ou si le flag explicite est
  fermé.
- La base URL et les endpoints sont allowlistés ; aucun URL utilisateur.
- Chaque observation porte la provenance obligatoire et respecte
  `observed_at <= available_at <= fetched_at`.
- Une nouvelle réponse modifiée crée une nouvelle version ; un hash identique
  ne crée aucun doublon.
- Aucun appel provider réel n'est exécuté par les tests.
- Aucun endpoint odds, predictions ou live automatique n'est implémenté.
- Les tables B1 ne sont pas accessibles directement aux rôles Data API
  publics ; le backend FastAPI reste l'unique frontière publique.

## Risques couverts

- E001–E005 : complétude, doublons, source, provenance et temporalité.
- E009/E011/E066/E071/E072 : compétition, couverture, timezone, missing et
  identité.
- E026/E037–E039/E049 : aucun conseil, aucune fuite future, aucune confusion
  pré-match/live/post-match.
- E065/E069/E070/E073/E074 : panne provider, versionnement, validation,
  latence/quota et secrets.
- E075–E084 : aucune promesse, aucun bookmaker et aucun pari réel.

## État

Terminé le 23 juillet 2026.

## Résultats

- Migration PostgreSQL 16 validée en upgrade, downgrade et ré-upgrade;
  `alembic check` sans dérive.
- RLS, triggers append-only et idempotence vérifiés sur une base jetable.
- Ruff réussi.
- Backend : 1 239 tests réussis et 3 conditionnels sans base externe; les
  3 tests PostgreSQL ont ensuite tous réussi sur la base jetable, soit
  1 242 tests uniques exécutés et aucun test laissé non vérifié.
- Frontend : contrats, lint et types réussis; 25 tests réussis.
- Build Next.js production réussi; 16 pages statiques générées.
- Smoke test Playwright desktop/mobile/offline réussi; 6 appels sportifs
  frontend vers FastAPI en HTTP 200, aucune erreur console.
- Audits Python et pnpm : aucune vulnérabilité connue.
- Scan de frontière des secrets et Blueprint Render : réussis.
- Aucun appel API-Football réel et aucune donnée sportive simulée publiée.
