# Responsible Betting Guard

`Responsible Betting Guard` encadre tous les contenus de pari de `URIM`, `Bet Center`, `Kairos Stake Guard` et `URIM Dashboard`.

Il ne place jamais de mise et ne connecte jamais de compte bookmaker dans le MVP.

## Regles absolues

- Ne jamais promettre un gain.
- Ne jamais promettre un taux de reussite garanti.
- Ne jamais presenter une probabilite comme une certitude.
- Ne jamais utiliser la martingale.
- Ne jamais conseiller de recuperer les pertes.
- Ne jamais afficher une mise fixe comme ordre d'execution.
- Ne jamais masquer les periodes negatives.
- Ne jamais cibler les mineurs.
- Ne jamais apprendre directement depuis un gain utilisateur non verifie.

## Decisions possibles

| Decision | Sens |
|---|---|
| `ALLOW_ANALYSIS` | Analyse sportive affichable. |
| `SHOW_WARNING` | Analyse affichable avec avertissement renforcé. |
| `DISABLE_BETTING_CONTENT` | Contenus de pari masques pour l'utilisateur. |
| `NO_BET` | Aucune recommandation. |
| `INSUFFICIENT_DATA` | Donnees insuffisantes. |
| `SUSPENDED` | Blocage temporaire pour risque ou politique produit. |

## Limites Bet Center

- Maximum 5 matchs par ticket recommande.
- `stake_interval_cdf` reste un intervalle prudent.
- Les selections utilisateur restent `USER_UNVALIDATED`.
- Le ROI utilisateur ne doit pas etre presente comme performance Kairos.
- Le budget hebdomadaire reste un budget interne declare, pas un solde bookmaker.

## Desactivation des contenus de pari

L'utilisateur doit pouvoir desactiver les contenus de pari.

Quand cette option est active :
- conserver l'analyse probabiliste ;
- masquer les fourchettes de mise ;
- masquer les CTA de ticket ;
- conserver `NO_BET` et les avertissements de risque.

## Sortie JSON attendue

```json
{
  "guard": "Responsible Betting Guard",
  "decision": "SHOW_WARNING",
  "betting_content_enabled": true,
  "stake_content_allowed": true,
  "forbidden_language_detected": false,
  "risk_alerts": ["PROBABILITY_IS_NOT_CERTAINTY"],
  "required_copy": [
    "Une fourchette en CDF n'est pas un ordre de pari.",
    "URIM ne garantit aucun gain."
  ]
}
```

## Erreurs couvertes

E026, E041-E062, E075, E076, E077, E078, E079, E080, E081, E082, E083, E084.
