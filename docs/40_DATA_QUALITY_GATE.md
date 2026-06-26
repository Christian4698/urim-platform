# Data Quality Gate

`Data Quality Gate` decide si une observation, un snapshot de features, un resultat officiel ou une cote peut etre utilise par `Kairos`.

Il combine validation de schema, controles metier, controles temporels, provenance et expectations de donnees.

## Decisions

| Decision | Sens |
|---|---|
| `PASS` | Donnee utilisable. |
| `WARN` | Donnee utilisable avec `quality_flags` et confiance reduite. |
| `BLOCK` | Donnee critique rejetee pour prediction. |
| `QUARANTINED` | Donnee conservee mais isolee pour audit. |
| `INSUFFICIENT_DATA` | Donnee insuffisante pour calculer une sortie fiable. |

## Stack recommandee

- `Pydantic` valide les schemas et types d'entree.
- `Great Expectations` valide les expectations batch et produit une documentation qualite.
- `PostgreSQL/Supabase` conserve les resultats de controles.
- `OpenTelemetry` trace les controles.
- `Sentry` remonte les erreurs de validation et regressions inattendues.

## Controles obligatoires

- Aucun `available_at > prediction_time` pour une prediction passee.
- Aucun champ missing transforme en zero.
- Aucun mock, seed ou fallback silencieux en production.
- Aucun provider sans `raw_hash`.
- Aucun payload brut sans emplacement d'archive.
- Aucune cote sans horodatage et provider.
- Aucun resultat officiel sans statut de verification.
- Aucune prediction si conflit critique non resolu.

## Quality flags

Exemples de `quality_flags` :
- `MISSING_HALF_TIME_SCORE`
- `STALE_ODDS`
- `LOW_PROVIDER_COVERAGE`
- `PROVIDER_CONFLICT`
- `UNVERIFIED_OFFICIAL_RESULT`
- `PARTIAL_LINEUP_COVERAGE`
- `MOCK_BLOCKED_IN_PRODUCTION`
- `TEMPORAL_LEAKAGE_BLOCKED`

## Score qualite fournisseur

Le score qualite ne remplace jamais les controles bloquants.

Il peut tenir compte de :
- taux de champs critiques presents ;
- fraicheur ;
- taux de conflits ;
- latence ;
- erreurs HTTP ;
- quotas restants ;
- stabilite schema ;
- couverture par competition.

## Sortie JSON attendue

```json
{
  "quality_run_id": "dq_2026_000001",
  "scope": "provider_observation",
  "provider": "API-Football",
  "decision": "WARN",
  "quality_score": 0.82,
  "quality_flags": ["PARTIAL_LINEUP_COVERAGE"],
  "blocking_errors": [],
  "warnings": [
    {
      "code": "LOW_PROVIDER_COVERAGE",
      "field": "lineups",
      "message": "Coverage is partial for this competition."
    }
  ],
  "production_mock_allowed": false
}
```

## Erreurs couvertes

E001, E002, E003, E004, E005, E011, E025, E026, E029, E030, E031, E037, E038, E039, E070, E071, E072, E074.
