# URIM Web

Interface Next.js App Router de la plateforme publique URIM.

## Configuration publique

Copier `.env.example` vers un fichier local non versionné et définir uniquement :

```text
NEXT_PUBLIC_API_URL=https://urim-api-jrbk.onrender.com
NEXT_PUBLIC_SITE_URL=https://urim.pro
```

Ces valeurs sont des origines publiques, pas des secrets. `DATABASE_URL`, les credentials fournisseurs, les clés API et toute donnée bookmaker restent interdits dans le frontend.

Le navigateur appelle exclusivement `GET /health` et `GET /readiness`. Chaque réponse est bornée à cinq secondes et validée à l’exécution. Les fournisseurs, bookmakers, live, pari réel, ML et création de prédictions restent désactivés.

## Pages

- `/` : accueil;
- `/dashboard` : posture opérationnelle;
- `/disponibilite` : état direct FastAPI et PostgreSQL;
- `/modules` : registre des capacités;
- `/parametres` : configuration publique.

## Validation

```text
pnpm web:lint
pnpm web:typecheck
pnpm web:test
pnpm web:build
```

Le Blueprint Render vit à la racine dans `render.yaml` afin de conserver l’accès aux packages du monorepo pendant le build.
