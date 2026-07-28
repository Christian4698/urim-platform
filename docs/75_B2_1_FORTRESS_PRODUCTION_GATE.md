# B2.1 Kairos Core — gate production Fortress Mode

## Verdict

**NO-GO production** au 27 juillet 2026.

Le code applicatif, les tests sans PostgreSQL, le packaging et les audits sont
verts. Le gate bloquant PostgreSQL a toutefois refusé toute connexion,
migration et requête parce que `B1_TEST_DATABASE_URL` n'est pas définie.
Aucune base de production n'a été utilisée et aucune URL de connexion n'a été
affichée.

Ce verdict ne remet pas en cause les tests unitaires de Kairos. Il signifie que
les invariants réels de migration, triggers, RLS, append-only, transaction
read-only, timeout et plans PostgreSQL ne disposent pas encore de la preuve
exigée pour une mise en production.

## Défauts confirmés et corrigés

### PROD-001 — tests PostgreSQL susceptibles de cibler `DATABASE_URL`

- Sévérité : haute pour le processus de release.
- Localisation initiale : `tests/test_database_foundation.py`.
- Preuve : deux tests d'écriture avec rollback sélectionnaient directement
  `DATABASE_URL`; une exécution de suite dans un environnement de production
  aurait donc pu ouvrir la base de production.
- Correction : tous les tests PostgreSQL B1 et Kairos utilisent exclusivement
  `B1_TEST_DATABASE_URL` après validation stricte de la cible.
- Garde-fous : refus si URL absente, non PostgreSQL, identique à
  `DATABASE_URL`, même hôte/port/base, marqueur de test absent, marqueur de
  production présent ou `APP_ENV` production-like.
- Outil : `scripts/b1_test_database_gate.py` applique deux fois `upgrade head`
  seulement après ce contrôle et ne sérialise jamais l'URL.

### PROD-002 — rate limiting mémoire non distribué

- Sévérité : moyenne.
- CWE : CWE-770.
- Localisation initiale : `app/api/v1/routes/kairos.py`.
- Preuve : quotas propres à chaque processus; plusieurs workers ou instances
  multipliaient les limites publiques.
- Correction : fenêtre glissante Redis atomique, heure serveur Redis, clés
  client SHA-256, TTL borné, espaces de clés séparés et limites conservées à
  30 analyses/minute/client et 120 méthodologies/minute/client.
- Dégradation sécurisée : absence, timeout, erreur ou réponse Redis invalide
  retourne un 503 générique avec `Retry-After` avant tout accès PostgreSQL.
- Readiness : le service n'est prêt que si PostgreSQL et Redis répondent.

### PROD-003 — panne de configuration Redis insuffisamment bornée

- Sévérité : faible.
- Localisation : création différée du client Redis.
- Preuve : une URL Redis invalide pouvait lever une erreur avant l'appel
  atomique.
- Correction : toute la création/évaluation du client est incluse dans la
  frontière fail-closed et les détails internes ne sont jamais renvoyés.

## Contrôles PostgreSQL

Commande exécutée :

```text
python scripts/b1_test_database_gate.py --migrate
```

Résultat exact :

```text
POSTGRES_GATE_STATUS=REFUSED
POSTGRES_GATE_REASON=B1_TEST_DATABASE_URL_MISSING
GATE_EXIT_CODE=2
```

Par conséquent :

- migrations appliquées : **non**, exécution explicitement refusée;
- migrations rejouées pour idempotence : **non**;
- triggers/RLS/append-only : **non vérifiés sur PostgreSQL réel**;
- transaction `READ ONLY` et `statement_timeout=3000ms` : **non vérifiés sur
  PostgreSQL réel**;
- requêtes repository réelles : **non exécutées**;
- plans/indexes/coûts : **aucun plan réel produit**.

Les tests conditionnels ajoutés vérifient, dès qu'une cible isolée est
disponible :

- la révision `alembic_version` égale à la tête Alembic;
- `SHOW transaction_read_only = on`;
- le timeout de session à trois secondes;
- le refus d'un `INSERT` dans la transaction Kairos;
- une requête réelle et bornée du repository;
- la présence des indexes match/competition/kickoff;
- un `EXPLAIN (FORMAT JSON, COSTS TRUE)` fini et inférieur au seuil de coût
  défensif de 100 000.

## APP_ENV et surface publique

Un processus isolé avec `APP_ENV=production` a obtenu exactement :

```text
/openapi.json = 404
/docs = 404
/redoc = 404
```

Les routes Kairos restent GET-only, read-only, sans écriture métier, appel
fournisseur, betting ou live automatique.

## Validations exécutées

- ciblés sécurité/Redis/PostgreSQL conditionnel : 107 réussis, 8 ignorés,
  1 warning;
- suite API complète : 1 369 réussis, 8 ignorés, 1 warning;
- Ruff : réussi;
- build sdist et wheel : réussi;
- `pip check` : aucune dépendance cassée;
- `pip-audit --local` : aucune vulnérabilité connue; paquet local non publié
  ignoré par l'audit;
- `pnpm audit --prod` : aucune vulnérabilité connue;
- scan `detect-secrets` : aucun secret confirmé; candidats limités à des
  placeholders de tests, mots-clés négatifs et intégrités de lockfile;
- `.env.example` : clé vide, provider désactivé, compétition, saison et URL
  Redis vides;
- `git diff --check` : réussi.

Le warning unique provient de la dépréciation Starlette `TestClient`/`httpx`.
Les huit tests ignorés sont exactement les deux invariants PostgreSQL de
fondation, les cinq tests PostgreSQL Kairos et le test d'intégration B1.

## Variables Render nécessaires

Les noms requis ou explicitement contrôlés sont :

- `APP_ENV`;
- `DATABASE_URL`;
- `REDIS_URL`;
- `CORS_ORIGINS`;
- `ENABLE_LIVE`;
- `ENABLE_REAL_BETTING`;
- `ALLOW_TEST_FIXTURES`;
- `ALLOW_PRODUCTION_MOCKS`;
- `API_FOOTBALL_ENABLED`;
- `API_FOOTBALL_KEY` uniquement si la synchronisation B1 est activée;
- `API_FOOTBALL_PRIORITY_COMPETITIONS`;
- `API_FOOTBALL_SEASON`;
- `API_FOOTBALL_FRESHNESS_MINUTES`.

`B1_TEST_DATABASE_URL` est une variable de test/CI et ne doit pas être définie
sur le service Render de production. Aucune valeur ou clé n'est documentée ici.

## Risques résiduels

1. **Bloquant — PostgreSQL réel non validé.** Fournir une base jetable et
   explicitement isolée, appliquer les migrations puis exécuter les huit tests
   conditionnels.
2. **Moyen — Redis réel non validé.** Aucun serveur Redis local n'était
   installé, `REDIS_URL` était absente et le daemon Docker était indisponible.
   Le script Lua a des tests unitaires, mais doit être exercé contre le service
   Redis-compatible isolé retenu pour Render.
3. **Moyen — identité client derrière proxy.** Valider le comportement
   Uvicorn/Render avec une liste de proxies de confiance. Une mauvaise
   configuration peut agréger les clients; faire confiance à toute provenance
   de header permettrait au contraire de forger l'identité.
4. **Moyen — provenance non signée.** SHA-256 garantit la cohérence calculée,
   pas l'authenticité face à un acteur disposant déjà d'un droit d'écriture DB.
5. **Faible — dépendance fail-closed.** Une panne Redis rend volontairement
   Kairos indisponible afin d'éviter le contournement des quotas.
6. **Faible — dépréciation de test.** La migration Starlette vers `httpx2`
   devra être planifiée sans changer B2.1.

## Condition de levée du NO-GO

Le verdict peut devenir GO seulement après :

1. validation positive de l'URL PostgreSQL isolée;
2. double application réussie des migrations;
3. zéro échec et zéro skip dans les tests PostgreSQL B1/Kairos;
4. capture des plans JSON et coûts réels sous le seuil;
5. test Redis atomique/concurrent contre une instance isolée;
6. validation de l'identité client derrière le proxy de production.

Aucun commit ni push n'a été effectué.
