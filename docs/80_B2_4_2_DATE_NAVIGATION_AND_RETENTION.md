# B2.4.2 — Navigation par date et diagnostic de rétention

## Journée métier

La journée utilisateur unique est `Africa/Kinshasa`. Les instants restent
stockés et comparés comme timestamps timezone-aware en UTC dans PostgreSQL.
Une date métier est toujours convertie en intervalle demi-ouvert entre deux
minuits Kinshasa successifs.

Exemple pour le 31 juillet 2026 :

```text
[2026-07-30T23:00:00Z, 2026-07-31T23:00:00Z)
```

Cette même définition est utilisée par la découverte, le refresh, les
snapshots, la résolution, les endpoints Kairos et les vues frontend.

## API en lecture seule

Les routes historiques restent compatibles :

```text
GET /api/v1/kairos/suggestions/today
GET /api/v1/kairos/opportunities/today
```

Les routes datées acceptent une date ISO civile unique, canonique et comprise
entre 1900 et 2100 :

```text
GET /api/v1/kairos/suggestions?date=YYYY-MM-DD
GET /api/v1/kairos/opportunities?date=YYYY-MM-DD
```

Un paramètre absent, invalide, dupliqué ou inconnu est rejeté. Les routes
datées n'acceptent aucun `as_of` fourni par le client. Elles utilisent un
instant serveur UTC unique et conservent les contrôles `available_at <= as_of`,
`fetched_at <= as_of` et `created_at <= as_of`.

## Navigation frontend

Suggestions et Opportunity Center proposent :

- Aujourd'hui ;
- Demain ;
- les sept prochaines dates ;
- la date effectivement consultée ;
- l'heure locale Kinshasa.

Une seule date est chargée et affichée à la fois. Une carte dont le kickoff
n'appartient pas à la date Kinshasa demandée est rejetée par le contrat
frontend. Une opportunité du 31 juillet ne peut donc jamais apparaître dans la
vue du 30 juillet.

## Funnel de rétention

Chaque run de découverte publie et persiste dans son checkpoint :

```text
fixtures_received
retained
rejected_competition
rejected_season
rejected_status
rejected_kickoff_window
rejected_missing_teams
rejected_insufficient_coverage
rejected_duplicate
rejected_other
```

Invariant :

```text
fixtures_received = retained + somme(rejected_*)
```

`rejected_duplicate` vise uniquement une identité répétée dans le lot
fournisseur. Les doublons PostgreSQL issus d'une relance idempotente restent
distincts. Le statut neutralisé de `urim-daily-operations status` refuse un
funnel incomplet, négatif, non entier ou non réconcilié.

## Compétitions

Kairos utilise le nom de la dernière observation de compétition réellement
disponible à l'instant d'analyse. Si ce nom n'est pas disponible, l'interface
affiche un libellé neutre et ne fabrique pas `Compétition <id>`.

## Limites et sécurité

- aucune migration B2.4.2 ;
- aucun bookmaker, aucune cote, aucune mise et aucune exécution automatique ;
- aucune modification des seuils analytiques ;
- aucun appel fournisseur depuis le frontend ;
- les endpoints recalculent une vue en lecture seule depuis les observations
  disponibles ; ils ne reconstruisent pas une carte complète depuis le journal
  append-only après le kickoff.

Les principaux risques suivis sont E003, E005, E066, E071, E072, E074 et E084.
