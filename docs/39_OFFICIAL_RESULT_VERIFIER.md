# Official Result Verifier

`Official Result Verifier` verifie les resultats officiels apres match avant que `Post-Match Learning Engine` ne puisse apprendre d'un resultat.

Il separe toujours :
- `user_reported_result` : declaration utilisateur dans `Bet Center` ;
- `official_result` : resultat verifie depuis une ou plusieurs sources fiables ;
- `learning_result` : resultat autorise pour recalibration et evaluation.

## Statuts

| Statut | Sens |
|---|---|
| `PENDING` | Verification non terminee. |
| `VERIFIED` | Resultat confirme selon les regles de confiance. |
| `CONFLICT` | Sources officielles ou secondaires divergentes. |
| `INSUFFICIENT_DATA` | Donnees trop pauvres pour conclure. |
| `REJECTED` | Declaration ou observation non utilisable. |

## Donnees necessaires

- `provider`
- `provider_event_id`
- `canonical_match_id`
- `observed_at`
- `fetched_at`
- `available_at`
- `source_version`
- `raw_hash`
- score mi-temps et score final si disponibles
- statut match officiel : scheduled, live, postponed, abandoned, finished
- reason codes de divergence

## Regles de verification

1. Verifier que le match est termine ou officiellement annule.
2. Comparer au moins une source principale et, si possible, une source secondaire.
3. Conserver toutes les observations append-only.
4. Bloquer `learning_result` si les scores critiques divergent.
5. Ne jamais reecrire une prediction `Kairos` publiee.
6. Ne jamais apprendre directement depuis une declaration utilisateur non verifiee.
7. Marquer `INSUFFICIENT_DATA` si le score mi-temps manque pour `HALF_GOAL_DOMINANCE`.

## Journal immuable

Chaque verification cree une entree append-only :
- ancien statut ;
- nouveau statut ;
- observations comparees ;
- hash des payloads ;
- horodatage UTC ;
- version des regles ;
- reason codes.

## Resultat utilisateur vs officiel

Une declaration utilisateur peut servir a :
- afficher un suivi personnel dans `Bet Center` ;
- declencher une verification ;
- detecter une divergence a auditer.

Elle ne peut pas servir a :
- recalibrer un modele ;
- corriger un resultat officiel ;
- modifier retroactivement une prediction ;
- publier une performance Kairos.

## Sortie JSON attendue

```json
{
  "verification_id": "orv_2026_000001",
  "canonical_match_id": "match_123",
  "market": "HALF_GOAL_DOMINANCE",
  "status": "VERIFIED",
  "official_result": {
    "half_time_score": "1-0",
    "full_time_score": "2-1",
    "winning_class": "EQUAL_HALF_GOALS"
  },
  "sources": [
    {
      "provider": "API-Football",
      "provider_event_id": "98765",
      "raw_hash": "sha256:...",
      "available_at": "2026-06-26T18:00:00Z"
    }
  ],
  "learning_allowed": true,
  "reason_codes": ["OFFICIAL_RESULT_VERIFIED"]
}
```

## Erreurs couvertes

E003, E004, E005, E026, E050, E051, E067, E068, E069, E078, E079.
