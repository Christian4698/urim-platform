# Provenance des données

Toute valeur importante conserve :
- fournisseur et identifiant externe ;
- endpoint/flux ;
- heure de l’événement ;
- heure observée ;
- heure de disponibilité ;
- heure de récupération ;
- version du schéma ;
- hash du payload brut ;
- transformations ;
- indicateurs de qualité ;
- licence et règles de redistribution.

## Provenance par champ
Score, statut, composition, blessure, carton rouge et cote ont une provenance par champ.

## Divergence
1. Conserver toutes les observations.
2. Appliquer une priorité documentée.
3. Créer un conflit explicite.
4. Bloquer si critique.
5. Expliquer la résolution.

Une correction manuelle est append-only : ancienne valeur, auteur, raison et heure restent conservés.
