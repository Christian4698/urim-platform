# Locale, devise et i18n

`URIM` utilise le franc congolais comme devise principale et le francais comme langue principale.

## Parametres par defaut

```json
{
  "app_name": "URIM",
  "engine_name": "Kairos",
  "default_locale": "fr-CD",
  "primary_language": "fr",
  "secondary_language": "en",
  "currency": "CDF"
}
```

## Langues

- Langue principale : francais.
- Langue secondaire : anglais optionnel.
- Toute interface critique doit etre disponible en francais avant l'anglais.
- Les textes responsables ne doivent pas etre adoucis dans la traduction anglaise.

## Devise CDF

Tous les montants du `Bet Center` et de `Kairos Stake Guard` sont affiches en `CDF`.

Regles :
- afficher des intervalles prudents, jamais des ordres fixes ;
- afficher `0 CDF` pour `NO_BET`, `WATCH`, `SUSPENDED`, `KAIROS_LOCKED` ou `INSUFFICIENT_DATA` ;
- stocker les montants comme entiers de plus petite unite applicable ;
- conserver la devise sur chaque champ financier ;
- ne jamais convertir silencieusement une devise.

## Temps et fuseaux

- Stocker tous les horodatages en UTC.
- Afficher selon la locale utilisateur.
- Conserver `available_at`, `fetched_at`, `observed_at` et `prediction_time` sans conversion destructive.
- Ne jamais utiliser l'heure locale affichee pour calculer la disponibilite temporelle.

## Copies responsables

Texte francais autorise :
- "Probabilite estimee"
- "Confiance de l'analyse"
- "Risque eleve"
- "Aucune recommandation : donnees insuffisantes"
- "Fourchette prudente indicative"

Texte anglais autorise :
- "Estimated probability"
- "Analysis confidence"
- "High risk"
- "No recommendation: insufficient data"
- "Indicative prudent range"

Texte interdit dans toutes les langues :
- "gain garanti"
- "sure bet"
- "match sur"
- "risk-free"
- "recuperer les pertes"
- "guaranteed profit"

## Sortie JSON attendue

```json
{
  "locale": "fr-CD",
  "currency": "CDF",
  "labels": {
    "probability": "Probabilite",
    "confidence": "Confiance",
    "risk": "Risque",
    "stake_interval": "Fourchette prudente"
  },
  "amounts": {
    "stake_interval_cdf": {
      "min": 250,
      "max": 750,
      "currency": "CDF",
      "display": "250-750 CDF"
    }
  }
}
```

## Erreurs couvertes

E066, E075, E076, E077, E083, E084.
