from app.schemas.providers import (
    ProviderActivationChecklist,
    ProviderOnboardingGate,
    ProviderSecretReadiness,
)


def build_provider_onboarding_gate(
    checklist: ProviderActivationChecklist | None = None,
    secret_readiness: ProviderSecretReadiness | None = None,
) -> ProviderOnboardingGate:
    """Build a safe blocked gate, resetting any caller-provided sub-objects.

    Phase 11 deliberately ignores checklist and secret-readiness inputs because
    they may have been created with Pydantic `model_construct` and bypassed
    `Literal[False]` validation. Real activation remains future work.
    """
    _ = (checklist, secret_readiness)
    return ProviderOnboardingGate(
        checklist=ProviderActivationChecklist(),
        secret_readiness=ProviderSecretReadiness(),
    )


def refuse_provider_activation(
    checklist: ProviderActivationChecklist | None = None,
    secret_readiness: ProviderSecretReadiness | None = None,
) -> ProviderOnboardingGate:
    """Return a structurally blocked provider activation gate.

    The gate is blocked by Pydantic `Literal[False]` fields and by resetting
    all caller-provided checklist and secret-readiness inputs to safe defaults.
    This function does not contain conditional activation logic in Phase 11.
    """
    return build_provider_onboarding_gate(
        checklist=checklist,
        secret_readiness=secret_readiness,
    )
