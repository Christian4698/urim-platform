# CLAUDE.md — Instructions Claude Code pour URIM

## Lecture obligatoire avant toute action

1. `AGENTS.md` — règles Codex, valides aussi pour Claude Code
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

| Rôle | Nom |
|---|---|
| Application | `URIM` |
| Nom court | `Urim` |
| Cerveau analytique | `Kairos` |
| Dashboard | `URIM Dashboard` |
| Centre de mise | `Bet Center` |
| Moteur prudent | `Kairos Stake Guard` |
| Organisation propriétaire | `General Tech Consult` / `GTC` |

`GTC` ne désigne jamais le produit — uniquement l'organisation créatrice.

## Interdictions absolues

- Ne jamais utiliser une information future pour une prédiction passée.
- Ne jamais présenter un mock, une donnée seedée ou une valeur par défaut comme réelle.
- Ne jamais exposer une clé API au frontend, dans les logs ou dans Git.
- Ne jamais modifier rétroactivement une prédiction publiée.
- Ne jamais garantir 80 %, un score exact ou un bénéfice.
- Ne jamais forcer un conseil : retourner `NO_BET` ou `INSUFFICIENT_DATA`.
- Ne jamais mélanger pré-match, live et post-match.
- Ne jamais exécuter un pari ou gérer une mise réelle dans le MVP.
- Ne jamais connecter un fournisseur réel avant que les cinq prérequis CI soient verts.

## Contrats obligatoires

Toute **observation** doit porter :
`provider`, `provider_event_id`, `observed_at`, `fetched_at`, `available_at`, `source_version`, `quality_flags`, `raw_hash`.

Toute **prédiction** doit porter :
`prediction_id`, `model_version`, `feature_snapshot_id`, `prediction_time`, `market`, `probabilities`, `calibration_bucket`, `decision`, `reasons`, `data_freshness`, `odds_snapshot_id`, `immutable_hash`.

Schémas canoniques : `schemas/prediction-envelope.schema.json` et `schemas/provider-observation.schema.json`.

## Definition of Done

- Plan créé dans `docs/exec-plans/active/` avant tout changement non trivial (modèle dans `PLANS.md`).
- Tests : unit, contract, integration, temporal, property, e2e, security, load, model-regression.
- Lint, types et scan de sécurité réussis (CI vert).
- `ALLOW_TEST_FIXTURES=false` et `ALLOW_PRODUCTION_MOCKS=false` en production.
- Provenance vérifiable par champ.
- Aucun secret commité (scan CI bloquant).
- Documentation et `docs/index.md` mis à jour.
- IDs E001–E084 concernés documentés dans la description de PR.
- Plan déplacé dans `docs/exec-plans/completed/` à la fin.

## Prérequis avant connexion d'un fournisseur réel

1. `.gitignore` commité et `.env` absent du dépôt.
2. Secret manager configuré — pas de clés dans `.env` local ou CI non chiffré.
3. Registre fournisseur réel (`config/provider-registry.yaml`, pas `.example`).
4. Tests de contrat verts.
5. CI avec `temporal` suite bloquante.

## Skills Claude Code

Les 16 skills sont dans `.claude/skills/`. Ils sont une copie de `.agents/skills/` (source canonique Codex).

**Règle de synchronisation** : toute modification d'un `SKILL.md` doit être appliquée dans les deux répertoires lors du même commit.

| Skill | Domaine |
|---|---|
| `agent-messaging` | Messagerie interne des agents |
| `backtesting-audit` | Backtest reproductible chronologique |
| `calibration-evaluation` | Calibration probabiliste et métriques |
| `bet-center` | Budget hebdomadaire, tickets et performance |
| `data-source-onboarding` | Intégration fournisseur réel |
| `feature-engineering` | Features versionnées sans fuite |
| `half-goals-intelligence` | Marché principal HALF_GOAL_DOMINANCE |
| `kairos-stake-guard` | Fourchettes CDF, exposition et anti-martingale |
| `live-match-engine` | Événements live et latence |
| `model-training` | Entraînement et sélection de modèles |
| `no-bet-risk-engine` | Règles ADVICE / WATCH / NO_BET |
| `post-match-learning` | Vérification officielle et apprentissage post-match |
| `prediction-release-gate` | Gate de livraison staging/production |
| `provider-reconciliation` | Réconciliation multi-fournisseurs |
| `security-review` | Audit sécurité et conformité |
| `temporal-integrity-guard` | Détection de data leakage |

## Erreurs de référence rapide

- **Bloquants temporels** : E005, E029, E030, E031, E037, E038, E039
- **Clés API** : E074
- **NO_BET obligatoire** : E026
- **Ledger immuable** : E067, E068
- **Données fictives** : E001–E004, E071
