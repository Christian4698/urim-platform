# Arborescence du kit URIM

```text
URIM/
├── AGENTS.md
├── ARCHITECTURE.md
├── CLAUDE.md
├── PLANS.md
├── QUALITY_SCORE.md
├── README.md
├── RELIABILITY.md
├── SECURITY.md
├── .env.example
├── .gitattributes
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── .agents/
│   └── skills/
│       ├── agent-messaging/
│       ├── backtesting-audit/
│       ├── calibration-evaluation/
│       ├── data-source-onboarding/
│       ├── feature-engineering/
│       ├── half-goals-intelligence/
│       ├── bet-center/
│       ├── kairos-stake-guard/
│       ├── live-match-engine/
│       ├── model-training/
│       ├── no-bet-risk-engine/
│       ├── post-match-learning/
│       ├── prediction-release-gate/
│       ├── provider-reconciliation/
│       ├── security-review/
│       └── temporal-integrity-guard/
├── .claude/
│   └── skills/
│       ├── agent-messaging/
│       ├── backtesting-audit/
│       ├── calibration-evaluation/
│       ├── data-source-onboarding/
│       ├── feature-engineering/
│       ├── half-goals-intelligence/
│       ├── bet-center/
│       ├── kairos-stake-guard/
│       ├── live-match-engine/
│       ├── model-training/
│       ├── no-bet-risk-engine/
│       ├── post-match-learning/
│       ├── prediction-release-gate/
│       ├── provider-reconciliation/
│       ├── security-review/
│       └── temporal-integrity-guard/
├── config/
│   └── provider-registry.example.yaml
├── docs/
│   ├── 00_PROJECT_CHARTER.md
│   ├── 01_PRODUCT_SPEC.md
│   ├── 02_DOMAIN_GLOSSARY.md
│   ├── 03_SYSTEM_ARCHITECTURE.md
│   ├── 04_REAL_DATA_SOURCES.md
│   ├── 05_PROVIDER_CONNECTOR_CONTRACT.md
│   ├── 06_DATA_PROVENANCE.md
│   ├── 07_TEMPORAL_INTEGRITY.md
│   ├── 08_CANONICAL_DATA_MODEL.md
│   ├── 09_FEATURE_STORE.md
│   ├── 10_MODELING_SPEC.md
│   ├── 11_BACKTESTING_PROTOCOL.md
│   ├── 12_CALIBRATION_AND_EVALUATION.md
│   ├── 13_NO_BET_AND_RISK_ENGINE.md
│   ├── 14_LIVE_PREDICTION_ENGINE.md
│   ├── 15_ODDS_AND_VALUE.md
│   ├── 16_AGENT_MESSAGING_SPEC.md
│   ├── 17_SECURITY.md
│   ├── 18_THREAT_MODEL.md
│   ├── 19_RELIABILITY_AND_OBSERVABILITY.md
│   ├── 20_TESTING_STRATEGY.md
│   ├── 21_API_AND_DATABASE_SPEC.md
│   ├── 22_RESPONSIBLE_USE.md
│   ├── 23_FAILURE_CATALOG_84.md
│   ├── 24_ACCEPTANCE_CRITERIA.md
│   ├── 25_ROADMAP.md
│   ├── 26_TOOLS_AND_EXTENSIONS.md
│   ├── 27_INCIDENT_RESPONSE.md
│   ├── 28_PROVIDER_ONBOARDING_CHECKLIST.md
│   ├── 29_HALF_GOALS_INTELLIGENCE_ENGINE.md
│   ├── 34_URIM_BRANDING_AND_KAIROS_ENGINE.md
│   ├── 35_KAIROS_STAKE_GUARD.md
│   ├── 36_BET_CENTER_SPEC.md
│   ├── 37_POST_MATCH_LEARNING_ENGINE.md
│   ├── REFERENCES.md
│   └── exec-plans/
│       ├── TECH_DEBT.md
│       ├── active/
│       │   ├── 000-foundation-plan.md
│       │   ├── 2026-06-26-half-goals-intelligence-engine.md
│       │   ├── 2026-06-26-urim-branding-kairos-stake-guard.md
│       │   └── 2026-06-26-bet-center-post-match-learning.md
│       └── completed/
│           └── 2026-06-26-urim-rename-phase.md
├── manifest.json
├── prompts/
│   ├── 00_MASTER_CODEX_PROMPT.md
│   ├── 01_PHASE_0_AUDIT_PROMPT.md
│   ├── 02_PROVIDER_IMPLEMENTATION_PROMPT.md
│   ├── 03_MODEL_AND_BACKTEST_PROMPT.md
│   └── 04_RELEASE_REVIEW_PROMPT.md
├── schemas/
│   ├── prediction-envelope.schema.json
│   └── provider-observation.schema.json
└── tests/
    └── README.md
```

## Note sur les skills

`.agents/skills/` est la source canonique pour Codex et le `manifest.json`.
`.claude/skills/` est le miroir utilisé par Claude Code.
Les deux répertoires doivent toujours être identiques. Toute mise à jour d'un `SKILL.md` doit être appliquée dans les deux lors du même commit.
