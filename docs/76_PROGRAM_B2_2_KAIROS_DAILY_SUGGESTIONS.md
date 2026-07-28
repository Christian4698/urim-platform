# Programme B2.2 — Kairos Daily Suggestions

## Portée

B2.2 transforme la sortie non persistée de Kairos Core en suggestions
analytiques quotidiennes. Il ne crée ni pari, ni conseil financier, ni cote,
ni mise, ni intégration bookmaker. Le calcul reste pré-match, déterministe,
read-only et utilise exclusivement les observations B1 déjà synchronisées
dans PostgreSQL.

Endpoints :

- `GET /api/v1/kairos/suggestions/today` ;
- `GET /api/v1/kairos/matches/{provider_match_id}/analysis` pour le détail ;
- `GET /api/v1/kairos/methodology` pour le contrat de calcul.

La journée est celle de `Africa/Kinshasa`. Un unique `as_of` UTC est fixé au
début de la requête quotidienne et doit être réutilisé par la page de détail.
Chaque requête SQL applique `available_at <= as_of`, `fetched_at <= as_of` et
`created_at <= as_of`. Les matchs historiques doivent aussi avoir commencé
avant `as_of` et avant le match cible.

## Contrat garde-fou et suggestion

La réponse détaillée sépare deux notions qui ne doivent jamais être
interprétées comme une décision de pari :

- `safety_decision` est le **Garde-fou Kairos**. Sa valeur reste `NO_BET` pour
  une analyse calculable et `INSUFFICIENT_DATA` lorsque le calcul est bloqué ;
- `analytical_suggestion` est la **Suggestion analytique** issue du score
  B2.2. Elle peut être une issue analytique ou `NO_BET`, sans cote, mise ni
  exécution ;
- `decision` reste un alias de compatibilité strictement égal à
  `safety_decision` ;
- `suggestion` reste un alias de compatibilité strictement égal à
  `analytical_suggestion`.

Les clients doivent afficher les libellés « Garde-fou Kairos » et
« Suggestion analytique ». Ils ne doivent jamais présenter
`analytical_suggestion` comme une décision ou un conseil de pari.

Chaque raison de suggestion porte :

- `category=analytical` pour un facteur calculé ;
- `category=guardrail` pour une limite ou un blocage ;
- `critical=true` pour un garde-fou qui ne peut pas être masqué par la limite
  d'affichage des trois principales raisons analytiques.

## Marchés analytiques

Les probabilités 1X2, double chance, Over/Under 2.5 et BTTS sont toutes
dérivées de la même matrice jointe de scores Poisson. Aucun marché ne fait
l'objet d'un modèle ou d'une donnée externe supplémentaire. La troncature de
la distribution est renormalisée et les compléments sont contrôlés.

Une seule suggestion est retenue parmi `Home Win`, `Away Win`, `Draw`,
`Double Chance`, `Over 2.5`, `Under 2.5`, `BTTS` et `NO_BET`.

## Score Kairos

Le score ne contient aucun coefficient de mélange ajouté pour B2.2 :

1. le signal d'un candidat est sa distance normalisée au cas sans information ;
2. les références sont `1/3` pour une issue 1X2, `2/3` pour une double chance
   et `1/2` pour un événement binaire ;
3. la fiabilité technique est `confidence_score / 65`, où `65` est le plafond
   documenté de Kairos Core ;
4. le score publié est le minimum entre signal normalisé, qualité des données
   et fiabilité technique normalisée.

Le minimum représente un contrat conservateur : le composant le moins fiable
borne la suggestion. Le seuil `40` réutilise la frontière documentée de
confiance faible/moyenne. En dessous, la réponse est `NO_BET`.

Les facteurs disponibles restent ceux de B2.1 : forme et résultats récents,
classement, contexte domicile/extérieur, attaque/défense par buts, tirs,
possession, corners, cartons et qualité/provenance. L'historique récent est
donc présent lorsqu'il existe. Aucun poids face-à-face séparé n'est introduit,
car la base actuelle ne fournit pas un échantillon H2H validé et comparable.

## Barrières NO_BET

`NO_BET` est obligatoire si :

- une équipe possède moins de trois résultats complets ;
- une probabilité ne peut pas être calculée sans imputation ;
- une observation viole la barrière temporelle, l'intégrité ou la provenance ;
- les données cibles sont périmées ;
- le score Kairos est inférieur à `40`.

Le niveau de confiance porte sur la fiabilité de l'analyse, jamais sur la
certitude du résultat. La baseline étant non calibrée et plafonnée à `65`, elle
ne publie pas un niveau de confiance `high`. Le risque reste `elevated` pour une
suggestion et `high` pour `NO_BET`.

## Sécurité et coûts

- transaction PostgreSQL `READ ONLY` et `statement_timeout=3000ms` ;
- rate limiting Redis fail-closed ;
- maximum `16` matchs évalués et `12` suggestions retournées ;
- maximum `2` requêtes quotidiennes concurrentes par instance ;
- validation stricte des query params et des identifiants ;
- aucune écriture métier, aucun appel fournisseur, aucun cache de suggestion,
  aucun secret et aucune donnée simulée ;
- hashes déterministes du snapshot de features et de la suggestion analytique.

Le frontend appelle uniquement l'API URIM publique. Il vérifie les flags de
sécurité et refuse les réponses qui activeraient écriture, provider direct,
bookmaker, betting ou live automatique.

Un `503` portant le code public `kairos_rate_limit_unavailable` est traduit en
message utilisateur indiquant que le contrôle de débit Redis est indisponible.
Les détails internes Redis ne sont jamais repris. L'interface distingue aussi
l'API indisponible, l'absence de match, les données insuffisantes et les
données périmées. Sur une carte, les garde-fous critiques sont affichés
séparément et sans troncature; seules les raisons analytiques sont limitées aux
trois principales.

Le Shell Render du service `urim-api` peut valider l'instance privée configurée
à l'exécution avec `python scripts/b2_2_redis_gate.py`. Le script n'accepte
aucune URL en argument et n'affiche ni URL, ni hôte, ni identifiant. Il contrôle
le ping, l'atomicité concurrente, le TTL, les limites 30/120, le hashage client,
le fail-closed et le nettoyage de ses seules clés éphémères.

## Migration et limites

Aucune migration n'est nécessaire : B2.2 lit les tables B1 existantes et ne
persiste pas ses résultats.

Limites connues :

- baseline Poisson non calibrée hors échantillon ;
- fournisseur unique, sans réconciliation multi-source ;
- aucun monitoring de drift de suggestions non persistées ;
- coût quotidien borné mais encore composé de plusieurs requêtes read-only par
  match ;
- pas de recommandation BTTS négative ni de marché au-delà de la liste B2.2 ;
- la disponibilité PostgreSQL réelle reste à vérifier via la suite
  conditionnelle lorsque `B1_TEST_DATABASE_URL` désigne une base isolée.

Les tests frontend de release couvrent `NO_BET`, les données périmées, les
données insuffisantes, le `503` Redis, l'absence de match, la propagation du
même `as_of` vers l'analyse détaillée et la séparation des deux libellés.
