# AGENTS.md — Carte d’instructions Codex pour URIM

## Mission
Construire URIM, un système d’intelligence sportive probabiliste, traçable, sécurisé et explicable. Son cerveau analytique est Kairos. Il ne promet jamais un résultat garanti.

## Nomenclature officielle
- Application : `URIM`
- Nom court produit : `Urim`
- Cerveau analytique / moteur technique : `Kairos`
- Dashboard : `URIM Dashboard`
- Centre de mise : `Bet Center`
- Moteur de mise prudente : `Kairos Stake Guard`
- Propriétaire / créateur possible : `General Tech Consult` / `GTC`

## Ordre de lecture obligatoire
1. `docs/index.md`
2. `docs/00_PROJECT_CHARTER.md`
3. `docs/03_SYSTEM_ARCHITECTURE.md`
4. `docs/06_DATA_PROVENANCE.md`
5. `docs/07_TEMPORAL_INTEGRITY.md`
6. `docs/11_BACKTESTING_PROTOCOL.md`
7. `docs/13_NO_BET_AND_RISK_ENGINE.md`
8. `docs/17_SECURITY.md`
9. `docs/23_FAILURE_CATALOG_84.md`
10. Le `SKILL.md` pertinent sous `.agents/skills/`

## Interdictions absolues
- Ne jamais utiliser une information future pour une prédiction passée.
- Ne jamais présenter un mock, une donnée seedée ou une valeur par défaut comme une donnée réelle.
- Ne jamais exposer les clés API au frontend, dans les logs ou dans Git.
- Ne jamais modifier rétroactivement une prédiction publiée.
- Ne jamais garantir 80 %, 90 %, un score exact ou un bénéfice.
- Ne jamais forcer un conseil : retourner `NO_BET` ou `INSUFFICIENT_DATA`.
- Ne jamais mélanger les métriques pré-match, live et post-match.
- Ne jamais exécuter un pari ou gérer une mise réelle dans le MVP.

## Contrats obligatoires
Toute observation doit porter : `provider`, `provider_event_id`, `observed_at`, `fetched_at`, `available_at`, `source_version`, `quality_flags`, `raw_hash`.

Toute prédiction doit porter : `prediction_id`, `model_version`, `feature_snapshot_id`, `prediction_time`, `market`, `probabilities`, `calibration_bucket`, `decision`, `reasons`, `data_freshness`, `odds_snapshot_id`, `immutable_hash`.

## Definition of Done
- Plan documenté.
- Tests unitaires, intégration, contrat, temporalité et régression.
- Lint, types et sécurité réussis.
- Données réelles distinguées des fixtures.
- Provenance vérifiable.
- Aucun secret commité.
- Documentation mise à jour.
- Rapport de limites et risques produit.
