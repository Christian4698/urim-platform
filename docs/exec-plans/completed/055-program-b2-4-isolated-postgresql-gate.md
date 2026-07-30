# Programme B2.4 — Isolated PostgreSQL Gate

## Mission

Valider B2.4 sur une base PostgreSQL locale explicitement isolée, sans utiliser
`DATABASE_URL`, sans accès fournisseur ou base distante, et sans afficher de
credential.

## Plan exécuté

1. Valider la cible `B1_TEST_DATABASE_URL` et l'absence de `DATABASE_URL`.
2. Appliquer Alembic jusqu'à l'unique tête `202607280001`.
3. Inspecter les contraintes, triggers, RLS et privilèges réels.
4. Tester temporalité, hashes, unicités, append-only et résolutions.
5. Tester idempotence, concurrence, rollback et workflow complet.
6. Downgrader B2.4 vers `26fe26a73d5c`, puis revenir au head.
7. Exécuter les suites API/frontend, builds et audits de sécurité.

## Migrations réellement appliquées

- base vide vers `202606260001` ;
- `202606260001` vers `202607080035` ;
- `202607080035` vers `26fe26a73d5c` ;
- `26fe26a73d5c` vers `202607280001`.

Le gate a ensuite confirmé l'idempotence d'un second `upgrade head`. Le test de
downgrade a supprimé les deux tables B2.4 à `26fe26a73d5c`, puis l'upgrade les
a recréées et a rétabli la tête `202607280001`.

## Invariants PostgreSQL vérifiés

- une seule tête Alembic dans le script et dans la base ;
- `analysis_time <= created_at < kickoff_at` ;
- unicité de `analysis_id` et `immutable_hash` ;
- format des hashes contrôlé ;
- `UPDATE` et `DELETE` interdits sur journal et résolutions ;
- journal et résolutions dans deux tables distinctes ;
- identité analyse/match/marché obligatoire et concordante ;
- résolution avant kickoff interdite ;
- résultat non-`VOID` recalculé depuis les scores HT/FT ;
- analyse originale impossible à altérer ;
- RLS activée et aucun grant `anon`/`authenticated` ;
- doublon logique absorbé sans modification de l'original ;
- concurrence ramenée à une seule identité logique ;
- rollback après erreur, puis transaction suivante fonctionnelle ;
- métriques limitées à `SUCCESS` et `FAILURE`, hors `VOID` ;
- avertissement d'échantillon insuffisant sous 30 résolutions.

## Défauts trouvés et corrigés

1. Le gate de migration copiait temporairement la cible de test dans
   `DATABASE_URL`. Alembic reçoit maintenant une cible explicite en mémoire et
   refuse l'exécution si `DATABASE_URL` est présente.
2. Une URL `postgresql` sélectionnait implicitement le pilote historique non
   installé. Le gate normalise en mémoire vers `postgresql+psycopg` sans
   modifier la cible.
3. La cohérence d'une résolution non-`VOID` reposait uniquement sur
   l'application. Le trigger PostgreSQL recalcule maintenant l'issue depuis les
   scores et refuse les scores ou résultats incohérents.
4. Un test `python -I` dépendait implicitement des paquets système. Il reçoit
   désormais explicitement les chemins isolés nécessaires.

## Tests et contrôles exécutés

- 8 tests PostgreSQL précédemment ignorés : `8 passed` ;
- intégration PostgreSQL B2.4 : `6 passed` ;
- groupe B2.4 ciblé : `41 passed` ;
- suite API complète : `1450 passed` ;
- frontend : `43 passed` ;
- Ruff, TypeScript et ESLint : réussis ;
- builds API et frontend : réussis ;
- `pip check` : aucune dépendance cassée ;
- `pip-audit` limité au projet : aucune vulnérabilité connue ;
- `pnpm audit --prod` : aucune vulnérabilité connue ;
- `detect-secrets` sur fichiers suivis et non suivis non ignorés : aucun
  fichier candidat inattendu ; les candidats restants sont des fixtures,
  hashes, expressions de validation et credentials factices documentés ;
- `git diff --check` : réussi.

## Risques résiduels

- fournisseur unique et modèle non calibré hors échantillon ;
- aucune conclusion de performance autorisée sous 30 résultats valides ;
- avertissements de dépréciation Starlette TestClient et configuration Alembic
  à traiter sans impact sur ce gate ;
- aucune validation de production, aucun appel fournisseur et aucun
  déploiement n'ont été réalisés.

## Erreurs du catalogue concernées

E005, E013, E037–E039, E042–E043, E049–E051, E067–E069 et E074.

## Verdict

`GO_DEPLOY_B2_4`
