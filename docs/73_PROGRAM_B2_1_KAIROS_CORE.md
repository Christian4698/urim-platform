# Programme B2.1 — Kairos Core backend-only

## Statut et périmètre

B2.1 active une analyse pré-match 1X2 calculée à la demande depuis les
observations API-Football déjà stockées par B1. Le module est backend-only,
read-only et sans appel fournisseur.

Ce n'est pas un modèle ML, une preuve de calibration, une recommandation
financière ou une promesse de résultat. Aucune cote, aucun bookmaker, aucune
mise, aucun placement de pari et aucune automatisation live ne sont ajoutés.
La décision exposée est toujours `NO_BET` ou `INSUFFICIENT_DATA`.

## Architecture

```text
Tables B1 append-only
  ├─ api_football_matches
  ├─ api_football_standings
  ├─ api_football_match_statistics
  └─ api_football_match_events
             │
             ▼
KairosRepository
  ├─ provider = api-football
  ├─ available_at <= as_of
  ├─ fetched_at <= as_of
  ├─ created_at <= as_of
  ├─ même compétition et même saison
  ├─ kickoff historique < as_of
  └─ match cible exclu de l'historique
             │
             ▼
Snapshot de features en mémoire
  ├─ fenêtre récente fixe de 5 matchs
  ├─ missing distinct de zéro
  ├─ provenance et hashes sources
  └─ feature_snapshot_hash déterministe
             │
             ▼
Baseline Poisson 1X2 déterministe
             │
             ▼
GET /api/v1/kairos/matches/{id}/analysis
```

Le repository ne contient aucun `INSERT`, `UPDATE`, `DELETE`, appel réseau ou
accès aux tables de cotes. Le GET ne provoque aucun effet de bord.

## Contrat temporel

`as_of` est obligatoire dans le calcul interne et vaut l'heure UTC de la
requête lorsqu'il n'est pas fourni par le client.

Une observation contribue uniquement lorsque ses trois horodatages locaux et
fournisseur satisfont :

```text
observed_at <= available_at <= fetched_at <= created_at <= as_of
```

Le match cible doit avoir un coup d'envoi strictement postérieur à `as_of` et
un statut `NS` ou `TBD`. Une demande au coup d'envoi ou après celui-ci est
bloquée pour empêcher tout mélange pré-match/live. Un `as_of` futur ou sans
fuseau horaire est refusé. Un match historique, même marqué terminé, est
également refusé lorsque son `kickoff_at` est supérieur ou égal à `as_of`.
Cette seconde défense protège le service contre une ligne fournisseur
temporellement incohérente.

## Registre des features

Toutes les features appartiennent au domaine `pre_match_1x2`, portent une
version `v1`, utilisent une fenêtre maximale de cinq matchs et un TTL issu de
`API_FOOTBALL_FRESHNESS_MINUTES`.

| Feature | Dépendances | Missing |
|---|---|---|
| `recent_form` | résultats terminés, équipe, `as_of` | null, jamais zéro implicite |
| `standings` | classement, compétition, saison, `as_of` | null |
| `home_away` | résultats terminés avec split de lieu | null |
| `goals` | score final ou buts finaux disponibles | null; `0-0` reste valide |
| `shots` | `Total Shots`, repli sur `Shots on Goal` | null |
| `possession` | `Ball Possession` | null |
| `corners` | `Corner Kicks` | null |
| `cards` | cartons jaunes + 2 × rouges, événements en repli | null |

Les statistiques non numériques, `NaN`, infinies, négatives ou hors bornes
de sécurité sont traitées comme manquantes et réduisent la couverture; elles
ne deviennent jamais un zéro implicite. Un score final négatif ou supérieur à
100 buts par équipe est également rejeté comme valeur aberrante.

La forme utilise 3 points pour une victoire, 1 pour un nul et 0 pour une
défaite. Le classement utilise le rang et les points par match lorsque les
deux valeurs existent. Les moyennes de buts sont séparées selon le rôle de
l'équipe dans chaque match et le split domicile/extérieur.

La force de l'opposition n'est pas encore ajustée individuellement en B2.1. Le
périmètre identique compétition+saison limite le mélange de domaines mais ne
remplace pas cet ajustement.

## Calcul probabiliste

Le taux de buts domicile combine :

- les buts récemment marqués par l'équipe à domicile;
- les buts récemment encaissés par l'équipe visiteuse;
- les mêmes mesures dans les splits domicile et extérieur disponibles.

Le taux extérieur est construit symétriquement. Les signaux forme, classement,
domicile/extérieur, tirs, possession, corners et cartons appliquent ensuite des
modificateurs logarithmiques bornés. Aucune valeur sportive par défaut n'est
injectée.

Une distribution de Poisson indépendante, tronquée à dix buts puis
renormalisée, produit les probabilités `home_win`, `draw` et `away_win`. Elles
somment à 1. Ce choix est explicable mais suppose une indépendance simplifiée
des scores et n'intègre pas encore Dixon-Coles, force d'opposition,
compositions, blessures pondérées ou changement d'entraîneur.

Moins de trois résultats complets par équipe produit :

- `analysis_status=insufficient_data`;
- `decision=INSUFFICIENT_DATA`;
- probabilités `null`;
- `confidence_score=0`;
- avertissement bloquant explicite.

## Qualité et confiance

`data_quality_score` est un score 0–100 de couverture, pondéré ainsi :

| Composant | Poids |
|---|---:|
| forme récente | 16 % |
| classement | 12 % |
| domicile/extérieur | 12 % |
| buts | 22 % |
| tirs | 10 % |
| possession | 9 % |
| corners | 8 % |
| cartons | 6 % |
| provenance | 5 % |

Les drapeaux invalides, conflits, stale ou unknown et la fraîcheur du match
cible réduisent le score. La dépendance à un fournisseur unique plafonne la
qualité à 85.

`confidence_score` mesure la fiabilité technique de l'analyse, pas la
probabilité d'un résultat. Il combine qualité, taille d'échantillon et
cohérence directionnelle des signaux. Il est plafonné à 65 tant qu'aucune
calibration walk-forward indépendante n'est disponible.

Le drift n'est pas mesurable sans historique versionné d'analyses B2.1. Le
statut `drift_monitoring_status=not_available` et un avertissement explicite
empêchent de masquer cette limite.

## API read-only

| Méthode et route | Rôle |
|---|---|
| `GET /api/v1/kairos/methodology` | versions, registre, fenêtres et restrictions |
| `GET /api/v1/kairos/matches/{provider_match_id}/analysis?as_of=...` | analyse 1X2 pré-match |

`POST`, `PUT`, `PATCH` et `DELETE` ne sont pas définis.

`provider_match_id` doit être la représentation ASCII canonique d'un entier
PostgreSQL `BIGINT` strictement positif. Les signes, zéros initiaux, chiffres
Unicode, identifiants non numériques, charges d'injection et entiers hors plage
sont rejetés avant toute ouverture de session DB.

La réponse d'analyse contient les champs demandés :

- `home_win_probability`, `draw_probability`,
  `away_win_probability`;
- `confidence_score`, `data_quality_score`;
- `reasons`, directement reliées aux features calculées;
- `warnings`, incluant calibration, données manquantes, source unique, drift,
  restriction pré-match et absence de betting.

Elle conserve aussi le contrat d'audit :

- `prediction_id`, `model_version`, `feature_snapshot_id`,
  `prediction_time`, `market`, `probabilities`;
- `calibration_bucket`, `safety_decision`, `data_freshness`,
  `odds_snapshot_id=null`, `immutable_hash`;
- `analytical_suggestion`, distincte du garde-fou;
- `decision` et `suggestion`, conservés uniquement comme alias de
  compatibilité des deux champs explicites;
- IDs et hashes des observations sources, `feature_snapshot_hash` et
  `max_available_at`;
- drapeaux `read_only=true`, `persisted=false`,
  `official_prediction_published=false`,
  `automatic_betting_enabled=false` et
  `live_automatic_enabled=false`.

## Migration

Aucune migration B2.1 n'est nécessaire. Les tables B1 contiennent déjà les
observations requises. Le snapshot et l'analyse sont déterministes mais restent
en mémoire : ils ne sont pas publiés dans le ledger.

La persistance append-only d'une prédiction officielle nécessitera une phase
séparée avec calibration, release gate, modèle versionné, migration dédiée et
tests d'immuabilité.

## Sécurité

- aucun secret ou nom de secret n'est sérialisé;
- les erreurs de base sont neutralisées;
- le fournisseur, les identifiants de provenance et les hashes SHA-256 sont
  validés avant calcul;
- les types de statistiques sont allowlistés et les volumes d'historique,
  statistiques et événements sont bornés;
- les réponses Kairos sont `no-store`, les paramètres inconnus ou dupliqués
  sont rejetés et les erreurs de validation ne réfléchissent pas les entrées;
- PostgreSQL est placé en transaction read-only avec un timeout SQL local de
  trois secondes pour chaque analyse;
- le débit est limité par client dans Redis avec une fenêtre glissante atomique
  fondée sur l'heure serveur, une clé client hachée et une expiration bornée;
- Redis est fail-closed : une configuration absente, une panne, un timeout ou
  une réponse invalide produit un 503 avant toute ouverture de session
  PostgreSQL; la readiness exige simultanément PostgreSQL et Redis;
- OpenAPI et les interfaces de documentation sont désactivés hors des
  environnements explicitement locaux ou de test;
- les routes n'appellent jamais API-Football;
- aucune donnée fixture n'est présentée comme réelle;
- la CSP, le CORS exact, les headers de sécurité et `Permissions-Policy`
  s'appliquent aux réponses;
- les flags bookmaker, betting réel et live restent désactivés.

## Validation

```powershell
pnpm api:lint
pnpm api:test
pnpm api:build
pnpm contracts:validate
pnpm web:lint
pnpm web:typecheck
pnpm web:test
pnpm web:build
pnpm audit --prod
git diff --check
```

Les tests B2.1 couvrent le calcul déterministe, la somme à 1, les zéros réels,
les valeurs manquantes ou non finies, le minimum d'historique, la compilation
SQL read-only et bornée, la validation des IDs, les routes, les erreurs
neutralisées, le refus live, les conflits de provenance et des injections
adversariales d'observations ou de matchs futurs. Le rapport Fortress Mode
complet est dans `74_B2_1_FORTRESS_MODE_PENTEST.md`.

## Limites et risques

- fournisseur unique sans réconciliation;
- baseline non calibrée et non validée walk-forward;
- absence de force d'opposition individualisée;
- couverture variable des statistiques selon la compétition;
- cartons basés sur une pondération simple;
- Poisson indépendant sans correction des faibles scores;
- pas de compositions, blessures pondérées, fatigue ou changement de régime;
- aucun suivi opérationnel du drift sans ledger historique;
- Redis est une dépendance de sécurité et de disponibilité : une panne bloque
  volontairement les deux endpoints Kairos;
- l'identité client dépend de l'adresse fournie par le serveur ASGI; la chaîne
  de proxies Render/Uvicorn doit être testée avec une allowlist de proxies de
  confiance pour éviter de regrouper tous les clients ou de faire confiance à
  un `X-Forwarded-For` forgé;
- l'intégration du script Lua contre une instance Redis réelle doit être
  validée dans un environnement isolé avant le GO production;
- l'authenticité cryptographique de la provenance n'est pas garantie par un
  simple SHA-256 si un acteur possède déjà un droit d'écriture en base;
- aucune analyse live, cote, valeur attendue, mise ou exécution de pari.

IDs du catalogue principalement couverts ou explicitement signalés :
E001, E002, E004, E005, E008, E009, E011, E013, E016, E021, E022, E025,
E026, E028, E039, E040, E042, E049, E064, E066, E069, E070, E071, E074,
E075, E076, E077 et E084.
