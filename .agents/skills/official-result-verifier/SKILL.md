---
name: official-result-verifier
description: Specifier, auditer ou implementer la verification officielle post-match URIM, incluant resultats officiels multi-source, statut de verification, journal append-only, conflits et apprentissage interdit depuis declaration utilisateur non verifiee.
---

# official-result-verifier

1. Lire `docs/39_OFFICIAL_RESULT_VERIFIER.md`, `docs/37_POST_MATCH_LEARNING_ENGINE.md`, `docs/06_DATA_PROVENANCE.md`, `docs/07_TEMPORAL_INTEGRITY.md` et `docs/23_FAILURE_CATALOG_84.md`.
2. Separer `user_reported_result`, `official_result` et `learning_result`.
3. Utiliser seulement des resultats officiels verifies pour l'apprentissage.
4. Conserver chaque verification append-only avec hashes et reason codes.
5. Retourner `CONFLICT` ou `INSUFFICIENT_DATA` si les sources divergent ou si le score mi-temps manque.
6. Ne jamais modifier retroactivement une prediction `Kairos`.
7. Ne jamais apprendre directement depuis un gain utilisateur declare.

## Sortie attendue
- Resume
- Fichiers modifies
- Tests executes
- Risques restants
- IDs E001-E084 concernes
