import json
import os
from collections.abc import Mapping
from typing import Any

from app.schemas.providers import ProviderSecretSafetySummary

FUTURE_PROVIDER_SECRET_ENV_NAMES: tuple[str, ...] = (
    "PROVIDER_API_KEY",
    "PROVIDER_API_SECRET",
    "PROVIDER_WEBHOOK_SECRET",
    "PROVIDER_CLIENT_ID",
    "PROVIDER_CLIENT_SECRET",
)


def build_provider_secret_safety_summary(
    environ: Mapping[str, str] | None = None,
) -> ProviderSecretSafetySummary:
    """Inspect future provider secret presence without exposing names or values.

    Phase 14 intentionally keeps provider activation blocked even if local
    developer secret values exist. Local presence is inspected only to preserve
    the future validation shape; it is never returned, logged or serialized.
    The returned model contains only public-safe categories, counts and disabled
    booleans.
    """
    environment = os.environ if environ is None else environ
    # Presence is deliberately consumed and discarded so public summaries never
    # reveal whether a developer has local provider secrets configured.
    _ = any(bool(environment.get(env_name)) for env_name in FUTURE_PROVIDER_SECRET_ENV_NAMES)
    return ProviderSecretSafetySummary()


def assert_public_payload_has_no_provider_secret_material(
    payload: Any,
    environ: Mapping[str, str] | None = None,
) -> None:
    """Reject public payloads that contain provider secret names or local values."""
    environment = os.environ if environ is None else environ
    serialized_payload = json.dumps(payload, default=str, sort_keys=True)

    if any(env_name in serialized_payload for env_name in FUTURE_PROVIDER_SECRET_ENV_NAMES):
        raise ValueError("public payload exposes provider secret metadata")

    for env_name in FUTURE_PROVIDER_SECRET_ENV_NAMES:
        secret_value = environment.get(env_name)
        if secret_value and secret_value in serialized_payload:
            raise ValueError("public payload exposes provider secret material")


def validate_env_example_provider_placeholders(env_text: str) -> None:
    """Ensure future provider secret placeholders exist only with empty values."""
    env_lines = set(env_text.splitlines())
    for env_name in FUTURE_PROVIDER_SECRET_ENV_NAMES:
        if f"{env_name}=" not in env_lines:
            raise ValueError("provider secret placeholders must remain empty")
