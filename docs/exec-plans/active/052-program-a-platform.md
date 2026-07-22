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

## Validation réalisée le 22 juillet 2026

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

Le code et `render.yaml` sont prêts. Le backend Render existant atteint Supabase
et retourne `database=ok`; les six capacités sensibles restent `disabled`.

L’activation du nouveau service `urim-web` et le basculement DNS demeurent des
actions de compte : aucun Render CLI, jeton Render ou session Dashboard
utilisable n’est disponible dans cet environnement. `urim.pro` pointe encore
vers Hostinger et doit être basculé seulement après création et vérification du
service Render.

## Critère de clôture

Déplacer ce plan dans `completed/` après :

1. création/application du Blueprint `urim-web` dans le compte Render ;
2. déploiement vert du commit Programme A ;
3. vérification CORS depuis le frontend Render ;
4. bascule DNS et émission TLS pour `urim.pro` ;
5. smoke test public navigateur → FastAPI → Supabase.

## Risques suivis

- E005 : aucune donnée future ni prédiction n’est consommée.
- E026 : `INSUFFICIENT_DATA` reste la posture explicite.
- E049/E066 : états incomplets et timeouts rendus sans valeur inventée.
- E071 : disponibilité absente distincte de `false`.
- E074 : secrets strictement backend.
- E075-E077/E083-E084 : aucune promesse, pression ou exécution de pari.
