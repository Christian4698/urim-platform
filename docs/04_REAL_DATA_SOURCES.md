# Sources de données réelles pour URIM

Ces sources alimentent `URIM` via `Kairos` et ne changent pas la politique de données réelles du projet.

| Fournisseur | Usage possible | Statut conseillé |
|---|---|---|
| API-Football | fixtures, classements, événements, lineups, statistiques, blessures, cotes selon couverture | MVP |
| Sportmonks | fixtures, livescores, événements, lineups, sidelined, statistiques et cotes selon plan | MVP/secondaire |
| football-data.org | calendriers, résultats, classements et équipes | validation/secours |
| StatsBomb Open Data | événements historiques selon compétitions et licence | recherche/prototype |
| The Odds API | snapshots de cotes multi-bookmakers | cotes |
| Sportradar | données B2B et temps réel avancé selon contrat | enterprise |
| Service météo vérifié | contexte du stade à l’heure du match | option |

## Politique
- Déclarer compétitions, saisons, endpoints, latence, fréquence, quotas et licence réellement couverts.
- Une absence de couverture reste `missing`, jamais zéro.
- Les prédictions d’un fournisseur sont une source distincte, jamais une vérité.
- Les réseaux sociaux ne sont pas officiels sans confirmation.
- Scraping non autorisé interdit.
- Les restrictions de redistribution sont codées dans le registre.

## Connectivité dynamique
Le système accueille plusieurs API via un registre de capacités. Chaque nouveau connecteur doit passer `28_PROVIDER_ONBOARDING_CHECKLIST.md`. La quantité ne remplace jamais la qualité.
