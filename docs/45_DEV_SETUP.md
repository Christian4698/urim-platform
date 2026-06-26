# Mise en place locale — URIM

## Prérequis

| Outil | Version minimale | Vérification |
|---|---|---|
| Python | 3.12 | `python --version` |
| Node.js | 20 LTS | `node --version` |
| Docker Desktop | 25+ | `docker --version` |
| Docker Compose | v2 (plugin) | `docker compose version` |
| Git | 2.40+ | `git --version` |
| make | — | `make --version` |

Créer un virtualenv Python avant toute installation :

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows PowerShell
```

## Variables d'environnement

Copier le fichier modèle (ne contient aucune vraie clé) :

```bash
cp .env.example .env.local
```

Fichier `.env.local` à remplir pour le développement local **uniquement** (jamais commité) :

```dotenv
# Base de données
DB_URL=postgresql+asyncpg://urim:urim@localhost:5432/urim_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT (local uniquement — générer avec: openssl rand -hex 32)
JWT_SECRET=changeme_local_only

# Origines autorisées
ALLOWED_ORIGINS=http://localhost:3000

# Protection contre les mocks de production
ALLOW_PRODUCTION_MOCKS=false
ALLOW_TEST_FIXTURES=true

# Clés fournisseurs (en développement, utiliser les fixtures de test)
# PROVIDER_X_API_KEY=<secret manager en production>

# Logs
LOG_LEVEL=DEBUG
REDACT_LOGS=false
```

`.env.local` est dans `.gitignore`. Ne jamais commiter de vrais secrets.

## Démarrage rapide

### 1. Démarrer l'infrastructure

```bash
docker compose up -d postgres redis
```

Attendre que PostgreSQL soit prêt :

```bash
docker compose exec postgres pg_isready -U urim
```

### 2. Initialiser la base de données

```bash
alembic upgrade head
```

### 3. Démarrer le backend API

```bash
cd apps/api
uvicorn main:app --reload --port 8000
```

Vérification : `curl http://localhost:8000/health` → `{"status":"ok"}`

### 4. Démarrer les services Python

```bash
# Worker Celery (dans un second terminal)
cd services/ingestion
celery -A worker worker --loglevel=info

# Service de prédiction
cd services/prediction
uvicorn main:app --reload --port 8001
```

### 5. Démarrer le frontend

```bash
cd apps/web
npm install
npm run dev
```

Frontend disponible sur `http://localhost:3000`.

## Commandes make usuelles

```bash
make install          # Installe toutes les dépendances
make db-up            # Démarre postgres + redis
make migrate          # Lance alembic upgrade head
make dev              # Démarre tous les services (api + web)
make test             # Lance tous les tests
make test-unit        # Tests unitaires uniquement
make test-temporal    # Gate temporelle (bloquante en CI)
make test-security    # Suite sécurité
make lint             # ruff + mypy + eslint
make secret-scan      # Gitleaks local
make docker-build     # Build toutes les images
```

## Installation des dépendances

```bash
# Backend
pip install -r requirements.lock

# Frontend
cd apps/web && npm ci
```

## Exécuter les tests

```bash
# Suite complète
pytest --tb=short

# Temporal gate (bloquant en CI)
pytest tests/temporal -x --tb=short

# Tests de contrat (providers)
pytest tests/contracts --tb=short

# Tests d'intégration
pytest tests/integration --tb=short -m integration

# Tests de sécurité
pytest tests/security --tb=short

# Property-based tests
pytest tests/property --tb=short

# Régression modèle
pytest tests/model_regression --tb=short
```

## Linting et types

```bash
# Python
ruff check .
mypy services/ apps/api/ packages/

# Frontend
cd apps/web
npm run lint
npm run type-check
```

## Migrations

```bash
# Créer une migration
alembic revision --autogenerate -m "description_courte"

# Appliquer
alembic upgrade head

# Vérifier l'état
alembic current

# Historique
alembic history
```

Les migrations des tables `predictions` et `audit_logs` sont irréversibles.

## Variables CI vs locales

| Variable | Local (.env.local) | CI (GitHub Secrets) | Production |
|---|---|---|---|
| `DB_URL` | Docker Compose | Service container | Secret manager |
| `JWT_SECRET` | chaîne locale | Secret chiffré | Secret manager |
| `PROVIDER_*_API_KEY` | Absente (fixtures) | Absente (dry-run) | Secret manager |
| `ALLOW_TEST_FIXTURES` | `true` | `true` (tests) | `false` (interdit) |
| `ALLOW_PRODUCTION_MOCKS` | `false` | `false` | `false` (interdit) |

## Prérequis CI avant connexion fournisseur réel

Les cinq conditions suivantes doivent être vertes avant tout appel API fournisseur réel :

1. `.gitignore` commité et `.env` absent du dépôt (`git ls-files .env` → vide).
2. Secret manager configuré (pas de clés dans les env vars CI en clair).
3. `config/provider-registry.yaml` présent (pas `.example`).
4. `pytest tests/contracts -v` → 100 % vert.
5. Job `temporal-gate` dans CI → 100 % vert.

## Structure Docker Compose

```yaml
# docker-compose.yml (résumé)
services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_USER: urim
      POSTGRES_PASSWORD: urim
      POSTGRES_DB: urim_dev
    ports: ["5432:5432"]
    volumes: ["postgres_data:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  api:
    build: ./apps/api
    depends_on: [postgres, redis]
    env_file: .env.local
    ports: ["8000:8000"]

  web:
    build: ./apps/web
    depends_on: [api]
    ports: ["3000:3000"]
```

## Diagnostics courants

| Problème | Diagnostic |
|---|---|
| `alembic upgrade head` échoue | Vérifier `DB_URL`, s'assurer que postgres est démarré |
| `Connection refused :5432` | `docker compose up -d postgres`, attendre `pg_isready` |
| JWT invalide | `JWT_SECRET` identique entre api et les services |
| Tests temporaux échouent | Vérifier `ALLOW_TEST_FIXTURES=true` en test |
| Port 8000 déjà utilisé | `lsof -i :8000` puis `kill <pid>` |
| `ALLOW_PRODUCTION_MOCKS` vrai en prod | INTERDIT — vérifier les variables d'environnement |
