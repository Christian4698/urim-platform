# B2.3 — Daily Fixture Discovery

## Objectif

B2.3 alimente chaque jour le socle B1 avec des fixtures réelles exploitables
par Kairos sans dépendre d'une compétition fixe. Le workflow reste backend-only,
pré-match, append-only et sans pari, bookmaker, live automatique ou création de
prédiction officielle.

## Audit de `match_statistics`

`sync_statistics` sélectionne uniquement les matchs terminés qui ne possèdent
pas encore de statistiques. Quand la base ne contient aucun match correspondant,
la liste de requêtes est vide : le run termine correctement à `SUCCEEDED` avec
`request_count=0`.

L'ancien endpoint `/api/v1/sports/sync/status` joignait à ce dernier run les cinq
dernières erreurs globales du fournisseur. Un `provider_unavailable` appartenant
à un run antérieur pouvait donc sembler être la cause du run vide. B2.3 :

- rattache les erreurs publiques au `run_id` affiché;
- inscrit `no_completed_matches_without_statistics` dans le checkpoint d'un
  run de statistiques sans requête;
- enregistre pour les nouveaux incidents une cause neutralisée telle que
  `provider_network_unavailable`, `provider_http_unavailable`,
  `provider_reported_error`, `provider_rate_limited` ou
  `daily_quota_exhausted`;
- ne stocke ni message fournisseur brut, ni URL, ni header, ni credential.

## Configuration runtime

Les commandes vérifient le backend runtime et ne sérialisent que des booléens :

- activation `API_FOOTBALL_ENABLED`;
- présence de `API_FOOTBALL_KEY`;
- présence de `API_FOOTBALL_SEASON`;
- présence de `API_FOOTBALL_PRIORITY_COMPETITIONS`;
- état agrégé `provider_runtime_ready`.

La valeur de la clé n'est jamais affichée. La saison fixe n'est pas utilisée
pour limiter la découverte : la saison de chaque fixture et la couverture
courante annoncées par le fournisseur font foi. La liste de compétitions
prioritaires sert uniquement au classement des candidats.

## Workflow

Pour une date ou une fenêtre métier `Africa/Kinshasa` :

1. appeler `fixtures?date=YYYY-MM-DD&timezone=Africa/Kinshasa` sans filtre de
   ligue, une fois par date et dans l'ordre chronologique;
2. si des fixtures existent, appeler `leagues?current=true`;
3. normaliser les lignes avec provenance et ordre temporel;
4. écarter les matchs hors de la journée locale demandée, non futurs, non
   planifiés, les coupes et les compétitions
   sans couverture classement ou statistiques de fixture;
5. classer les ligues éligibles : priorités configurées d'abord, puis couverture
   statistique, classement, volume de fixtures et identifiant stable;
6. retenir au plus cinq compétitions et uniquement celles dont
   l'enrichissement tient dans le budget restant;
7. charger les équipes de la compétition;
8. charger les résultats terminés des 60 jours antérieurs;
9. conserver une fixture uniquement si chacune de ses équipes possède au moins
   trois résultats récents, seuil minimal exact de Kairos;
10. charger le classement lorsque la couverture fournisseur l'annonce;
11. ingérer compétition, saison, équipes, fixture cible, résultats récents et
    classement;
12. utiliser le quota restant pour les statistiques des matchs historiques,
    avec une sélection récente et équitable entre équipes.

Les écritures utilisent les contraintes append-only et
`ON CONFLICT DO NOTHING` du Programme B1. Une observation identique devient un
doublon comptabilisé; une observation réellement modifiée reste une nouvelle
version traçable.

## Quotas

Le budget effectif est le minimum entre :

- `API_FOOTBALL_MAX_REQUESTS_PER_SYNC` moins les requêtes déjà consommées;
- le quota quotidien restant lorsqu'il est connu;
- le quota minute restant lorsqu'il est connu.

Une requête `fixtures` par date précède le filtrage, puis une requête charge les
métadonnées des ligues si au moins une fixture a été reçue. Le workflow ne
réessaie plus une plage globale `from/to` sans `league` et `season`. Chaque
compétition retenue réserve ensuite :

- une requête équipes;
- une requête résultats récents;
- une requête classement seulement si disponible.

Les statistiques historiques consomment exclusivement le reliquat. Le rapport
compte explicitement les matchs statistiques omis faute de quota.

## Commandes

Depuis `apps/api` :

```powershell
urim-sports-sync daily-discovery --date YYYY-MM-DD
urim-sports-sync daily-refresh --days 7
```

`daily-discovery` accepte aujourd'hui ou une date située dans les 30 prochains
jours selon `Africa/Kinshasa`. `daily-refresh` accepte une fenêtre de 1 à 7
jours et démarre au jour métier Kinshasa courant.

La commande historique `upcoming --days 30` conserve des requêtes par
compétition avec une plage inclusive, `league` et `season`. Elle exige donc :

- `API_FOOTBALL_SEASON`, sinon
  `api_football_season_missing`;
- `API_FOOTBALL_PRIORITY_COMPETITIONS`, sinon
  `api_football_priority_competitions_missing`.

Une fenêtre `upcoming` invalide retourne `upcoming_window_invalid`. Les erreurs
de configuration connues ne sont plus regroupées sous
`synchronization_configuration_invalid`.

## Correctif plage fournisseur

Le mode fautif de `daily-refresh` envoyait `fixtures` avec `from` et `to`, sans
portée `league` et `season`. API-Football a rejeté cette forme après la première
requête. Le corps brut historique n'a volontairement pas été conservé. Le client
classe désormais toute réponse d'erreur à cette forme sous le code public précis
`provider_fixture_range_requires_league_and_season`, sans sérialiser le message
du fournisseur. Le refresh corrigé utilise exclusivement le paramètre `date`.

## Rapport public sûr

La sortie JSON contient :

- nombre de fixtures reçues, retenues et ignorées;
- funnel exclusif `fixtures_received`, `retained`, `rejected_competition`,
  `rejected_season`, `rejected_status`, `rejected_kickoff_window`,
  `rejected_missing_teams`, `rejected_insufficient_coverage`,
  `rejected_duplicate` et `rejected_other`;
- nombre de dates demandées, réussies et échouées;
- raisons agrégées : statut non planifié, horaire passé, métadonnées absentes,
  type de compétition, couverture insuffisante, budget, équipes absentes ou
  historique insuffisant;

Le funnel se réconcilie toujours exactement :

`fixtures_received = retained + somme(rejected_*)`.

Les doublons de ce funnel sont les identités répétées dans le lot fournisseur.
Les doublons PostgreSQL d'une relance idempotente restent suivis séparément et
ne transforment pas une fixture logiquement retenue en rejet.
- compétitions sélectionnées;
- compétitions, saisons, équipes, matchs cibles et résultats récents ajoutés;
- doublons de matchs;
- lignes de classement disponibles;
- matchs statistiques disponibles, indisponibles ou omis faute de quota;
- lignes statistiques ajoutées;
- quota quotidien et minute restant lorsqu'ils sont fournis;
- codes et causes fournisseur neutralisés;
- état booléen de la configuration runtime.

La sortie exclut les fixtures brutes, corps fournisseur, paramètres secrets,
clé API, URLs internes, headers d'authentification et chaînes de connexion.

## Intégrité temporelle

L'instant `started_at` du run borne les événements admissibles. Une fixture
cible doit être future par rapport à cet instant. Les résultats utilisés pour
la forme sont terminés et antérieurs à `started_at`. Chaque réponse conserve
ensuite ses propres heures réelles d'observation et de récupération avec
`observed_at <= available_at <= fetched_at`. Kairos applique toujours son filtre
`available_at <= as_of`; aucune donnée future n'est injectée.

## Limites

- La couverture réelle reste déterminée par API-Football et le plan souscrit.
- Une compétition sans classement et sans statistiques de fixture est ignorée.
- Une compétition peut être omise lorsque le budget ne permet pas son
  enrichissement minimal.
- Les statistiques sont opportunistes après les données indispensables; leur
  absence reste `missing`, jamais zéro.
- Il n'existe toujours pas de fournisseur secondaire.
- Aucune planification Render n'est créée par ce hotfix : l'opérateur conserve
  la responsabilité du déclenchement sécurisé.

## Erreurs du catalogue

B2.3 réduit principalement E001, E002, E003, E005, E009, E011, E039, E065,
E066, E067, E069, E071, E072 et E074. Le risque E004 reste ouvert faute de
second fournisseur.
