# Plan actif - Finalisation technologies, sources fiables et skills URIM

Date : 2026-06-26
Statut : actif
Portee : specifications documentaires, inventaire et skills locaux
Produit : `URIM`
Moteur analytique : `Kairos`
Coeur produit : `Half Goals Intelligence Engine`

## Objectif
Finaliser les technologies indispensables, les sources fiables, les modules de controle et les derniers skills avant le debut du coding reel de `URIM`.

## Contraintes
- Ne pas coder de connecteur API reel.
- Ne pas connecter un compte bookmaker dans le MVP.
- Ne pas executer de mise reelle.
- Ne jamais utiliser de donnees fictives en production.
- Ne jamais faire de fallback mock silencieux.
- Ne jamais exposer de cles API au frontend, dans les logs ou dans Git.
- Ne jamais apprendre directement depuis un gain utilisateur non verifie.
- Ne jamais modifier une prediction publiee.
- Ne jamais promettre de gain ou de taux de reussite garanti.
- Conserver `HALF_GOAL_DOMINANCE` comme marche principal.

## Fichiers a creer
- `docs/38_PROVIDER_CAPABILITY_MATRIX.md`
- `docs/39_OFFICIAL_RESULT_VERIFIER.md`
- `docs/40_DATA_QUALITY_GATE.md`
- `docs/41_LOCALE_CURRENCY_I18N.md`
- `docs/42_RESPONSIBLE_BETTING_GUARD.md`
- `docs/43_MODEL_CARD_TEMPLATE.md`
- `docs/44_DATA_CARD_TEMPLATE.md`
- `.agents/skills/provider-capability-matrix/SKILL.md`
- `.agents/skills/official-result-verifier/SKILL.md`
- `.agents/skills/data-quality-gate/SKILL.md`
- `.agents/skills/locale-currency-i18n/SKILL.md`
- `.agents/skills/responsible-betting-guard/SKILL.md`
- `.agents/skills/model-data-card/SKILL.md`
- `.claude/skills/provider-capability-matrix/SKILL.md`
- `.claude/skills/official-result-verifier/SKILL.md`
- `.claude/skills/data-quality-gate/SKILL.md`
- `.claude/skills/locale-currency-i18n/SKILL.md`
- `.claude/skills/responsible-betting-guard/SKILL.md`
- `.claude/skills/model-data-card/SKILL.md`

## Fichiers a mettre a jour
- `docs/index.md`
- `docs/04_REAL_DATA_SOURCES.md`
- `docs/20_TESTING_STRATEGY.md`
- `docs/21_API_AND_DATABASE_SPEC.md`
- `docs/22_RESPONSIBLE_USE.md`
- `prompts/00_MASTER_CODEX_PROMPT.md`
- `KIT_TREE.md`
- `CLAUDE.md`
- `manifest.json`

## Stack retenue
- Frontend : `Next.js + React + TypeScript`.
- Backend intelligence : `FastAPI + Python`.
- Base principale : `PostgreSQL/Supabase`.
- Securite multi-utilisateur : `RLS`.
- Cache et rate limit : `Redis`.
- Taches MVP : `Celery`.
- Validation schemas : `Pydantic`.
- Baselines et calibration : `scikit-learn`.
- Tracking et registre modele : `MLflow`.
- Qualite donnees : `Great Expectations`.
- Observabilite : `OpenTelemetry + Sentry`.
- CI/CD et secrets : `GitHub Actions + GitHub Secrets`.

## Stack differee
- `TimescaleDB` pour les series temporelles lourdes.
- `Temporal` pour les workflows durables.
- `Sportradar` comme option enterprise.
- Live engine avance comme phase future.

## Providers retenus
- `API-Football` : provider principal MVP.
- `Sportmonks` : provider secondaire.
- `football-data.org` : validation simple.
- `The Odds API` : cotes.
- `StatsBomb Open Data` : recherche.
- `Sportradar` : option enterprise.

## Validation
- Rechercher les technologies retenues et differees dans les specs attendues.
- Rechercher `NO_BET`, `INSUFFICIENT_DATA`, `mock`, `fallback`, `bookmaker`, `mise reelle`, `martingale`, `gain garanti`, `fr-CD`, `CDF`.
- Executer `git diff --check`.
- Verifier les hashes des skills `.agents` et `.claude`.
- Verifier `python -m json.tool manifest.json`.
- Si `quick_validate.py` est absent, verifier manuellement le frontmatter `name` + `description`.

## Erreurs E001-E084 concernees
E001-E005, E011, E013-E026, E029-E031, E037-E062, E063-E074 et E075-E084.
