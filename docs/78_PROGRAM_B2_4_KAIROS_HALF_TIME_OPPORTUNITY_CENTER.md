# B2.4 — Kairos Half-Time & Opportunity Center

## Périmètre

B2.4 ajoute une analyse pré-match des buts par période et un centre
d'opportunités strictement analytique. Il ne crée ni cote, ni mise, ni ticket,
ni ordre bookmaker, ni automatisation live. Les routes publiques restent en
lecture seule et n'appellent jamais API-Football.

Les valeurs manquantes restent `null`. Aucun score HT, événement, H2H ou
résultat n'est inventé ou imputé à zéro.

## Matrice des données

| Donnée | État | Source / endpoint | Coût incrémental B2.4 | Usage |
|---|---|---|---:|---|
| Score HT | disponible dans le schéma et le normaliseur | `fixtures` | 0 quand la fixture ou l'historique est déjà chargé | signal principal |
| Score FT | disponible | `fixtures` | 0 | calcul des buts en seconde période et résolution |
| Résultats récents | disponible | `fixtures` par ligue+saison+plage | coût B2.3 existant | fenêtre de 5 matchs par équipe |
| Domicile / extérieur | disponible | rôles home/away de `fixtures` | 0 | contexte et contrôle de portée |
| Classement | disponible si couverture fournisseur | `standings` | 0 ou 1 par compétition dans B2.3 | qualité et contexte |
| Statistiques équipe / match | partiel selon couverture et quota | `fixtures/statistics` | 1 par match retenu | contexte Kairos B2.2 |
| Minutes de buts | partiel selon couverture et quota | `fixtures/events` | 1 par match enrichi | contrôle de qualité, jamais prérequis |
| H2H récent | partiel | historique local, puis `fixtures/headtohead` si moins de 3 confrontations | 0 ou 1 par paire, maximum 5 appels par run | signal secondaire plafonné à 10 % |
| Statistiques par période | disponible côté fournisseur à partir des saisons couvertes, non requise par le moteur | `fixtures/statistics?half=true` | jusqu'à 2 appels supplémentaires par match | non activé pour préserver le quota |

Le runtime local de développement n'est pas utilisé pour lire une base de
production. Les quantités réelles doivent être auditées depuis une connexion
explicitement autorisée. Sans cette autorisation, cet audit atteste le schéma,
les normaliseurs, les requêtes et les tests, pas un nombre de lignes de
production.

Documentation fournisseur consultée :

- <https://www.api-football.com/documentation?source=post_page>
- <https://www.api-football.com/news/post/how-to-optimize-api-sports-calls-and-quota-usage>

## Ingestion bornée

Le workflow B2.3 conserve la découverte par date et cinq compétitions maximum.
B2.4 :

1. utilise directement les scores HT/FT normalisés des résultats récents ;
2. demande les événements seulement si `coverage.fixtures.events=true` ;
3. conserve uniquement les événements `Goal` nécessaires à Kairos ;
4. répartit le reliquat de quota par paire statistiques+événements ;
5. dérive d'abord le H2H des matchs locaux ;
6. appelle `fixtures/headtohead` seulement sous trois confrontations locales ;
7. limite le H2H à cinq matchs et cinq requêtes par run ;
8. filtre compétition, équipes, statut terminé et instant antérieur au run ;
9. insère avec `ON CONFLICT DO NOTHING` dans les tables append-only.

Le rapport ajoute : appels H2H, H2H reçus/ajoutés/doublons, matchs avec ou sans
événements de but et lignes de buts ajoutées. Les causes fournisseur restent
neutralisées et aucun paramètre, credential ou payload brut n'est sérialisé.

## Moteur mi-temps

Version : `kairos_half_time_b2_4_v1`.

Marchés :

- `FIRST_HALF_MORE_GOALS` ;
- `SECOND_HALF_MORE_GOALS` ;
- `EQUAL_HALF_GOALS` ;
- `FIRST_HALF_OVER_0_5` ;
- `SECOND_HALF_OVER_0_5` ;
- `SECOND_HALF_OVER_1_5`.

Le moteur prend au plus cinq observations HT/FT complètes par équipe et exige
au moins trois observations par équipe. Il déduplique un match présent dans
les deux historiques. Les probabilités empiriques utilisent un lissage de
Laplace : prior uniforme à trois catégories pour la comparaison des périodes
et prior Beta(1,1) pour les marchés binaires.

Le H2H n'a aucune influence sous trois confrontations complètes. Au-delà, son
poids est plafonné à 10 %. Les événements de but minutés augmentent uniquement
le score de qualité ; leur absence n'est jamais interprétée comme zéro but.

Chaque analyse expose la probabilité estimée, la qualité des données, la
confiance technique, les tailles d'échantillon, le risque, les raisons, les
guardrails, l'éligibilité, l'état insuffisant et un hash déterministe. Qualité
et confiance sont plafonnées respectivement à 85 et 65 car le fournisseur est
unique et le modèle non calibré.

## Gate centralisé

Les constantes sont définies dans
`app/modules/kairos/opportunity_config.py` :

- probabilité estimée ≥ 0,70 ;
- qualité ≥ 65 ;
- confiance technique ≥ 50 ;
- source cible fraîche ;
- aucun guardrail critique ;
- données suffisantes.

Un match possède au plus une analyse primaire et deux alternatives. Par
prudence, les six marchés mi-temps forment un seul groupe corrélé et les trois
doubles chances un second : une sélection ne peut contenir qu'un élément de
chaque groupe. Une analyse bloquée ne publie ni primaire ni alternative et
retourne `NO_BET` ou `INSUFFICIENT_DATA`.

## API et interface

`GET /api/v1/kairos/opportunities/today` :

- lit exclusivement PostgreSQL local ;
- utilise le rate limiting Redis fail-closed ;
- limite l'évaluation à 16 matchs et la réponse à 12 ;
- n'effectue aucune écriture ni aucun appel fournisseur ;
- expose les seuils exacts et les métriques du journal résolu uniquement.

La page `/opportunities` présente les sections ≥70 %, mi-temps, marchés de
buts, double chance, à surveiller et NO_BET. Le détail match affiche les six
analyses mi-temps, y compris l'état insuffisant.

## Journal append-only

La migration `202607280001` crée deux tables séparées des prédictions
officielles :

- `kairos_analysis_journal` pour les snapshots pré-match autorisés ;
- `kairos_analysis_resolutions` pour une résolution post-match unique.

Les deux tables ont un trigger interdisant `UPDATE` et `DELETE`, RLS activée,
des identités et hashes uniques et des contrôles temporels. La route GET ne
persiste rien. Les opérations sont explicites :

```text
urim-kairos-journal snapshot --date YYYY-MM-DD
urim-kairos-journal resolve --date YYYY-MM-DD
urim-kairos-journal report
```

La résolution utilise uniquement la dernière observation réelle terminée,
disponible à `as_of`. Un score absent, incohérent ou un marché inconnu donne
`VOID`, jamais un échec fabriqué. Les taux observés et segments par marché
incluent seulement `SUCCESS` et `FAILURE`. Sous 30 résultats résolus,
l'interface interdit explicitement toute conclusion de performance ou de
calibration.

## Limites et risques résiduels

- Un seul fournisseur : qualité plafonnée et aucun arbitrage inter-provider.
- Modèle non calibré hors échantillon : les probabilités sont des estimations,
  pas des taux observés.
- Les événements minutés et H2H restent opportunistes sous contrainte de quota.
- Les statistiques par période `half=true` ne sont pas ingérées : les scores
  HT/FT suffisent au moteur actuel.
- Le journal requiert la migration et une planification opérateur ; aucune
  planification ou écriture de production n'est effectuée par cette mission.
- Sans PostgreSQL de test isolée, l'intégration migration réelle reste un gate
  séparé et ne doit jamais cibler la production.
