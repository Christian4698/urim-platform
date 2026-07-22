# Programme A — Plateforme utilisable

## Objectif

Le Programme A livre la première surface publique utilisable d’URIM sans activer de donnée sportive, fournisseur, moteur de prédiction, live, bookmaker, pari réel ou authentification.

## Architecture livrée

```text
Navigateur Next.js
  ├─ GET /health
  └─ GET /readiness
         ↓
      FastAPI
         ↓
  PostgreSQL / Supabase (sonde SELECT 1 bornée)
```

Le navigateur ne reçoit jamais `DATABASE_URL`. FastAPI neutralise les détails de connexion et retourne uniquement `ok` ou `unavailable` pour la base.

## Routes frontend

- `/` : accueil et positionnement responsable;
- `/dashboard` : synthèse opérationnelle;
- `/disponibilite` : contrôle direct de la chaîne publique;
- `/modules` : registre transparent des capacités;
- `/parametres` : configuration publique sans secret.

Les états `loading`, `empty`, `error` et `offline` sont explicites. La navigation est utilisable au clavier et adaptée aux écrans desktop, tablette et mobile. Les animations respectent `prefers-reduced-motion`.

## Contrats réseau

`NEXT_PUBLIC_API_URL` est la seule origine API exposée au navigateur. La valeur doit être une origine HTTPS exacte, sauf `localhost`, `127.0.0.1` ou `::1` autorisés en HTTP pour le développement.

`CORS_ORIGINS` est une liste d’origines exactes séparées par des virgules. Les wildcards, credentials, chemins, queries, fragments, schémas non HTTP(S), ports invalides et listes vides font échouer le démarrage.

Origines de production prévues :

```text
https://urim.pro
https://www.urim.pro
https://urim-web.onrender.com
```

## Variables Render frontend

| Variable | Valeur | Sensibilité |
|---|---|---|
| `NODE_ENV` | `production` | publique |
| `NODE_VERSION` | `22.22.0` | publique |
| `NEXT_TELEMETRY_DISABLED` | `1` | publique |
| `NEXT_PUBLIC_API_URL` | `https://urim-api-jrbk.onrender.com` | publique |
| `NEXT_PUBLIC_SITE_URL` | `https://urim.pro` | publique |

Aucune variable secrète n’est nécessaire au service frontend.

## Render et domaine

Le Blueprint `render.yaml` décrit un web service Node nommé `urim-web`, plan `free`, région `frankfurt`, build pnpm depuis la racine du monorepo et domaine `urim.pro`. Le sous-domaine Render reste actif jusqu’à la vérification DNS.

Après application du Blueprint :

1. ajouter ou vérifier `urim.pro` dans les domaines personnalisés du service;
2. chez le fournisseur DNS, supprimer les éventuels enregistrements `AAAA` incompatibles;
3. pointer l’apex avec `ANAME`/`ALIAS` vers le sous-domaine Render ou, à défaut, un `A` vers `216.24.57.1`;
4. pointer `www` avec un `CNAME` vers le sous-domaine `onrender.com`;
5. vérifier le domaine dans Render et attendre le certificat TLS;
6. conserver `https://urim.pro`, `https://www.urim.pro` et le sous-domaine Render dans `CORS_ORIGINS` du backend pendant la transition.

## Limites et risques

- Aucun déploiement ne doit charger ou modifier un secret depuis le dépôt.
- La disponibilité PostgreSQL est une sonde de connexion, pas une preuve d’intégrité métier.
- Un service Render gratuit peut subir un démarrage à froid; l’interface transforme le timeout en état d’erreur explicite.
- Les écrans ne présentent aucune fixture ou valeur par défaut comme donnée sportive réelle.
- Le domaine et le TLS exigent une action de contrôle dans le compte Render et chez le fournisseur DNS.

## Erreurs du catalogue couvertes

E005, E026, E049, E066, E071, E074, E075, E076, E077, E079, E083 et E084 : intégrité temporelle préservée par absence de prédiction, états manquants non convertis en valeurs réelles, secrets non exposés et limites produit visibles.
