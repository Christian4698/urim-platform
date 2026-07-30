# URIM — Sports Intelligence Platform

URIM est l'application produit et KAIROS son moteur technique. Le dépôt
construit une plateforme sportive probabiliste, traçable, sécurisée et
explicable. Aucun résultat, score ou bénéfice n'est jamais garanti.

## État du produit

- Programme A : plateforme publique Next.js + FastAPI, terminé et figé par le
  tag `v1.0.0-programme-a`.
- Programme B1 : fondation API-Football backend-only, stockage PostgreSQL
  append-only, API read-only et écran `/donnees-sportives`.
- Programme B2.1 : Kairos Core backend-only produit une baseline 1X2 pré-match
  read-only, explicable, non persistée et non calibrée depuis les données B1.
- Programme B2.2 : suggestions quotidiennes explicables, read-only, en bêta
  analytique, avec séparation entre Garde-fou Kairos et Suggestion analytique.
- Hotfix B2.3 : découverte quotidienne multi-compétitions et enrichissement
  minimal des fixtures réelles nécessaires à Kairos.
- Prédictions officielles publiées, bookmakers, live automatique,
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
commandes de synchronisation, les variables et le runbook Render. Voir
[Programme B2.1](docs/73_PROGRAM_B2_1_KAIROS_CORE.md) pour les features,
contrats temporels, endpoints et limites de Kairos Core.
Voir [Programme B2.2](docs/76_PROGRAM_B2_2_KAIROS_DAILY_SUGGESTIONS.md) pour le
score conservateur, les suggestions du jour et leurs barrières NO_BET.
Voir [Hotfix B2.3](docs/77_B2_3_DAILY_FIXTURE_DISCOVERY.md) pour la découverte
globale, le filtrage qualité, les quotas et les commandes opérateur.

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
pnpm api:build
pnpm web:lint
pnpm web:typecheck
pnpm web:test
pnpm web:build
pnpm audit --prod
git diff --check
```

Principe central : aucune fixture, donnée simulée ou valeur par défaut ne doit
être présentée comme une observation sportive réelle.
