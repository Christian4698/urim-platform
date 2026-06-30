from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.constants import DISABLED_STATUS
from app.schemas.common import ApiMetadata, build_metadata

ProviderCapabilityName = Literal[
    "fixtures",
    "results",
    "standings",
    "lineups",
    "events",
    "odds",
    "injuries",
]

PROVIDER_CAPABILITY_NAMES: tuple[ProviderCapabilityName, ...] = (
    "fixtures",
    "results",
    "standings",
    "lineups",
    "events",
    "odds",
    "injuries",
)

REQUIRED_PROVENANCE_FIELDS: tuple[str, ...] = (
    "provider",
    "provider_event_id",
    "observed_at",
    "available_at",
    "fetched_at",
    "source_version",
    "raw_hash",
    "quality_flags",
)

POST_MATCH_LEARNING_SOURCE = "post_match_outcomes_only"
DISALLOWED_LEARNING_SOURCES = (
    "tickets.user_declared_result",
    "tickets.user_declared_profit_loss",
)
SANDBOX_QA_MARKERS = ("DEMO_NON_PROD", "PLACEHOLDER", "SANDBOX_ONLY")

PROVIDER_QA_REQUIREMENTS = (
    "license_review_required",
    "quota_and_rate_limit_required",
    "golden_payloads_required",
    "payload_redaction_required",
    "monitoring_required",
    "independent_audit_required",
    "no_production_mock_fallback",
)
PROVIDER_QA_REQUIREMENTS_DESCRIPTION = (
    "QA requirements validate provider payload shape, provenance, redaction and contract behavior."
)

PROVIDER_ONBOARDING_REQUIREMENTS = (
    "license_review_required",
    "quota_documentation_required",
    "rate_limit_documentation_required",
    "latency_budget_required",
    "pagination_contract_required",
    "retry_policy_required",
    "circuit_breaker_policy_required",
    "payload_redaction_required",
    "monitoring_required",
    "reconciliation_plan_required",
    "anonymized_real_golden_payloads_required_before_activation",
    "security_audit_required",
)
PROVIDER_ONBOARDING_REQUIREMENTS_DESCRIPTION = (
    "Onboarding requirements cover business, operations and security prerequisites before real provider activation."
)

PROVIDER_ACTIVATION_BLOCKING_REASONS = (
    "real_provider_audit_not_completed",
    "license_not_validated",
    "quotas_not_documented",
    "rate_limits_not_documented",
    "latency_not_measured",
    "pagination_not_documented",
    "retry_and_circuit_breaker_not_defined",
    "redaction_not_verified",
    "monitoring_not_defined",
    "reconciliation_strategy_not_defined",
    "anonymized_real_golden_payloads_missing",
    "security_audit_not_validated",
    "secure_secret_management_not_validated",
    "phase_10_blocks_real_provider_activation",
)

PROVIDER_SECRET_READINESS_CATEGORIES = (
    "provider_auth_material",
    "webhook_signing_material",
    "client_auth_material",
)

RATE_LIMIT_QUOTA_CONTRACTS = (
    "quota_contract_status=readiness_only",
    "rate_limit_contract_status=readiness_only",
    "retry_execution=disabled",
    "circuit_breaker_execution=disabled",
    "scheduler=disabled",
    "queue=disabled",
    "provider_network_calls=disabled",
)

RECONCILIATION_READINESS_REQUIREMENTS = (
    "canonical_entity_mapping_required",
    "field_level_provenance_required",
    "conflict_marking_required",
    "silent_overwrite_forbidden",
    "critical_conflict_blocks_future_predictions",
    "database_writes=disabled_in_phase_10",
)

SANDBOX_INTEGRATION_FLOW = (
    "identity",
    "payloads",
    "raw_reference",
    "observation",
    "quality_report",
    "canonical_mapping_placeholder",
    "official_result_envelope_placeholder",
)


def _require_aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError("provider timestamps must be timezone-aware")
    return value


class ProviderIdentity(BaseModel):
    provider: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    enabled: Literal[False] = False
    api_football_connected: Literal[False] = False
    network_calls_enabled: Literal[False] = False
    credentials_configured: Literal[False] = False
    production_mock_fallback_allowed: Literal[False] = False

    model_config = ConfigDict(extra="forbid")


class ProviderActivationChecklist(BaseModel):
    license_validated: Literal[False] = False
    quotas_known: Literal[False] = False
    rate_limits_known: Literal[False] = False
    latency_measured: Literal[False] = False
    pagination_documented: Literal[False] = False
    retries_defined: Literal[False] = False
    circuit_breaker_defined: Literal[False] = False
    redaction_verified: Literal[False] = False
    monitoring_defined: Literal[False] = False
    reconciliation_strategy_defined: Literal[False] = False
    anonymized_real_golden_payloads_available: Literal[False] = False
    security_audit_validated: Literal[False] = False
    secure_env_secret_management_validated: Literal[False] = False

    model_config = ConfigDict(extra="forbid")


class ProviderSecretReadiness(BaseModel):
    configured: Literal[False] = False
    secret_values_present: Literal[False] = False
    public_env_var_names_exposed: Literal[False] = False
    secret_categories: list[str] = Field(default_factory=lambda: list(PROVIDER_SECRET_READINESS_CATEGORIES))
    expected_secret_count: int = len(PROVIDER_SECRET_READINESS_CATEGORIES)
    storage_requirement: str = "future_secret_manager_or_secure_environment_only"

    model_config = ConfigDict(extra="forbid")


class ProviderOnboardingGate(BaseModel):
    status: str = "blocked_until_real_provider_audit"
    can_activate: Literal[False] = False
    providers_enabled: Literal[False] = False
    api_football_connected: Literal[False] = False
    network_calls_enabled: Literal[False] = False
    db_ingestion_enabled: Literal[False] = False
    checklist: ProviderActivationChecklist = Field(default_factory=ProviderActivationChecklist)
    secret_readiness: ProviderSecretReadiness = Field(default_factory=ProviderSecretReadiness)
    blocking_reasons: list[str] = Field(default_factory=lambda: list(PROVIDER_ACTIVATION_BLOCKING_REASONS))
    qa_requirements_description: str = PROVIDER_QA_REQUIREMENTS_DESCRIPTION
    onboarding_requirements_description: str = PROVIDER_ONBOARDING_REQUIREMENTS_DESCRIPTION

    model_config = ConfigDict(extra="forbid")


class ProviderCapability(BaseModel):
    capability: ProviderCapabilityName
    enabled: Literal[False] = False
    status: str = DISABLED_STATUS

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def require_disabled_status(self) -> Self:
        if self.status != DISABLED_STATUS:
            raise ValueError("provider capabilities must remain disabled in Phase 10")
        return self


class ProviderCapabilityMatrix(BaseModel):
    fixtures: ProviderCapability = Field(default_factory=lambda: ProviderCapability(capability="fixtures"))
    results: ProviderCapability = Field(default_factory=lambda: ProviderCapability(capability="results"))
    standings: ProviderCapability = Field(default_factory=lambda: ProviderCapability(capability="standings"))
    lineups: ProviderCapability = Field(default_factory=lambda: ProviderCapability(capability="lineups"))
    events: ProviderCapability = Field(default_factory=lambda: ProviderCapability(capability="events"))
    odds: ProviderCapability = Field(default_factory=lambda: ProviderCapability(capability="odds"))
    injuries: ProviderCapability = Field(default_factory=lambda: ProviderCapability(capability="injuries"))

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def require_matching_disabled_capabilities(self) -> Self:
        for capability_name in PROVIDER_CAPABILITY_NAMES:
            capability = getattr(self, capability_name)
            if capability.capability != capability_name:
                raise ValueError("provider capability matrix entries must match their field names")
            if capability.enabled is not False or capability.status != DISABLED_STATUS:
                raise ValueError("provider capability matrix must remain fully disabled in Phase 10")
        return self

    def as_list(self) -> list[ProviderCapability]:
        return [getattr(self, capability_name) for capability_name in PROVIDER_CAPABILITY_NAMES]


class TemporalAvailabilityMetadata(BaseModel):
    provider: str = Field(min_length=1)
    provider_event_id: str = Field(min_length=1)
    observed_at: datetime
    available_at: datetime
    fetched_at: datetime
    source_version: str = Field(min_length=1)
    raw_hash: str = Field(min_length=1)
    quality_flags: list[str]

    model_config = ConfigDict(extra="forbid")

    @field_validator("observed_at", "available_at", "fetched_at")
    @classmethod
    def timestamps_must_be_aware(cls, value: datetime) -> datetime:
        return _require_aware_datetime(value)

    @model_validator(mode="after")
    def validate_temporal_order(self) -> Self:
        if not self.observed_at <= self.available_at <= self.fetched_at:
            raise ValueError("provider timestamps must satisfy observed_at <= available_at <= fetched_at")
        return self


class RawPayloadReference(BaseModel):
    provider: str = Field(min_length=1)
    provider_event_id: str = Field(min_length=1)
    fetched_at: datetime
    source_version: str = Field(min_length=1)
    raw_hash: str = Field(min_length=1)
    endpoint: str | None = None
    storage_uri: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @field_validator("fetched_at")
    @classmethod
    def fetched_at_must_be_aware(cls, value: datetime) -> datetime:
        return _require_aware_datetime(value)


class ProviderObservation(TemporalAvailabilityMetadata):
    raw_payload_ref: RawPayloadReference | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class CanonicalEntityMapping(BaseModel):
    provider: str = Field(min_length=1)
    provider_entity_id: str = Field(min_length=1)
    provider_entity_type: str = Field(min_length=1)
    canonical_entity_id: str | None = None
    valid_from: datetime
    valid_to: datetime | None = None
    confidence: float = Field(ge=0, le=1)
    quality_flags: list[str]

    model_config = ConfigDict(extra="forbid")

    @field_validator("valid_from", "valid_to")
    @classmethod
    def validity_timestamps_must_be_aware(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return _require_aware_datetime(value)

    @model_validator(mode="after")
    def validate_validity_order(self) -> Self:
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("valid_to must be greater than or equal to valid_from")
        return self


class OfficialResultEnvelope(TemporalAvailabilityMetadata):
    result_payload: dict[str, Any] = Field(default_factory=dict)
    learning_source: str = POST_MATCH_LEARNING_SOURCE
    disallowed_learning_sources: list[str] = Field(default_factory=lambda: list(DISALLOWED_LEARNING_SOURCES))

    @model_validator(mode="after")
    def validate_learning_source(self) -> Self:
        if self.learning_source != POST_MATCH_LEARNING_SOURCE:
            raise ValueError("official result learning source must be post_match_outcomes_only")
        return self


class DataQualityReport(BaseModel):
    status: str = "contract_only"
    providers_enabled: Literal[False] = False
    network_calls_enabled: Literal[False] = False
    production_mock_fallback_allowed: Literal[False] = False
    required_fields: list[str] = Field(default_factory=lambda: list(REQUIRED_PROVENANCE_FIELDS))
    quality_flags: list[str] = Field(default_factory=list)
    temporal_order_valid: bool = True
    complete_provenance: bool = True

    model_config = ConfigDict(extra="forbid")


class ProviderReadinessResponse(BaseModel):
    metadata: ApiMetadata
    status: str = "provider_readiness_contract_only"
    providers_enabled: Literal[False] = False
    api_football_connected: Literal[False] = False
    network_calls_enabled: Literal[False] = False
    credentials_configured: Literal[False] = False
    provider_identities: list[ProviderIdentity] = Field(default_factory=list)
    capability_matrix: ProviderCapabilityMatrix = Field(default_factory=ProviderCapabilityMatrix)
    capabilities: list[ProviderCapability] = Field(default_factory=list)
    required_provenance_fields: list[str] = Field(default_factory=lambda: list(REQUIRED_PROVENANCE_FIELDS))
    temporal_contract: list[str] = Field(
        default_factory=lambda: [
            "observed_at <= available_at <= fetched_at",
            "available_at <= prediction_time",
        ]
    )
    quality_report: DataQualityReport = Field(default_factory=DataQualityReport)
    qa_requirements: list[str] = Field(default_factory=lambda: list(PROVIDER_QA_REQUIREMENTS))
    qa_requirements_description: str = PROVIDER_QA_REQUIREMENTS_DESCRIPTION
    onboarding_requirements: list[str] = Field(default_factory=lambda: list(PROVIDER_ONBOARDING_REQUIREMENTS))
    onboarding_requirements_description: str = PROVIDER_ONBOARDING_REQUIREMENTS_DESCRIPTION
    rate_limit_quota_contracts: list[str] = Field(default_factory=lambda: list(RATE_LIMIT_QUOTA_CONTRACTS))
    reconciliation_readiness: list[str] = Field(default_factory=lambda: list(RECONCILIATION_READINESS_REQUIREMENTS))
    onboarding_gate: ProviderOnboardingGate = Field(default_factory=ProviderOnboardingGate)
    post_match_learning_source: str = POST_MATCH_LEARNING_SOURCE
    disallowed_learning_sources: list[str] = Field(default_factory=lambda: list(DISALLOWED_LEARNING_SOURCES))
    safeguards: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class SandboxProviderStatusResponse(BaseModel):
    metadata: ApiMetadata
    status: str = "sandbox_provider_status"
    sandbox_mode: Literal["DEMO_NON_PROD"] = "DEMO_NON_PROD"
    provider_enabled: Literal[False] = False
    api_football_connected: Literal[False] = False
    network_calls_enabled: Literal[False] = False
    credentials_configured: Literal[False] = False
    db_ingestion_enabled: Literal[False] = False
    prediction_creation_enabled: Literal[False] = False
    production_mock_fallback_allowed: Literal[False] = False
    provider_identity: ProviderIdentity
    payload_count: int
    raw_hashes: list[str]
    capabilities: list[ProviderCapability]
    qa_markers: list[str] = Field(default_factory=lambda: list(SANDBOX_QA_MARKERS))
    onboarding_gate: ProviderOnboardingGate = Field(default_factory=ProviderOnboardingGate)
    onboarding_requirements: list[str] = Field(default_factory=lambda: list(PROVIDER_ONBOARDING_REQUIREMENTS))
    rate_limit_quota_contracts: list[str] = Field(default_factory=lambda: list(RATE_LIMIT_QUOTA_CONTRACTS))
    reconciliation_readiness: list[str] = Field(default_factory=lambda: list(RECONCILIATION_READINESS_REQUIREMENTS))
    sandbox_integration_flow: list[str] = Field(default_factory=lambda: list(SANDBOX_INTEGRATION_FLOW))
    payload_summaries: list[dict[str, Any]] = Field(default_factory=list)
    safeguards: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


def disabled_provider_capabilities() -> list[ProviderCapability]:
    return ProviderCapabilityMatrix().as_list()


def build_provider_readiness_response() -> ProviderReadinessResponse:
    capability_matrix = ProviderCapabilityMatrix()
    onboarding_gate = ProviderOnboardingGate()
    return ProviderReadinessResponse(
        metadata=build_metadata(),
        provider_identities=[
            ProviderIdentity(
                provider="api-football",
                display_name="API-Football future contract only",
            )
        ],
        capability_matrix=capability_matrix,
        capabilities=capability_matrix.as_list(),
        onboarding_gate=onboarding_gate,
        safeguards=[
            "Provider contracts are defined but no provider connector is active.",
            "API-Football is not connected.",
            "No outbound provider network calls are enabled.",
            "No provider credentials are configured or exposed.",
            "Provider onboarding gate blocks activation until a real provider audit is completed.",
            "Future provider secret names are documented only outside public API responses and must remain empty until secure secret management exists.",
            "Production mock fallback is forbidden.",
            "Provider QA requires license review, quotas, redaction, monitoring and independent audit.",
            "Provider onboarding requires quota, rate-limit, latency, pagination, retry, circuit breaker, reconciliation and security audit readiness before activation.",
            "Rate-limit and quota contracts are readiness-only; no scheduler, queue, retry execution or provider network call is enabled.",
            "Provider reconciliation readiness is documented without database writes or canonical overwrites.",
            "Sandbox provider status is informational, non-production and does not enable providers.",
            "Post-Match Learning may use only verified post_match_outcomes in a future phase.",
        ],
    )
