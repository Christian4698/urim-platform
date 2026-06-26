---
name: bet-center
description: Spécifier, auditer ou implémenter le Bet Center de URIM, incluant budget hebdomadaire en CDF, solde virtuel interne, tickets Kairos et utilisateur, statuts gagné/perdu/annulé/remboursé, profit net, ROI, alertes de risque et séparation entre sélections validées par Kairos et sélections utilisateur non validées.
---

# bet-center

1. Lire `docs/36_BET_CENTER_SPEC.md`, `docs/35_KAIROS_STAKE_GUARD.md`, `docs/22_RESPONSIBLE_USE.md` et `docs/13_NO_BET_AND_RISK_ENGINE.md`.
2. Traiter `Bet Center` comme interface interne `URIM`, jamais connectée à un bookmaker réel dans le MVP.
3. Utiliser `weekly_budget_cdf`, `virtual_balance_cdf` et `bankroll_cdf` en `CDF`.
4. Limiter les tickets recommandés à 5 matchs maximum.
5. Afficher des intervalles `stake_interval_cdf`, jamais des mises fixes.
6. Autoriser les sélections utilisateur, mais les marquer `USER_UNVALIDATED`.
7. Séparer tickets `Kairos` et tickets utilisateur dans le suivi de performance, profit net et ROI.
8. Gérer les statuts `WON`, `LOST`, `VOID`, `REFUNDED` sans les confondre avec les résultats officiels.
9. Bloquer martingale, récupération des pertes, surmise et dépassement d'exposition.
10. Ne jamais présenter une recommandation ou une fourchette comme une garantie.

## Sortie attendue
- Résumé
- Fichiers modifiés
- Tests exécutés
- Risques restants
- IDs E001–E084 concernés
