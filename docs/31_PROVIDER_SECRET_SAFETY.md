# Provider Secret Safety

Phase 12 prepare la gestion future des secrets provider sans connecter de fournisseur reel.

## Statut
- Les providers restent desactives.
- API-Football reste deconnecte.
- Le gate d'onboarding reste `blocked_until_real_provider_audit`.
- Les reponses publiques n'exposent ni noms complets de variables provider, ni valeurs, ni credentials.

## Configuration future
Les futurs noms de variables provider peuvent apparaitre uniquement comme placeholders vides dans `.env.example`.

Les vraies valeurs devront etre stockees plus tard dans un environnement securise ou un secret manager. Elles ne doivent jamais etre commitees, loggees, retournees par API publique, envoyees au frontend ou utilisees pour activer un provider en Phase 12.

## Loader secret-safe
Le loader Phase 12 peut inspecter l'environnement local pour confirmer que le code reste secret-safe, mais son modele public retourne seulement :
- `configured=false`
- `missing=true`
- `providers_enabled=false`
- `activation_allowed=false`
- categories non sensibles
- compteurs
- exigence de stockage securise

## Phase 13 preflight
La Phase 13 conserve les garanties Phase 12 et ajoute une decision preflight publique separee. Cette decision reste bloquee et ne revele pas les noms complets de variables provider ni les valeurs locales.

La presence locale d'un secret peut etre inspectee par le loader pour garder la forme de validation future, mais cette presence est consommee puis ignoree. Elle ne change jamais `configured=false`, `missing=true` ou `real_provider_preparation_ready=false`.

## Hors portee
Aucun connecteur provider, aucun appel reseau, aucune cle reelle, aucun bookmaker, aucune mise reelle, aucun ML, aucune prediction reelle, aucune ingestion DB et aucune migration ne sont ajoutes.
