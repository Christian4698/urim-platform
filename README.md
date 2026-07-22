# URIM — Sports Intelligence Platform

URIM est l’application produit et Kairos son moteur technique. Ce dépôt construit
une plateforme sportive probabiliste, traçable, sécurisée et explicable. La
version Programme A est une plateforme publique de consultation : elle ne crée
aucune prédiction, ne connecte aucun bookmaker et n’exécute aucun pari.

## Périmètre Programme A

- `apps/web` : interface Next.js responsive (Accueil, Dashboard,
  Disponibilité, Modules et Paramètres) ;
- `apps/api` : API FastAPI publique en lecture seule pour `/health` et
  `/readiness` ;
- PostgreSQL/Supabase : interrogé exclusivement par le backend ;
- `render.yaml` : Blueprint du frontend Render et du domaine `urim.pro` ;
- `packages/contracts`, `packages/config` et `packages/ui` : contrats et
  composants partagés.

API Football, les bookmakers, le live, les paris réels, le moteur de prédiction
et l’authentification restent explicitement désactivés.

## Démarrage local

Prérequis : Node.js 22.22, `pnpm` et Python 3.12+.

```bash
corepack enable
pnpm install --frozen-lockfile
pnpm web:dev
```

Dans un second terminal :

```bash
cd apps/api
python -m uvicorn app.main:app --reload
```

Copier uniquement les fichiers `.env.example` vers des fichiers `.env` locaux.
Ne jamais placer `DATABASE_URL` dans `apps/web` ni dans une variable
`NEXT_PUBLIC_*`.

## Vérification

```bash
pnpm contracts:validate
pnpm web:lint
pnpm web:typecheck
pnpm web:test
pnpm web:build
pnpm api:lint
pnpm api:test
pnpm audit --prod
```

La procédure de déploiement, les variables autorisées et la configuration DNS
sont détaillées dans `docs/71_PROGRAM_A_PLATFORM.md`.

## Principe central

> Aucune donnée de production ne doit être inventée, extrapolée comme si elle
> était observée, ou remplacée silencieusement par un mock.

Les données simulées sont réservées aux tests, fixtures locales et
environnements explicitement marqués `DEMO` ou `PLACEHOLDER`.
