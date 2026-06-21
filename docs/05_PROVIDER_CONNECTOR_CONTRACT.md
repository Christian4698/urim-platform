# Contrat des connecteurs

```text
health()
capabilities()
coverage()
fetch_competitions()
fetch_fixtures(window)
fetch_fixture(fixture_id)
fetch_lineups(fixture_id)
fetch_injuries(scope)
fetch_statistics(fixture_id)
fetch_live_events(fixture_id, cursor)
fetch_odds(event_id, market, as_of)
normalize(raw_payload)
```

## Réponse standard
`provider`, `request_id`, `provider_event_id`, `fetched_at`, `provider_timestamp`, `http_status`, `quota_remaining`, `raw_hash`, `payload_location`, `schema_version`, `warnings`, `data`.

## Obligations
Timeouts, retries ciblés, backoff+jitter, circuit breaker, idempotence, quotas, cache distinct, clés côté serveur, absence de donnée différente de zéro, schéma fournisseur isolé du canonique.
