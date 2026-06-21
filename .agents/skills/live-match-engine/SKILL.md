---
name: live-match-engine
description: Travailler sur événements live, WebSocket, recalcul in-play, latence et corrections.
---

# live-match-engine


1. Séparer strictement live et pré-match.
2. Ordonner, dédupliquer et corriger les événements.
3. Mesurer la latence bout en bout.
4. Suspendre si stale ou incohérent.
5. Versionner chaque recalcul.
6. Ne jamais écraser une prédiction antérieure.
7. Tester carton rouge, VAR, report, abandon et correction.


## Sortie attendue
- Résumé
- Fichiers modifiés
- Tests exécutés
- Risques restants
- IDs E001–E084 concernés
