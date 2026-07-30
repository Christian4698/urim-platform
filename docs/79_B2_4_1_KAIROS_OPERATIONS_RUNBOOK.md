# B2.4.1 — Runbook Kairos quotidien

## Périmètre

Cette routine orchestre la collecte sportive, le snapshot analytique, la
résolution post-match et le rapport descriptif. Elle ne consulte aucun
bookmaker, n'utilise aucune cote, ne propose aucune mise et n'exécute aucun
pari.

Les seuils B2.4 restent inchangés :

- probabilité estimée minimale : 0,70 ;
- qualité minimale : 65 ;
- confiance technique minimale : 50 ;
- au moins trois historiques HT/FT par équipe ;
- au moins 30 résolutions valides avant d'afficher autre chose que
  `Échantillon insuffisant`.

## Préconditions

1. Exécuter la commande uniquement depuis le runtime backend autorisé.
2. Vérifier `APP_ENV` et la cible PostgreSQL sans afficher de chaîne de
   connexion.
3. Vérifier que Redis et PostgreSQL sont disponibles avec `/health` et
   `/readiness`.
4. Vérifier que le fournisseur est activé et que son credential est présent
   sans jamais en afficher la valeur.
5. Vérifier l'état Alembic avant toute nouvelle migration. Une routine
   quotidienne n'applique jamais de migration.

## Routine quotidienne

Depuis `apps/api` :

```powershell
urim-daily-operations --date YYYY-MM-DD
urim-daily-operations status
```

La commande prend un verrou distribué Redis et refuse de démarrer si Redis ne
peut pas confirmer l'exclusivité. Elle exécute dans cet ordre :

1. `urim-sports-sync daily-discovery --date YYYY-MM-DD` ;
2. `urim-sports-sync daily-refresh --days 7` ;
3. `urim-kairos-journal snapshot --date YYYY-MM-DD` ;
4. `urim-kairos-journal resolve --date YYYY-MM-DD` ;
5. `urim-kairos-journal report`.

`daily-discovery` et `snapshot` sont critiques. Un échec arrête les étapes
suivantes. Un échec de refresh, resolve ou report dégrade le run et reste
visible dans son résumé ; il ne provoque aucune poursuite silencieuse.

Chaque événement de log JSON porte un `correlation_id`, l'étape, sa durée, son
état et uniquement des compteurs ou codes publics neutralisés. Les URLs,
headers, credentials, payloads fournisseur bruts et chaînes de connexion sont
interdits.

## Vérification des données

Après chaque run :

1. lire le résumé final et confirmer `status=completed` ou examiner toute
   dégradation ;
2. comparer fixtures reçues et retenues ;
3. contrôler les quotas quotidien et minute ;
4. contrôler les snapshots créés, doublons et décisions `NO_BET` ou
   `INSUFFICIENT_DATA` ;
5. contrôler les résolutions créées ;
6. ouvrir `GET /api/v1/kairos/opportunities/today` ;
7. ouvrir `GET /api/v1/kairos/performance`.

Les ressources publiques restent en lecture seule et ne réalisent aucun appel
fournisseur.

## Interprétation de zéro opportunité

Zéro opportunité est un résultat analytique valide, pas une panne. Examiner :

- `evaluated_match_count` ;
- `watchlist_count`, `no_bet_count` et `insufficient_data_count` ;
- `rejection_reason_counts` ;
- `data_freshness` ;
- le message Kairos agrégé.

Une panne est signalée explicitement par un statut HTTP d'erreur, une
dépendance indisponible dans `/readiness` ou un run quotidien en échec.

## Snapshot, resolve et report

Les opérations unitaires restent disponibles :

```powershell
urim-kairos-journal snapshot --date YYYY-MM-DD
urim-kairos-journal resolve --date YYYY-MM-DD
urim-kairos-journal report
```

- `snapshot` est idempotent et uniquement pré-match.
- `resolve` ne traite que les matchs réellement terminés et disponibles après
  le kickoff.
- `report` exclut `VOID` et unresolved des taux observés.
- Une relance avec la même date ne modifie jamais un snapshot existant.

## Panne fournisseur

1. Ne pas fabriquer de fixture ou de statistique.
2. Lire uniquement le code public neutralisé du run.
3. Vérifier activation, quota et statut fournisseur sans afficher de
   credential.
4. Attendre la récupération du fournisseur puis relancer la même date.
5. Conserver `INSUFFICIENT_DATA` tant que les données ne sont pas suffisantes.

L'absence de fournisseur secondaire maintient le risque E004.

## Panne Redis

1. La commande quotidienne et les routes Kairos échouent fermées.
2. Ne pas contourner le verrou par une exécution parallèle manuelle.
3. Vérifier la dépendance Redis dans `/readiness`.
4. Restaurer Redis, confirmer qu'aucun run n'est actif, puis relancer la même
   date.
5. Ne supprimer un verrou que selon la procédure d'incident approuvée et après
   preuve que son propriétaire n'exécute plus aucune étape.

## Panne PostgreSQL

1. Arrêter le workflow au premier échec critique.
2. Vérifier `/readiness`, les limites de connexion et les logs neutralisés.
3. Ne jamais basculer vers une base non authentifiée ou une fixture locale.
4. Après récupération, relancer la même date : les écritures idempotentes
   évitent les doublons.

## Migration

1. Les migrations sont séparées de la routine quotidienne.
2. Vérifier la cible, le head courant, le head attendu et l'absence de
   divergence.
3. Appliquer `alembic upgrade head` une seule fois depuis un processus
   explicitement autorisé.
4. Vérifier ensuite contraintes, triggers, RLS et privilèges.
5. Aucun downgrade de base de production n'est autorisé par ce runbook.

## Contrôle des quotas

Le résumé expose uniquement les compteurs `quota_remaining_daily` et
`quota_remaining_minute`. Si le quota est faible ou épuisé :

1. ne pas multiplier les retries ;
2. conserver les statistiques optionnelles comme manquantes ;
3. prioriser les données indispensables selon le plan B2.3 ;
4. relancer après renouvellement du quota.

## Rotation de secrets

1. Tourner le credential dans le gestionnaire de secrets.
2. Mettre à jour uniquement le runtime backend concerné.
3. Redéployer la version applicative courante.
4. Vérifier `/health`, `/readiness` et un appel contrôlé.
5. Révoquer l'ancien credential.
6. Scanner Git et les logs sans jamais copier la valeur dans un terminal,
   ticket ou document.

## Rollback applicatif sans downgrade DB

1. Désactiver tout auto-déploiement avant l'intervention.
2. Redéployer manuellement le dernier commit applicatif sain.
3. Ne pas exécuter `alembic downgrade`.
4. Conserver les tables et données append-only ajoutées par les migrations
   compatibles.
5. Vérifier health, readiness, logs, opportunities et performance.
6. Documenter le commit restauré et l'incident avant de réactiver un mécanisme
   de déploiement.

## Limites

- Les probabilités B2.4 restent non calibrées.
- Un taux observé est descriptif et ne prédit pas la performance future.
- Sous 30 résolutions valides, l'interface affiche
  `Échantillon insuffisant`.
- `VOID` et unresolved sont toujours exclus du taux observé.
- Les marchés sans observation restent visibles comme `Sans échantillon`.
