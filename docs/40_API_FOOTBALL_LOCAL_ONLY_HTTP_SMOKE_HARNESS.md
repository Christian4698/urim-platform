# API-Football Local-Only HTTP Smoke Harness

Phase 21 prepares a local-only HTTP smoke harness for API-Football without activating a provider. The harness is
not a FastAPI route, not a scheduler and not a production fallback. It can only be used from local Python code or a
terminal script, and it refuses by default.

## What It Adds
- A local script shape that delegates to the Phase 19 manual smoke runner.
- An explicitly injected request callable hook for future local smoke experiments.
- A public-safe result with `executed`, `provider`, `mode`, disabled DB/prediction/betting flags and an optional
  `payload_hash`.
- Output validation that rejects credentials, local provider configuration, raw provider URLs and payload material.

## What It Does Not Add
- No API-Football activation.
- No public endpoint.
- No concrete HTTP client.
- No committed provider URL.
- No committed credential or secret.
- No DB ingestion or raw payload storage.
- No prediction, ML, bookmaker, stake or betting path.
- No frontend or design change.

## Local-Only Contract
The harness accepts a request callable only through explicit Python injection. The default `main()` path does not
construct a callable and therefore returns the disabled public-safe result. Any real local experiment must stay
outside Git, outside prompts, outside logs and outside public responses.

The injected callable receives local configuration only after the Phase 18 gates pass: explicit smoke mode,
local auth material, local provider location, read-only confirmation, non-production confirmation, non-production
environment and blocked provider activation gate. If any condition is missing, the callable is not invoked.

## Safety Checklist
- Confirm the branch is dedicated to local smoke work.
- Keep local configuration untracked and outside `.env.example`.
- Keep credentials out of prompts, logs, docs and commits.
- Confirm `APP_ENV` is non-production.
- Confirm smoke mode, read-only and non-production flags explicitly.
- Use a mock/fake callable in automated tests.
- Confirm no DB writes, predictions, bookmaker actions, stakes or betting outputs are created.
- Verify the result contains no raw provider payload, URL, credential or local config names/values.

## Acceptance Criteria
- FastAPI does not import the harness.
- Plausible smoke, runbook and harness endpoints remain absent.
- Dangerous provider readiness methods remain `405`.
- Unit tests do not open sockets or call a real provider.
- Public readiness remains safe and does not expose local smoke configuration.
