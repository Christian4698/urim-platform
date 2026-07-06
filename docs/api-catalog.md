# Catalogue interne d'APIs publiques (annexe, hors séquence de phases)

> Annexe de recherche — ne fait pas partie de la séquence numérotée `docs/00_...` à `docs/43_...` et ne déclenche aucune phase Codex. Source de référence : dépôt cloné localement dans `_references/public-apis/` (non versionné, voir `.gitignore`). Aucune de ces APIs n'est câblée dans le code applicatif : ce document sert de matière première pour une validation humaine avant toute intégration réelle.
>
> Portée : ce dépôt (`sports-intelligence-codex-blueprint`) ne contient que **URIM**. Les entrées « GTC Academy » et « Kazon/Razon » sont conservées ici pour référence future car ces produits vivent dans d'autres dépôts ; elles ne doivent donner lieu à aucun code dans ce dépôt-ci.
>
> Repère README source : `_references/public-apis/README.md` (branches lues : Sports & Fitness, Weather, Currency Exchange, Cryptocurrency, News, Finance, Authentication & Authorization, Cloud Storage & File Sharing, Documents & Productivity, Email, Text Analysis).

## Comment lire ce catalogue
- **Auth requise** : No / `apiKey` / `OAuth`.
- **Niveau de risque** : faible (lecture seule, données publiques, quota généreux) / moyen (quota limité, dépendance commerciale) / élevé (mouvement d'argent réel, trading, ou service instable/non documenté).
- **Adapté MVP / Adapté prod** : jugement basé sur HTTPS obligatoire, stabilité de la documentation et absence de risque de conformité — pas une validation finale.
- Toute API sans HTTPS est **rejetée pour la production** (règle absolue, voir skill `api-research-integrator`).

---

## URIM — intelligence sportive, probabilités, odds, No Bet

### API-FOOTBALL
- Catégorie : Sports & Fitness
- Usage URIM : déjà intégré comme provider réel (voir `apps/api/app/modules/providers/api_football_adapter.py`, `docs/35_API_FOOTBALL_READ_ONLY_ADAPTER.md`). Entrée listée ici pour mémoire, ne pas ré-intégrer.
- Auth requise : `apiKey` — HTTPS : Yes — CORS : Yes
- Niveau de risque : faible (déjà sous contrat `docs/05_PROVIDER_CONNECTOR_CONTRACT.md`)
- MVP : oui (déjà en place) — Prod : oui, sous garde-fous existants (secret preflight, sandbox, activation gate)
- Commentaire technique : ne pas dupliquer ce connecteur ; toute évolution passe par le pattern déjà établi dans `apps/api/app/modules/providers/`.
- Variables .env : déjà couvertes par `.env.example` existant.

### TheSportsDB
- Catégorie : Sports & Fitness
- Usage URIM : source secondaire/backup pour métadonnées équipes, compétitions, artwork ; utile pour enrichir l'affichage, pas pour les probabilités.
- Auth requise : `apiKey` (clé de test publique disponible) — HTTPS : Yes — CORS : Yes
- Niveau de risque : faible
- MVP : oui, en mock d'abord — Prod : oui pour données non critiques uniquement
- Commentaire technique : ne jamais l'utiliser comme source de vérité pour les cotes ou résultats engageant une décision `NO_BET`/pari.
- Variables .env : `THESPORTSDB_API_KEY`

### Football-Data.org
- Catégorie : Sports & Fitness
- Usage URIM : matches, compétitions, classements — complément de couverture ligues européennes.
- Auth requise : `X-Mashape-Key` (équivalent apiKey) — HTTPS : Yes — CORS : Unknown
- Niveau de risque : moyen (quota gratuit restreint)
- MVP : oui — Prod : à valider selon quota
- Commentaire technique : vérifier les limites de rate-limit avant d'en dépendre pour le live.
- Variables .env : `FOOTBALL_DATA_API_KEY`

### Sportmonks Football
- Catégorie : Sports & Fitness
- Usage URIM : statistiques avancées, historique, standings multi-ligues — candidat pour diversifier les providers (redondance en cas de panne API-Football).
- Auth requise : `apiKey` — HTTPS : Yes — CORS : Unknown
- Niveau de risque : moyen (offre payante au-delà du plan gratuit)
- MVP : à l'étude — Prod : oui si contrat de licence validé
- Commentaire technique : suivre `docs/28_PROVIDER_ONBOARDING_CHECKLIST.md` avant toute activation.
- Variables .env : `SPORTMONKS_API_KEY`

### TheRundown
- Catégorie : Sports & Fitness (odds)
- Usage URIM : cotes temps réel multi-bookmakers, utile pour `docs/15_ODDS_AND_VALUE.md` (calcul de value bet).
- Auth requise : `apiKey` — HTTPS : Yes — CORS : Yes
- Niveau de risque : moyen (dépendance à un fournisseur de cotes tiers)
- MVP : mock d'abord — Prod : oui après validation de couverture et fraîcheur (`observed_at`/`available_at`)
- Commentaire technique : les cotes doivent porter un `odds_snapshot_id` conforme au contrat de prédiction — jamais consommées brutes.
- Variables .env : `THERUNDOWN_API_KEY`

### Oddsmagnet
- Catégorie : Sports & Fitness (odds)
- Usage URIM : historique de cotes bookmakers UK — utile pour backtesting (`docs/11_BACKTESTING_PROTOCOL.md`).
- Auth requise : No — HTTPS : Yes — CORS : Yes
- Niveau de risque : faible
- MVP : oui — Prod : oui pour usage historique/backtest uniquement
- Commentaire technique : pas de clé à gérer, mais vérifier la fraîcheur et la couverture géographique avant usage live.
- Variables .env : aucune

### Open-Meteo
- Catégorie : Weather
- Usage URIM : conditions météo comme feature contextuelle (terrain, météo match) pour le feature store.
- Auth requise : No — HTTPS : Yes — CORS : Yes
- Niveau de risque : faible
- MVP : oui — Prod : oui (usage non commercial gratuit, vérifier limite si trafic élevé)
- Commentaire technique : gratuit et sans clé — bon candidat par défaut avant d'envisager un fournisseur payant.
- Variables .env : aucune

### OpenWeatherMap
- Catégorie : Weather
- Usage URIM : alternative payante à Open-Meteo si SLA/quota nécessaires.
- Auth requise : `apiKey` — HTTPS : Yes — CORS : Unknown
- Niveau de risque : faible
- MVP : non prioritaire (Open-Meteo suffit) — Prod : oui si besoin de SLA
- Commentaire technique : garder en secours, ne pas dupliquer l'intégration tant qu'Open-Meteo répond au besoin.
- Variables .env : `OPENWEATHERMAP_API_KEY`

### Frankfurter / Exchangerate.host
- Catégorie : Currency Exchange
- Usage URIM : conversion CDF/USD pour affichage bankroll/dashboard multi-devises.
- Auth requise : No — HTTPS : Yes — CORS : Yes
- Niveau de risque : faible
- MVP : oui — Prod : oui (gratuit, pas de clé, historique disponible)
- Commentaire technique : privilégier ces deux-là avant tout fournisseur payant pour un simple taux de change d'affichage.
- Variables .env : aucune

### GNews / NewsAPI
- Catégorie : News
- Usage URIM : actualités/événements sportifs contextuels pour dashboard (pas pour la modélisation probabiliste).
- Auth requise : `apiKey` — HTTPS : Yes — CORS : Yes (GNews) / Unknown (NewsAPI)
- Niveau de risque : moyen (quota gratuit faible)
- MVP : optionnel — Prod : à valider selon usage réel
- Commentaire technique : ne jamais mélanger ce flux avec les métriques pré-match/live/post-match du moteur de prédiction (interdiction AGENTS.md).
- Variables .env : `GNEWS_API_KEY` ou `NEWSAPI_API_KEY`

---

## GTC Academy — formation, certification, paiements manuels (hors dépôt)

### Sendgrid
- Catégorie : Email
- Usage GTC : envoi transactionnel (confirmation d'inscription, certificats, rappels).
- Auth requise : `apiKey` — HTTPS : Yes — CORS : Unknown
- Niveau de risque : faible (service mature, largement utilisé)
- MVP : oui (mock d'abord) — Prod : oui
- Commentaire technique : clé strictement backend, jamais exposée côté client.
- Variables .env : `SENDGRID_API_KEY`

### iLovePDF
- Catégorie : Documents & Productivity
- Usage GTC : fusion/scission/extraction de texte pour livrets de formation et certificats PDF.
- Auth requise : `apiKey` — HTTPS : Yes — CORS : Yes
- Niveau de risque : faible
- MVP : oui — Prod : oui (250 documents/mois gratuits, vérifier volume réel)
- Commentaire technique : bon candidat pour génération de certificats à partir de templates.
- Variables .env : `ILOVEPDF_API_KEY`

### CraftMyPDF
- Catégorie : Documents & Productivity
- Usage GTC : génération de certificats/attestations à partir de templates drag-and-drop.
- Auth requise : `apiKey` — HTTPS : Yes — CORS : No
- Niveau de risque : faible
- MVP : oui — Prod : oui
- Commentaire technique : alternative à iLovePDF si un moteur de templates plus riche est nécessaire.
- Variables .env : `CRAFTMYPDF_API_KEY`

### QR code (goqr.me)
- Catégorie : Documents & Productivity (QR)
- Usage GTC : génération de QR codes de vérification de certificat.
- Auth requise : No — HTTPS : Yes — CORS : Unknown
- Niveau de risque : faible
- MVP : oui — Prod : oui pour usage non critique ; prévoir un fallback si CORS Unknown pose problème côté navigateur
- Commentaire technique : pas de clé à gérer ; service simple, faible dépendance.
- Variables .env : aucune

### Auth0
- Catégorie : Authentication & Authorization
- Usage GTC : authentification utilisateurs/élèves, gestion de rôles (élève/formateur/admin).
- Auth requise : `apiKey` — HTTPS : Yes — CORS : Yes
- Niveau de risque : moyen (dépendance critique, coût au volume d'utilisateurs)
- MVP : à valider (peut être sur-dimensionné pour un MVP) — Prod : oui si volume le justifie
- Commentaire technique : évaluer d'abord une solution interne plus simple pour le MVP avant de committer sur ce fournisseur.
- Variables .env : `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET`

### Google Drive / Dropbox
- Catégorie : Cloud Storage & File Sharing
- Usage GTC : stockage des livres/supports de cours.
- Auth requise : `OAuth` — HTTPS : Yes — CORS : Unknown
- Niveau de risque : moyen (flux OAuth à sécuriser, gestion des tokens)
- MVP : optionnel (un stockage objet classique peut suffire) — Prod : oui si intégration OAuth validée
- Commentaire technique : ne jamais stocker de refresh token côté client.
- Variables .env : `GOOGLE_DRIVE_CLIENT_ID`, `GOOGLE_DRIVE_CLIENT_SECRET` (ou équivalent Dropbox)

---

## Kazon/Razon — trading/market intelligence, DEMO par défaut, LIVE OFF (hors dépôt)

### CoinGecko
- Catégorie : Cryptocurrency
- Usage Kazon : prix, marché, données développeur/social — bon défaut pour un mode DEMO/MOCK.
- Auth requise : No — HTTPS : Yes — CORS : Yes
- Niveau de risque : faible (lecture seule, pas de mouvement d'argent)
- MVP : oui — Prod : oui pour affichage de marché ; jamais pour exécution d'ordre
- Commentaire technique : idéal comme source de données pour le mode DEMO par défaut.
- Variables .env : aucune (clé optionnelle pour tiers payant)

### CoinCap
- Catégorie : Cryptocurrency
- Usage Kazon : alternative/secours à CoinGecko pour prix temps réel.
- Auth requise : No — HTTPS : Yes — CORS : Unknown
- Niveau de risque : faible
- MVP : oui — Prod : oui
- Commentaire technique : redondance utile en cas d'indisponibilité de CoinGecko.
- Variables .env : aucune

### FRED (Federal Reserve Economic Data)
- Catégorie : Finance (données économiques)
- Usage Kazon : indicateurs macroéconomiques US pour contexte de marché.
- Auth requise : `apiKey` — HTTPS : Yes — CORS : Yes
- Niveau de risque : faible (source institutionnelle, lecture seule)
- MVP : optionnel — Prod : oui
- Commentaire technique : bonne source pour enrichir un tableau de bord macro sans risque de conformité.
- Variables .env : `FRED_API_KEY`

### Econdb
- Catégorie : Finance (données économiques)
- Usage Kazon : données macroéconomiques mondiales complémentaires à FRED.
- Auth requise : No — HTTPS : Yes — CORS : Yes
- Niveau de risque : faible
- MVP : optionnel — Prod : oui
- Commentaire technique : pas de clé à gérer.
- Variables .env : aucune

### Binance / Kraken (market data uniquement)
- Catégorie : Cryptocurrency (exchange)
- Usage Kazon : données de marché temps réel si un flux plus riche que CoinGecko est requis. **Ne jamais utiliser les endpoints de trading/ordre sans validation explicite — Kazon reste LIVE OFF par défaut.**
- Auth requise : `apiKey` — HTTPS : Yes — CORS : Unknown
- Niveau de risque : élevé si utilisé au-delà de la lecture seule (mouvement d'argent réel possible)
- MVP : lecture seule uniquement, en mock — Prod : lecture seule seulement, jamais d'exécution d'ordre sans validation humaine explicite
- Commentaire technique : isoler strictement les endpoints de lecture (prix/carnet) des endpoints d'ordre ; toute activation d'ordre réel exige une validation explicite hors de ce catalogue.
- Variables .env : `BINANCE_API_KEY` / `KRAKEN_API_KEY` (lecture seule)

### MarketAux
- Catégorie : News (finance)
- Usage Kazon : actualités marché avec tickers taggés et sentiment.
- Auth requise : `apiKey` — HTTPS : Yes — CORS : Yes
- Niveau de risque : moyen (quota gratuit limité)
- MVP : optionnel — Prod : à valider selon volume
- Commentaire technique : utile pour contexte de marché, pas pour décision automatique.
- Variables .env : `MARKETAUX_API_KEY`

---

## APIs à éviter
- **Toute API listée avec HTTPS = No** (ex. `AccuWeather`, `Fixer`, `MLB Records and Stats`) — rejetée d'office pour la production, quel que soit le projet.
- **Endpoints de trading/ordre réel** (Binance, Kraken, Coinbase Pro, Bitmex, etc. au-delà de la lecture seule) — interdits sans validation explicite, en contradiction directe avec le mode LIVE OFF de Kazon/Razon.
- **APIs à CORS/documentation « Unknown » et sans historique d'usage connu** — à re-vérifier manuellement avant tout usage prod, ne pas se fier au tableau seul.
- **EmailJS et équivalents « clé côté client »** — pattern incompatible avec l'interdiction d'exposer une clé API au frontend (AGENTS.md) ; à proscrire pour GTC sauf si la clé est strictement restreinte et à faible risque.

## Prochaines étapes avant intégration réelle
1. Validation humaine du présent catalogue (aucune intégration réelle avant ce feu vert).
2. Pour chaque API retenue : créer un adapter derrière l'interface canonique existante (backend `apps/api/app/modules/providers/` pour URIM), avec mock/demo d'abord.
3. Documenter chaque variable dans `.env.example` (jamais de clé committée).
4. Pour URIM : suivre `docs/28_PROVIDER_ONBOARDING_CHECKLIST.md` et `docs/29_PROVIDER_READINESS_CONTRACTS.md` avant toute activation.
5. Pour GTC/Kazon (autres dépôts) : reproduire le même principe mock-first / clé backend uniquement / LIVE OFF par défaut.
