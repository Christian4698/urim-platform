---
name: kairos-stake-guard
description: Spécifier, auditer ou implémenter Kairos Stake Guard, les états Kairos, les fourchettes prudentes en CDF, les limites de bankroll/exposition, et les protections contre martingale, surmise, récupération des pertes et garanties irréalistes.
---

# kairos-stake-guard

1. Lire `docs/35_KAIROS_STAKE_GUARD.md`, `docs/34_URIM_BRANDING_AND_KAIROS_ENGINE.md`, `docs/13_NO_BET_AND_RISK_ENGINE.md`, `docs/15_ODDS_AND_VALUE.md` et `docs/22_RESPONSIBLE_USE.md`.
2. Traiter `Kairos Stake Guard` comme autorité bloquante sur toute fourchette de mise.
3. Afficher les montants uniquement en intervalles `stake_interval_cdf`, jamais comme ordre fixe.
4. Utiliser `CDF` comme devise principale.
5. Calculer les intervalles depuis `bankroll_cdf` avec plafond par match `0.5 %` et plafond journalier `1.0 %`.
6. Autoriser `Kairos éveillé` seulement pour `KAIROS_AWAKENED`.
7. Exiger probabilité calibrée, cote fraîche, confiance, calibration, qualité des données, exposition restante et risque global.
8. Retourner `NO_BET`, `INSUFFICIENT_DATA` ou `SUSPENDED` si une entrée critique manque ou si un seuil de risque est dépassé.
9. Bloquer toute martingale, surmise, récupération des pertes ou promesse de bénéfice.
10. Ne jamais présenter une probabilité, une confiance ou une fourchette de mise comme une garantie.

## Sortie attendue
- Résumé
- Fichiers modifiés
- Tests exécutés
- Risques restants
- IDs E001–E084 concernés
