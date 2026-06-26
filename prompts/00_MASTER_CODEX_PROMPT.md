# Prompt maitre a envoyer a Codex

Tu travailles dans un depot destine a creer `URIM`, une application d'intelligence et d'analyse predictive sportive reposant exclusivement sur des donnees reelles en production. Son cerveau analytique est `Kairos`.

## Premiere obligation
Avant d'ecrire du code :
1. Lis `AGENTS.md`.
2. Lis `docs/index.md` et les documents obligatoires.
3. Charge les skills pertinents sous `.agents/skills/`.
4. Resume les contraintes non negociables.
5. Audite l'etat du depot.
6. Cree un plan dans `docs/exec-plans/active/`.
7. Indique les outils et extensions necessaires. Pour la phase documentaire, precise qu'aucune extension supplementaire n'est obligatoire.

## But
Creer `URIM` avec :
- `Kairos` comme moteur pre-match ;
- `Half Goals Intelligence Engine` comme coeur produit principal ;
- `HALF_GOAL_DOMINANCE` comme marche principal, avec `FIRST_HALF_MORE_GOALS`, `SECOND_HALF_MORE_GOALS` et `EQUAL_HALF_GOALS` calcules ensemble et normalises a 100 % ;
- plus tard un moteur live separe ;
- une couche multi-fournisseurs dynamique ;
- une base canonique avec provenance par champ ;
- un feature store temporel ;
- des modeles probabilistes calibres ;
- `Kairos Stake Guard` et un `NO_BET Engine` ;
- le statut d'interface `Kairos eveille` uniquement quand `Kairos Stake Guard` retourne `KAIROS_AWAKENED` ;
- des fourchettes prudentes `stake_interval_cdf` en `CDF`, jamais des mises fixes ;
- `Bet Center` avec budget hebdomadaire, solde virtuel, tickets, ROI et resultats utilisateur ;
- `Post-Match Learning Engine` apprenant seulement depuis des resultats officiels verifies ;
- `Official Result Verifier` avant tout apprentissage post-match ;
- `Data Quality Gate` bloquant mocks, conflits critiques et donnees insuffisantes ;
- `Responsible Betting Guard` pour les contenus de pari ;
- model cards et data cards avant promotion ;
- un ledger immuable ;
- une API ;
- `URIM Dashboard` ;
- `Bet Center` ;
- une messagerie entre agents specialises.

Les marches 1X2, totaux de buts, Both Teams To Score, score exact, corners, fautes et cartons restent secondaires tant qu'ils ne renforcent pas le coeur `HALF_GOAL_DOMINANCE`.

## Contraintes absolues
- Pas de donnee illustrative en production.
- Pas de fallback silencieux vers un mock.
- Pas de cle API dans frontend, logs ou Git.
- Pas de donnees futures.
- Pas de split aleatoire pour l'evaluation temporelle.
- Pas de modification retroactive.
- Pas de garantie de 80 %, score exact ou gain.
- Pas de recommandation forcee.
- Pas d'execution de paris dans le MVP.
- Pas de connexion bookmaker dans le MVP.
- Pas de martingale.
- Pas de recuperation des pertes.
- Pas de calcul de mise fonde uniquement sur la probabilite.
- Pas d'apprentissage direct depuis une declaration utilisateur non verifiee.
- Missing reste missing.
- Toute source reelle est horodatee et tracable.
- Distinguer probabilite et confiance : une probabilite elevee n'est pas une garantie, et un `confidence_score` faible peut declencher `NO_BET`.
- Afficher les montants en `CDF` sous forme d'intervalles prudents, jamais comme ordre fixe.

## Stack recommandee avant coding reel
- Frontend : `Next.js + React + TypeScript`.
- Backend intelligence : `FastAPI + Python`.
- Base principale : `PostgreSQL/Supabase` avec `RLS`.
- Cache et rate limit : `Redis`.
- Taches MVP : `Celery`.
- Validation schemas : `Pydantic`.
- Baselines et calibration : `scikit-learn`.
- Tracking et registry : `MLflow`.
- Data quality : `Great Expectations`.
- Observabilite : `OpenTelemetry + Sentry`.
- CI/CD et secrets : `GitHub Actions + GitHub Secrets`.
- Differes : `TimescaleDB`, `Temporal`, live engine avance et `Sportradar` enterprise.

## Sources recommandees
- `API-Football` comme provider principal MVP.
- `Sportmonks` comme provider secondaire.
- `football-data.org` pour validation simple.
- `The Odds API` pour les cotes.
- `StatsBomb Open Data` pour recherche.
- `Sportradar` plus tard en enterprise.

## Phases
1. Gouvernance et contrats.
2. Base et migrations.
3. SDK connecteurs.
4. Premier connecteur reel.
5. Second connecteur et reconciliation.
6. Snapshots temporels.
7. Baselines `Half Goals Intelligence Engine` et walk-forward.
8. Calibration multiclasses `HALF_GOAL_DOMINANCE` et `Kairos Stake Guard`.
9. API et ledger.
10. `URIM Dashboard`, `Bet Center`, `Post-Match Learning Engine`, `Official Result Verifier`, cards et messagerie.
11. Observabilite.
12. Securite et release gate.

Apres chaque phase :
- execute les tests ;
- relis le diff ;
- mets les docs a jour ;
- indique les erreurs E001-E084 prevenues ;
- corrige tout bloquant avant de poursuivre.
