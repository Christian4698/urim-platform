# Programme A — Plateforme utilisable

## Objectif

Livrer une première plateforme URIM publique, professionnelle et responsive,
reliée aux contrats de disponibilité FastAPI/PostgreSQL, sans activer de
fournisseur sportif, bookmaker, live, pari réel, prédiction ou authentification.

## Périmètre exécuté

- CORS par origines exactes, sans wildcard ni credentials.
- Client navigateur limité à `GET /health` et `GET /readiness`.
- Pages Accueil, Dashboard, Disponibilité, Modules et Paramètres.
- Layout, navigation desktop/tablette/mobile, états loading/empty/error/offline,
  animations réduites et accessibilité clavier.
- SEO technique, manifeste, robots, sitemap, métadonnées et en-têtes de sécurité.
- Migration Next.js 16 / React 19 et correction des dépendances npm vulnérables.
- Blueprint Render monorepo, variables publiques et préparation DNS `urim.pro`.
- Documentation d’exploitation et de sécurité Programme A.

## Validation réalisée les 22 et 23 juillet 2026

- ESLint : réussi, zéro avertissement.
- TypeScript : réussi.
- Tests frontend : 22 réussis.
- Contrats JSON : 6 schémas validés.
- Tests FastAPI : 1 203 réussis, 2 ignorés, 1 avertissement tiers Starlette.
- Ruff : réussi.
- `pip check` : réussi.
- `pnpm audit --prod` : aucune vulnérabilité connue.
- Build Next.js 16.2.11 : réussi, 15 pages statiques, compilation 5,9 s.
- QA navigateur : desktop et mobile, navigation, requêtes réelles, mode offline,
  zéro erreur ou avertissement console.
- Performance locale Dashboard : FCP 472 ms, chargement 427 ms, 21 662 octets
  transférés après démarrage.
- Scan Git : aucun fichier `.env`, aucune clé privée/API détectée.

## État de déploiement

Le Blueprint `render.yaml` est validé et synchronisé dans le workspace Render
`urim-platform`. Le service `urim-web` est `live` en région `frankfurt` sur le
commit `3e013930ec5645e9ebd0ea3a9c1789f7954f7fdd`.

- `https://urim-web.onrender.com` répond en HTTPS.
- `https://urim.pro` répond `200` avec un certificat valide.
- `https://www.urim.pro` possède un certificat valide et redirige vers l’apex.
- Cloudflare DNS et Google DNS résolvent l’apex vers `216.24.57.1`, sans AAAA,
  et `www` vers `urim-web.onrender.com`.
- Render marque `urim.pro` et `www.urim.pro` comme `verified`.
- Le Dashboard public confirme Frontend → FastAPI → Supabase `Opérationnel`.
- `/health` retourne `status=ok`.
- `/readiness` retourne `ready=true` et `database=ok`.
- API Football, live, bookmakers, prédiction, authentification et paris réels
  restent désactivés.

## Critère de clôture

Les cinq critères de clôture sont satisfaits : service Render `live`, CORS
validé, DNS propagé, TLS actif sur les deux domaines et smoke test public
navigateur → FastAPI → Supabase réussi sur desktop, mobile et mode offline.

## Plan State

Programme A terminé à 100 %. Le plan actif est clôturé et déplacé dans
`completed/`.

## Risques suivis

- E005 : aucune donnée future ni prédiction n’est consommée.
- E026 : `INSUFFICIENT_DATA` reste la posture explicite.
- E049/E066 : états incomplets et timeouts rendus sans valeur inventée.
- E071 : disponibilité absente distincte de `false`.
- E074 : secrets strictement backend.
- E075-E077/E083-E084 : aucune promesse, pression ou exécution de pari.
