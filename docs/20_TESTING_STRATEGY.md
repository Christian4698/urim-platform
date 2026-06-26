# Strategie de tests

## Pyramide
Unitaires, contrats, normalisation, integration, temporalite, property-based, end-to-end, charge, securite et regression modele.

## Tests obligatoires
- Futur exclu d'un snapshot passe.
- Lineup et cote posterieures a T exclues.
- Reponse vide reste `missing`.
- Idempotence.
- Divergence critique bloque.
- Aucun secret dans les logs.
- Prediction publiee immuable.
- Production refuse les fixtures et les mocks.
- Live suspendu si latence excessive.
- Provider capabilities testees avant activation.
- Official Result Verifier append-only et multi-source.
- Data Quality Gate retourne `BLOCK`, `QUARANTINED` ou `INSUFFICIENT_DATA` sur conflit critique.
- `fr-CD` et `CDF` presents dans les sorties produit.
- Responsible Betting Guard bloque martingale, recuperation des pertes, promesse de gain et ordre fixe.
- Model cards et data cards presentes avant promotion staging ou production.

## Stack de test recommandee
- Frontend : tests TypeScript/React/Next.js.
- Backend : tests FastAPI/Pydantic.
- Data quality : suites Great Expectations.
- Modeles : walk-forward, calibration, regression modele avec scikit-learn.
- Observabilite : traces OpenTelemetry et erreurs Sentry verifiees en staging.
- CI/CD : GitHub Actions, secrets via GitHub Secrets, jamais en clair.
