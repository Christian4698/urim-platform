# URIM — Sports Intelligence Platform

URIM est l'application produit et KAIROS son futur moteur technique. Le dépôt
construit une plateforme sportive probabiliste, traçable, sécurisée et
explicable. Aucun résultat, score ou bénéfice n'est jamais garanti.

## État du produit

- Programme A : plateforme publique Next.js + FastAPI, terminé et figé par le
  tag `v1.0.0-programme-a`.
- Programme B1 : fondation API-Football backend-only, stockage PostgreSQL
  append-only, API read-only et écran `/donnees-sportives`.
- Prédictions, probabilités officielles, KAIROS, bookmakers, live automatique,
  authentification et paris réels : désactivés.

Le fournisseur sportif est opt-in. Sans `API_FOOTBALL_KEY` backend et
`API_FOOTBALL_ENABLED=true`, aucun appel externe n'est possible. La clé ne doit
jamais être exposée au frontend, aux logs ou à Git.

## Architecture

```text
API-Football
    ↓ client backend borné
Normalisation + provenance
    ↓
PostgreSQL / Supabase
    ↓
FastAPI read-only
    ↓
Next.js
```

Voir [Programme B1](docs/72_PROGRAM_B1_REAL_SPORTS_DATA.md) pour le schéma, les
commandes de synchronisation, les variables et le runbook Render.

## Démarrage local

Prérequis : Node.js 22.22, pnpm 9 et Python 3.12+.

```powershell
corepack enable
pnpm install --frozen-lockfile
pnpm web:dev
```

Dans un second terminal :

```powershell
cd apps/api
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload
```

Copier uniquement `.env.example` vers un fichier local non suivi. Ne jamais
placer `DATABASE_URL` ni `API_FOOTBALL_KEY` dans `apps/web` ou une variable
`NEXT_PUBLIC_*`.

## Vérification

```powershell
pnpm contracts:validate
pnpm api:lint
pnpm api:test
pnpm web:lint
pnpm web:typecheck
pnpm web:test
pnpm web:build
pnpm audit --prod
git diff --check
```

Principe central : aucune fixture, donnée simulée ou valeur par défaut ne doit
être présentée comme une observation sportive réelle.
