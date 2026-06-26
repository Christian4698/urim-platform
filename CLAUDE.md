# CLAUDE.md - Instructions Claude Code pour URIM

## Lecture obligatoire avant toute action

1. `AGENTS.md` - regles Codex, valides aussi pour Claude Code
2. `docs/index.md`
3. `docs/00_PROJECT_CHARTER.md`
4. `docs/03_SYSTEM_ARCHITECTURE.md`
5. `docs/06_DATA_PROVENANCE.md`
6. `docs/07_TEMPORAL_INTEGRITY.md`
7. `docs/11_BACKTESTING_PROTOCOL.md`
8. `docs/13_NO_BET_AND_RISK_ENGINE.md`
9. `docs/17_SECURITY.md`
10. `docs/23_FAILURE_CATALOG_84.md`
11. Le `SKILL.md` pertinent sous `.claude/skills/`

## Nomenclature officielle

| Role | Nom |
|---|---|
| Application | `URIM` |
| Nom court | `Urim` |
| Cerveau analytique | `Kairos` |
| Dashboard | `URIM Dashboard` |
| Centre de mise | `Bet Center` |
| Moteur prudent | `Kairos Stake Guard` |
| Organisation proprietaire | `General Tech Consult` / `GTC` |

`GTC` ne designe jamais le produit, uniquement l'organisation creatrice.

## Interdictions absolues

- Ne jamais utiliser une information future pour une prediction passee.
- Ne jamais presenter un mock, une donnee seedee ou une valeur par defaut comme reelle.
- Ne jamais exposer une cle API au frontend, dans les logs ou dans Git.
- Ne jamais modifier retroactivement une prediction publiee.
- Ne jamais garantir 80 %, un score exact ou un benefice.
- Ne jamais forcer un conseil : retourner `NO_BET` ou `INSUFFICIENT_DATA`.
- Ne jamais melanger pre-match, live et post-match.
- Ne jamais executer un pari ou gerer une mise reelle dans le MVP.
- Ne jamais connecter un fournisseur reel avant que les prerequis CI soient verts.
- Ne jamais connecter un compte bookmaker dans le MVP.

## Contrats obligatoires

Toute observation doit porter :
`provider`, `provider_event_id`, `observed_at`, `fetched_at`, `available_at`, `source_version`, `quality_flags`, `raw_hash`.

Toute prediction doit porter :
`prediction_id`, `model_version`, `feature_snapshot_id`, `prediction_time`, `market`, `probabilities`, `calibration_bucket`, `decision`, `reasons`, `data_freshness`, `odds_snapshot_id`, `immutable_hash`.

Schemas canoniques : `schemas/prediction-envelope.schema.json` et `schemas/provider-observation.schema.json`.

## Definition of Done

- Plan cree dans `docs/exec-plans/active/` avant tout changement non trivial.
- Tests : unit, contract, integration, temporal, property, e2e, security, load, model-regression.
- Lint, types et scan de securite reussis.
- `ALLOW_TEST_FIXTURES=false` et `ALLOW_PRODUCTION_MOCKS=false` en production.
- Provenance verifiable par champ.
- Aucun secret commite.
- Documentation et `docs/index.md` mis a jour.
- IDs E001-E084 concernes documentes dans la description de PR.
- Plan deplace dans `docs/exec-plans/completed/` a la fin.

## Prerequis avant connexion d'un fournisseur reel

1. `.gitignore` commite et `.env` absent du depot.
2. Secret manager configure, pas de cles dans `.env` local ou CI non chiffre.
3. Registre fournisseur reel (`config/provider-registry.yaml`, pas `.example`).
4. Tests de contrat verts.
5. CI avec suite temporelle bloquante.
6. `Data Quality Gate` actif.
7. Provider capability matrix validee.

## Stack recommandee

- Frontend : `Next.js + React + TypeScript`.
- Backend intelligence : `FastAPI + Python`.
- Base principale : `PostgreSQL/Supabase` avec `RLS`.
- Cache et rate limit : `Redis`.
- Taches MVP : `Celery`.
- Validation schemas : `Pydantic`.
- Baselines/calibration : `scikit-learn`.
- Tracking et registry : `MLflow`.
- Data quality : `Great Expectations`.
- Observabilite : `OpenTelemetry + Sentry`.
- CI/CD et secrets : `GitHub Actions + GitHub Secrets`.
- Differes : `TimescaleDB`, `Temporal`, live engine avance, `Sportradar` enterprise.

## Skills Claude Code

Les 22 skills sont dans `.claude/skills/`. Ils sont une copie de `.agents/skills/` (source canonique Codex).

Regle de synchronisation : toute modification d'un `SKILL.md` doit etre appliquee dans les deux repertoires lors du meme commit.

| Skill | Domaine |
|---|---|
| `agent-messaging` | Messagerie interne des agents |
| `backtesting-audit` | Backtest reproductible chronologique |
| `bet-center` | Budget hebdomadaire, tickets et performance |
| `calibration-evaluation` | Calibration probabiliste et metriques |
| `data-quality-gate` | Validation data quality et blocages |
| `data-source-onboarding` | Integration fournisseur reel |
| `feature-engineering` | Features versionnees sans fuite |
| `half-goals-intelligence` | Marche principal HALF_GOAL_DOMINANCE |
| `kairos-stake-guard` | Fourchettes CDF, exposition et anti-martingale |
| `live-match-engine` | Evenements live et latence |
| `locale-currency-i18n` | Locale `fr-CD`, devise `CDF`, i18n |
| `model-data-card` | Model cards et data cards |
| `model-training` | Entrainement et selection de modeles |
| `no-bet-risk-engine` | Regles ADVICE / WATCH / NO_BET |
| `official-result-verifier` | Verification officielle post-match |
| `post-match-learning` | Verification officielle et apprentissage post-match |
| `prediction-release-gate` | Gate de livraison staging/production |
| `provider-capability-matrix` | Capacites et statuts providers |
| `provider-reconciliation` | Reconciliation multi-fournisseurs |
| `responsible-betting-guard` | Guard responsable betting |
| `security-review` | Audit securite et conformite |
| `temporal-integrity-guard` | Detection de data leakage |

## Erreurs de reference rapide

- Bloquants temporels : E005, E029, E030, E031, E037, E038, E039
- Cles API : E074
- NO_BET obligatoire : E026
- Ledger immuable : E067, E068
- Donnees fictives : E001-E004, E071
- Betting responsable : E075-E084
