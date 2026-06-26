# Provider Capability Matrix

Ce document fixe la matrice de capacite fournisseur pour `URIM`.

Il ne connecte aucune API reelle. Il sert a choisir, auditer et activer progressivement les sources utilisees par `Kairos`.

## Statuts fournisseur

| Statut | Sens |
|---|---|
| `PRIMARY_MVP` | Fournisseur principal du MVP, active seulement apres checklist et tests de contrat. |
| `SECONDARY_MVP` | Fournisseur de comparaison ou de secours controle. |
| `VALIDATION_ONLY` | Source simple de verification, jamais verite unique pour tous les marches. |
| `ODDS_ONLY` | Source de cotes horodatees, separee des resultats sportifs. |
| `RESEARCH_ONLY` | Donnees de recherche ou prototype, jamais production sans validation licence. |
| `ENTERPRISE_LATER` | Option future selon budget, contrat et couverture. |

## Etats de capacite

| Etat | Sens |
|---|---|
| `SUPPORTED` | Capacite documentee, testee et couverte par contrat fournisseur. |
| `PARTIAL` | Capacite disponible seulement sur certains pays, ligues, saisons ou plans. |
| `MISSING` | Capacite absente ou non achetee. |
| `UNKNOWN` | Capacite non confirmee par documentation ou test. |
| `FUTURE` | Capacite utile mais hors MVP. |

## Providers recommandes

| Provider | Statut | Usage URIM | Limites |
|---|---|---|---|
| `API-Football` | `PRIMARY_MVP` | fixtures, scores, evenements, lineups, statistiques, blessures, odds selon couverture | Couverture variable par competition et plan. |
| `Sportmonks` | `SECONDARY_MVP` | fixtures, livescores, events, lineups, sidelined, statistiques, odds selon plan | A utiliser pour reconciliation et secours, pas comme ecrasement silencieux. |
| `football-data.org` | `VALIDATION_ONLY` | calendriers, resultats, classements, equipes | Validation simple, couverture plus limitee pour features fines. |
| `The Odds API` | `ODDS_ONLY` | snapshots de cotes multi-bookmakers | Ne donne pas les resultats officiels sportifs. |
| `StatsBomb Open Data` | `RESEARCH_ONLY` | evenements historiques et recherche analytique | Licence et competitions limitees, pas production live. |
| `Sportradar` | `ENTERPRISE_LATER` | donnees B2B, couverture avancee, live et enterprise | Cout, contrat et integration hors MVP. |

## Matrice MVP

| Capacite | API-Football | Sportmonks | football-data.org | The Odds API | StatsBomb Open Data | Sportradar |
|---|---|---|---|---|---|---|
| Fixtures | `SUPPORTED` | `SUPPORTED` | `SUPPORTED` | `PARTIAL` | `PARTIAL` | `FUTURE` |
| Scores FT | `SUPPORTED` | `SUPPORTED` | `SUPPORTED` | `MISSING` | `PARTIAL` | `FUTURE` |
| Scores mi-temps | `PARTIAL` | `PARTIAL` | `UNKNOWN` | `MISSING` | `PARTIAL` | `FUTURE` |
| Evenements buts | `PARTIAL` | `PARTIAL` | `MISSING` | `MISSING` | `SUPPORTED` | `FUTURE` |
| Lineups | `PARTIAL` | `PARTIAL` | `PARTIAL` | `MISSING` | `PARTIAL` | `FUTURE` |
| Blessures/suspensions | `PARTIAL` | `PARTIAL` | `MISSING` | `MISSING` | `MISSING` | `FUTURE` |
| Statistiques match | `PARTIAL` | `PARTIAL` | `MISSING` | `MISSING` | `SUPPORTED` | `FUTURE` |
| Corners | `PARTIAL` | `PARTIAL` | `MISSING` | `MISSING` | `PARTIAL` | `FUTURE` |
| Fautes/cartons | `PARTIAL` | `PARTIAL` | `MISSING` | `MISSING` | `PARTIAL` | `FUTURE` |
| Cotes pre-match | `PARTIAL` | `PARTIAL` | `MISSING` | `SUPPORTED` | `MISSING` | `FUTURE` |
| Official result verification | `SUPPORTED` | `SUPPORTED` | `SUPPORTED` | `MISSING` | `PARTIAL` | `FUTURE` |

## Regles d'activation

- Une capacite `UNKNOWN` ou `MISSING` ne peut pas alimenter une prediction de production.
- Une capacite `PARTIAL` doit porter un `quality_flag` explicite et peut declencher `INSUFFICIENT_DATA`.
- Une source unique non verifiee ne doit pas devenir la verite systeme pour un resultat critique.
- Les observations divergentes restent toutes conservees avec provenance par champ.
- Aucun fallback mock silencieux n'est autorise en production.
- Les cles API restent cote serveur, via secrets chiffrés.

## Sortie JSON attendue

```json
{
  "provider": "API-Football",
  "status": "PRIMARY_MVP",
  "capabilities": {
    "fixtures": "SUPPORTED",
    "half_time_score": "PARTIAL",
    "odds": "PARTIAL",
    "corners": "PARTIAL"
  },
  "coverage_scope": {
    "sports": ["football"],
    "competitions": ["MVP_TARGET_ONLY"],
    "live": "FUTURE"
  },
  "activation_gate": {
    "contract_tests": "REQUIRED",
    "data_quality_gate": "REQUIRED",
    "server_side_secret": "REQUIRED",
    "production_mocks": "FORBIDDEN"
  }
}
```

## Sources officielles

- API-Football : https://www.api-football.com/documentation-v3
- Sportmonks : https://docs.sportmonks.com/v3/tutorials-and-guides/tutorials/livescores-and-fixtures/fixtures
- football-data.org : https://www.football-data.org/documentation/api
- The Odds API : https://the-odds-api.com/liveapi/guides/v4/
- StatsBomb Open Data : https://github.com/statsbomb/open-data
- Sportradar Soccer : https://developer.sportradar.com/soccer/docs/soccer-ig-api-basics

## Erreurs couvertes

E001, E002, E003, E004, E005, E011, E065, E070, E071, E072, E074.
