# Data Card Template

Chaque dataset, source fournisseur ou snapshot de features utilisable par `Kairos` doit posseder une data card.

La data card decrit origine, licence, couverture, fraicheur, qualite, transformations, restrictions et risques.

## Identite

- `data_card_id`
- provider ou dataset
- version
- proprietaire
- licence
- statut : `DRAFT`, `VALIDATED`, `QUARANTINED`, `RETIRED`

## Couverture

Documenter :
- sport ;
- competitions ;
- saisons ;
- pays ;
- champs disponibles ;
- champs partiels ;
- champs absents ;
- frequence de mise a jour ;
- latence observee.

## Provenance

Chaque champ critique doit porter :
- `provider`
- `provider_event_id`
- `observed_at`
- `fetched_at`
- `available_at`
- `source_version`
- `quality_flags`
- `raw_hash`

## Qualite

Inclure :
- score qualite ;
- taux de missing ;
- taux de conflits ;
- champs critiques manquants ;
- violations Great Expectations ;
- erreurs schema Pydantic ;
- anomalies temporelles ;
- decisions du `Data Quality Gate`.

## Restrictions

Documenter :
- limites de licence ;
- redistribution autorisee ou interdite ;
- quotas ;
- couts ;
- restrictions de stockage ;
- interdiction de mock production.

## Sortie JSON attendue

```json
{
  "data_card_id": "dc_api_football_mvp_2026",
  "provider": "API-Football",
  "status": "VALIDATED",
  "coverage": {
    "sport": "football",
    "competitions": ["MVP_TARGET_ONLY"],
    "half_time_score": "PARTIAL",
    "odds": "PARTIAL"
  },
  "quality": {
    "quality_score": null,
    "missing_rate": null,
    "conflict_rate": null,
    "gate_decision": "PENDING"
  },
  "license": {
    "redistribution": "TO_BE_CONFIRMED",
    "source_url": "https://www.api-football.com/documentation-v3"
  },
  "e_codes": ["E001", "E004", "E005", "E071", "E074"]
}
```

## Erreurs couvertes

E001-E005, E011, E037-E039, E065, E070-E074, E084.
