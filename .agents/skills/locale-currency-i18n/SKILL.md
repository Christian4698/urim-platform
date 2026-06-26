---
name: locale-currency-i18n
description: Specifier, auditer ou implementer la locale et devise URIM, incluant francais principal, anglais optionnel, default_locale fr-CD, devise CDF, formats d'affichage, UTC en base et copies responsables.
---

# locale-currency-i18n

1. Lire `docs/41_LOCALE_CURRENCY_I18N.md`, `docs/22_RESPONSIBLE_USE.md`, `docs/35_KAIROS_STAKE_GUARD.md` et `docs/36_BET_CENTER_SPEC.md`.
2. Utiliser `fr-CD` comme locale par defaut et `CDF` comme devise principale.
3. Stocker les horodatages en UTC et afficher selon la locale utilisateur.
4. Afficher les montants comme intervalles prudents, jamais ordres fixes.
5. Conserver la devise sur chaque champ financier.
6. Ne jamais traduire une probabilite en certitude.
7. Garder les textes responsables equivalents en francais et anglais.

## Sortie attendue
- Resume
- Fichiers modifies
- Tests executes
- Risques restants
- IDs E001-E084 concernes
