# integrations/ (mock-only scaffold)

No third-party API is wired here. This folder prepares URIM typed contracts and
demo providers only.

- `types/`: canonical TypeScript contracts with provenance, not raw provider JSON.
- `mocks/`: plausible mock/demo providers. Every response is flagged as mock data.
- `providers/`: registry/factory that exposes the mock providers and rejects LIVE
  or real-provider activation.
- `config/`: frontend-safe runtime gates. No secret is read from this folder.

Current guarantees:

- DEMO/MOCK is the default and only active mode.
- LIVE is forcibly OFF.
- No API key is referenced in frontend code.
- No frontend call is made to a third-party provider.
- URIM mocks cover football fixtures, team statistics, odds/value, weather, and
  match news/events.
- URIM exchange-rate mocks cover display-only CDF/USD conversion.
- API-Football is not duplicated here; future changes to the existing real
  adapter stay in `apps/api/app/modules/providers/`.

Future real integrations must be implemented as backend adapters first, under
the existing provider pattern in `apps/api/app/modules/providers/`, and must pass
the onboarding gates in `docs/28_PROVIDER_ONBOARDING_CHECKLIST.md` and related
readiness documents before this frontend registry points to any backend proxy.
