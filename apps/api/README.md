# URIM API

FastAPI backend for the URIM Kairos engine.

This package currently covers Phase 18 API-Football env-gated smoke client work:

- SQLAlchemy metadata for the PostgreSQL foundation schema.
- Alembic migrations for local and future controlled environments.
- Versioned FastAPI routes under `/api/v1`.
- API-first security headers, including a restrictive Content-Security-Policy.
- Thread-safe SQLAlchemy 2.0-style engine/session-factory reuse keyed by `DATABASE_URL`.
- Safety overrides that keep live prediction, production mocks, provider connectors, API-Football, bookmakers, prediction creation, and real betting disabled.
- Read-only provider readiness contracts under `/api/v1/providers/readiness`.
- Provider QA helpers for contract-only golden payload checks and payload redaction.
- Read-only sandbox provider status under `/api/v1/providers/sandbox/status`.
- Readiness-only onboarding, quota/rate-limit, and reconciliation requirements for future providers.
- Provider onboarding gate that blocks real provider activation until a future independent audit.
- Provider secret-safety summaries that expose only public-safe categories, counts and disabled booleans.
- Provider preflight safety review that keeps controlled real-provider preparation blocked.
- Real provider adapter shell status that documents a future API-Football provider shape while keeping network,
  credentials, HTTP client, provider URL, DB ingestion and prediction creation disabled.
- Provider activation readiness final gate that keeps provider activation blocked until license, terms, quotas,
  rate limits, latency, egress, secret management, redaction, monitoring, alerting, reconciliation, rollback,
  anonymized real golden payloads and security audit evidence are approved.
- API-Football read-only adapter status and blocked adapter methods for fixtures, results, team statistics,
  standings, lineups and events. The adapter is disabled by default and cannot call the network.
- API-Football test-only transport contracts for fixtures, results, team statistics, standings, lineups and
  events. These contracts use in-memory `TEST_ONLY` / `DEMO_NON_PROD` placeholders and have no public runtime.
- API-Football env-gated smoke client shape. It is internal, disabled by default, requires explicit local
  non-production opt-in and an injected transport, and never exposes local smoke configuration in public API
  responses.

It does not activate API-Football by default, train ML models, execute bets, create real predictions, create production sports results, or seed production data. The Bet Center remains virtual/internal only.

The Phase 18 CSP remains intentionally strict for an API surface:
`default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`.
It may restrict Swagger UI or ReDoc interactive rendering; an auth/docs portal is out of scope for Phase 18.

`official_result_envelope` remains a sandbox-only placeholder used to test future wiring shape. Real Official Result Verifier behavior and Post-Match Learning activation remain out of scope.

Future provider secret environment variable names are documented only in local configuration examples with empty values. Public API responses expose readiness categories and counts, never secret names or values.

The real provider shell is not a connector. It exposes only disabled metadata and raises a controlled
`ProviderNetworkDisabledError` before any future data-producing path could perform network I/O.

The API-Football read-only adapter is also not connected. It exposes only disabled status metadata and raises
`ApiFootballProviderDisabledError` before fixtures, results, statistics, standings, lineups or events could
perform network I/O.

The API-Football test transport is internal and test-only. It does not import provider HTTP clients, open
sockets, expose an endpoint, load credentials, ingest data, create predictions, connect bookmakers or execute
betting.

The API-Football smoke client is also internal. It refuses execution unless all local smoke conditions are met
and a transport is explicitly injected; public readiness remains false-by-default and redacted.

## Validation

From `apps/api`:

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

With local PostgreSQL available:

```bash
$env:DATABASE_URL="postgresql+psycopg://urim:urim_local_only@localhost:5432/urim_local"
alembic check
```

Future Post-Match Learning may learn only from verified `post_match_outcomes`, never from `tickets.user_declared_result` or `tickets.user_declared_profit_loss`.
