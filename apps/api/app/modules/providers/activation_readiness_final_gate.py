from app.schemas.providers import (
    ProviderActivationReadinessFinalGate,
    ProviderFinalActivationPrerequisites,
)


def build_provider_activation_readiness_final_gate(
    prerequisites: ProviderFinalActivationPrerequisites | None = None,
    final_gate: ProviderActivationReadinessFinalGate | None = None,
) -> ProviderActivationReadinessFinalGate:
    """Build the final provider activation gate as blocked, ignoring caller input.

    Phase 15 resets caller-provided objects because they may have been created
    with Pydantic `model_construct` and bypassed `Literal[False]` validation.
    No conditional activation logic exists in this phase.
    """
    _ = (prerequisites, final_gate)
    return ProviderActivationReadinessFinalGate(
        prerequisites=ProviderFinalActivationPrerequisites(),
    )


def refuse_provider_final_activation(
    prerequisites: ProviderFinalActivationPrerequisites | None = None,
    final_gate: ProviderActivationReadinessFinalGate | None = None,
) -> ProviderActivationReadinessFinalGate:
    """Return a structurally blocked final activation gate for all callers."""
    return build_provider_activation_readiness_final_gate(
        prerequisites=prerequisites,
        final_gate=final_gate,
    )
