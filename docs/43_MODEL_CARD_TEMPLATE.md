# Model Card Template

Chaque modele `Kairos` publiable doit posseder une model card.

La model card decrit ce que le modele sait faire, ce qu'il ne sait pas faire, les donnees utilisees, les metriques, les limites et les risques.

## Identite

- `model_version`
- nom du module : `Half Goals Intelligence Engine`, `Corners Intelligence Engine`, `Fouls & Cards Intelligence Engine`, etc.
- marche principal ou secondaire
- proprietaire technique
- date de creation
- date de validation
- statut : `DRAFT`, `CANDIDATE`, `STAGING`, `PRODUCTION`, `RETIRED`

## Usage prevu

Documenter :
- marche cible ;
- horizon : pre-match, live futur, post-match ;
- competitions couvertes ;
- conditions d'utilisation ;
- conditions `NO_BET` ;
- exclusions connues.

## Donnees et features

Inclure :
- data cards liees ;
- fenetre historique ;
- sources ;
- features principales ;
- features exclues ;
- controles temporels ;
- quality gates requis.

## Evaluation

Inclure au minimum :
- Brier score ;
- log loss ;
- calibration error ;
- couverture ;
- taux de `NO_BET` ;
- performance par competition ;
- performance par marche ;
- stabilite hors echantillon ;
- ROI simule net si odds disponibles, sans promesse de rentabilite.

## Calibration

Documenter :
- methode de calibration ;
- buckets ;
- volume par bucket ;
- courbe de fiabilite ;
- segments faibles ;
- seuils de confiance.

## Limites

La model card doit expliquer :
- donnees manquantes ;
- petits echantillons ;
- competitions peu couvertes ;
- changement de regime ;
- drift ;
- correlation de marches ;
- limites des cotes ;
- absence de garantie.

## Sortie JSON attendue

```json
{
  "model_card_id": "mc_kairos_half_goals_v1",
  "model_version": "kairos-half-goals-0.1.0",
  "market": "HALF_GOAL_DOMINANCE",
  "status": "CANDIDATE",
  "intended_use": "Pre-match probability estimation",
  "metrics": {
    "brier_score": null,
    "log_loss": null,
    "calibration_error": null,
    "coverage": null,
    "no_bet_rate": null
  },
  "data_cards": ["dc_api_football_mvp_2026"],
  "limitations": ["No guaranteed outcome", "Coverage varies by competition"],
  "e_codes": ["E005", "E026", "E042", "E067", "E084"]
}
```

## Erreurs couvertes

E013-E026, E029-E031, E037-E062, E063, E064, E067-E069, E075-E084.
