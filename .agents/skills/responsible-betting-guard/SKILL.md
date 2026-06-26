---
name: responsible-betting-guard
description: Specifier, auditer ou implementer le Responsible Betting Guard URIM, incluant interdiction de garantie, martingale, recuperation des pertes, bookmaker MVP, mise reelle, langage trompeur et contenus betting desactivables.
---

# responsible-betting-guard

1. Lire `docs/42_RESPONSIBLE_BETTING_GUARD.md`, `docs/22_RESPONSIBLE_USE.md`, `docs/35_KAIROS_STAKE_GUARD.md` et `docs/36_BET_CENTER_SPEC.md`.
2. Bloquer promesse de gain, taux garanti, martingale, recuperation des pertes et ordre fixe.
3. Retourner `NO_BET`, `INSUFFICIENT_DATA` ou `SUSPENDED` quand le risque ou la politique produit l'exige.
4. Conserver les contenus betting desactivables sans masquer l'analyse sportive.
5. Ne jamais connecter un compte bookmaker dans le MVP.
6. Ne jamais executer de mise reelle.
7. Ne jamais presenter `Kairos eveille` comme une certitude.

## Sortie attendue
- Resume
- Fichiers modifies
- Tests executes
- Risques restants
- IDs E001-E084 concernes
