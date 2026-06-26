---
name: data-quality-gate
description: Specifier, auditer ou implementer le Data Quality Gate URIM, incluant validations Pydantic, Great Expectations, quality flags, decisions PASS/WARN/BLOCK/QUARANTINED/INSUFFICIENT_DATA et blocage des mocks production.
---

# data-quality-gate

1. Lire `docs/40_DATA_QUALITY_GATE.md`, `docs/06_DATA_PROVENANCE.md`, `docs/07_TEMPORAL_INTEGRITY.md` et `docs/23_FAILURE_CATALOG_84.md`.
2. Appliquer les decisions `PASS`, `WARN`, `BLOCK`, `QUARANTINED` et `INSUFFICIENT_DATA`.
3. Valider schemas avec `Pydantic` et batches avec `Great Expectations`.
4. Bloquer les donnees futures, conflits critiques, payloads sans hash et mocks production.
5. Garder `missing` comme `missing`, jamais zero.
6. Ajouter des `quality_flags` explicites pour toute couverture partielle.
7. Produire des controles tracables avec timestamps UTC.

## Sortie attendue
- Resume
- Fichiers modifies
- Tests executes
- Risques restants
- IDs E001-E084 concernes
