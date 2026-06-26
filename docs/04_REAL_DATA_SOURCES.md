# Sources de donnees reelles pour URIM

Ces sources alimentent `URIM` via `Kairos` et ne changent pas la politique de donnees reelles du projet.

| Fournisseur | Usage possible | Statut conseille |
|---|---|---|
| API-Football | fixtures, classements, evenements, lineups, statistiques, blessures, cotes selon couverture | `PRIMARY_MVP` |
| Sportmonks | fixtures, livescores, evenements, lineups, sidelined, statistiques et cotes selon plan | `SECONDARY_MVP` |
| football-data.org | calendriers, resultats, classements et equipes | `VALIDATION_ONLY` |
| The Odds API | snapshots de cotes multi-bookmakers | `ODDS_ONLY` |
| StatsBomb Open Data | evenements historiques selon competitions et licence | `RESEARCH_ONLY` |
| Sportradar | donnees B2B et temps reel avance selon contrat | `ENTERPRISE_LATER` |
| Service meteo verifie | contexte du stade a l'heure du match | option |

## Politique
- Declarer competitions, saisons, endpoints, latence, frequence, quotas et licence reellement couverts.
- Une absence de couverture reste `missing`, jamais zero.
- Les predictions d'un fournisseur sont une source distincte, jamais une verite.
- Les reseaux sociaux ne sont pas officiels sans confirmation.
- Scraping non autorise interdit.
- Les restrictions de redistribution sont codees dans le registre.
- Aucune capacite `UNKNOWN`, `MISSING` ou `PARTIAL` ne doit etre masquee.

## Connectivite dynamique
Le systeme accueille plusieurs API via un registre de capacites. Chaque nouveau connecteur doit passer `28_PROVIDER_ONBOARDING_CHECKLIST.md`. La quantite ne remplace jamais la qualite.

La matrice officielle est `38_PROVIDER_CAPABILITY_MATRIX.md`. Une capacite `UNKNOWN`, `MISSING` ou `PARTIAL` doit etre representee explicitement dans les `quality_flags` et peut declencher `INSUFFICIENT_DATA`.

## Stack data recommandee
- Validation de schemas : `Pydantic`.
- Qualite de donnees : `Great Expectations`.
- Base principale : `PostgreSQL/Supabase`.
- Securite multi-utilisateur : `RLS`.
- Cache, quotas et rate limit : `Redis`.
- Taches MVP : `Celery`.
- Workflows durables : `Temporal` plus tard.
- Series temporelles lourdes : `TimescaleDB` plus tard.

## Sources officielles a relire avant activation
- API-Football : https://www.api-football.com/documentation-v3
- Sportmonks : https://docs.sportmonks.com/v3/tutorials-and-guides/tutorials/livescores-and-fixtures/fixtures
- football-data.org : https://www.football-data.org/documentation/api
- The Odds API : https://the-odds-api.com/liveapi/guides/v4/
- StatsBomb Open Data : https://github.com/statsbomb/open-data
- Sportradar Soccer : https://developer.sportradar.com/soccer/docs/soccer-ig-api-basics
