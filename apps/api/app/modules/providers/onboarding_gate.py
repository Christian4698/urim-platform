from app.schemas.providers import (
    ProviderActivationChecklist,
    ProviderOnboardingGate,
    ProviderSecretReadiness,
)


def build_provider_onboarding_gate(
    checklist: ProviderActivationChecklist | None = None,
    secret_readiness: ProviderSecretReadiness | None = None,
) -> ProviderOnboardingGate:
    return ProviderOnboardingGate(
        checklist=checklist or ProviderActivationChecklist(),
        secret_readiness=secret_readiness or ProviderSecretReadiness(),
    )


def refuse_provider_activation(
    checklist: ProviderActivationChecklist | None = None,
    secret_readiness: ProviderSecretReadiness | None = None,
) -> ProviderOnboardingGate:
    return build_provider_onboarding_gate(
        checklist=checklist,
        secret_readiness=secret_readiness,
    )

