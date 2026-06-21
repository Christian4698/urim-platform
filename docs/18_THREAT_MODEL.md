# Threat Model

| Menace | Contrôle |
|---|---|
| Vol de clé API | secret manager, rotation, egress controls |
| Injection de payload | validation, allowlists, canonicalisation |
| Rejeu de webhook | nonce, timestamp, idempotence |
| Falsification de prédiction | ledger immuable, hash, audit |
| Donnée future injectée | Temporal Guard et tests as-of |
| Provider spoofing | TLS et allowlist |
| Prompt injection via données | données traitées comme données, jamais comme instruction |
| Abus API | auth, quotas, rate limits |
| Fuite de données licenciées | règles de redistribution |
| Manipulation manuelle | append-only, RBAC, justification |
