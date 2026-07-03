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
API_FOOTBALL_TEST_RESPONSE_CONTRACTS = (
    "fixtures",
    "results",
    "team_statistics",
    "standings",
    "lineups",
    "events",
)

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
    "phase_14_keeps_real_provider_activation_blocked",
)

PROVIDER_SECRET_READINESS_CATEGORIES = (
    "provider_auth_material",
    "webhook_signing_material",
    "client_auth_material",
)
EXPECTED_FUTURE_PROVIDER_SECRET_COUNT = 5

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
    "database_writes=disabled_in_phase_14",
)

PROVIDER_PREFLIGHT_BLOCKING_REASONS = (
    "real_provider_preflight_not_approved",
    "secret_manager_not_validated",
    "egress_controls_not_validated",
    "quota_and_rate_limit_plan_not_validated",
    "provider_license_not_validated",
    "monitoring_not_validated",
    "reconciliation_not_validated",
    "independent_audit_not_completed",
)

PROVIDER_PREFLIGHT_FUTURE_CHECKLIST = (
    "secret_manager_required",
    "egress_controls_required",
    "quota_and_rate_limit_required",
    "provider_license_required",
    "monitoring_required",
    "reconciliation_required",
    "independent_audit_required",
)

PROVIDER_FINAL_ACTIVATION_PREREQUISITES = (
    "license_review_completed",
    "provider_terms_accepted",
    "quota_limits_documented",
    "rate_limits_documented",
    "latency_budget_defined",
    "egress_policy_defined",
    "secret_manager_validated",
    "log_redaction_validated",
    "monitoring_defined",
    "alerting_defined",
    "reconciliation_plan_defined",
    "rollback_plan_defined",
    "anonymized_real_golden_payloads_approved",
    "security_audit_completed",
)

PROVIDER_FINAL_ACTIVATION_BLOCKING_REASONS = (
    "license_review_not_completed",
    "provider_terms_not_accepted",
    "quota_limits_not_documented",
    "rate_limits_not_documented",
    "latency_budget_not_defined",
    "egress_policy_not_defined",
    "secret_manager_not_validated",
    "log_redaction_not_validated",
    "monitoring_not_defined",
    "alerting_not_defined",
    "reconciliation_plan_not_defined",
    "rollback_plan_not_defined",
    "anonymized_real_golden_payloads_not_approved",
    "security_audit_not_completed",
    "phase_15_final_gate_keeps_provider_activation_blocked",
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


class ProviderSecretSafetySummary(BaseModel):
    status: str = "provider_secret_safety_preparation_only"
    configured: Literal[False] = False
    missing: Literal[True] = True
    providers_enabled: Literal[False] = False
    activation_allowed: Literal[False] = False
    raw_values_exposed: Literal[False] = False
    public_env_var_names_exposed: Literal[False] = False
    secret_categories: list[str] = Field(default_factory=lambda: list(PROVIDER_SECRET_READINESS_CATEGORIES))
    category_count: int = len(PROVIDER_SECRET_READINESS_CATEGORIES)
    # Kept as a schema-local count to avoid importing internal secret env names into public models.
    expected_secret_count: int = EXPECTED_FUTURE_PROVIDER_SECRET_COUNT
    storage_requirement: str = "future_secret_manager_or_secure_environment_only"
    safeguards: list[str] = Field(
        default_factory=lambda: [
            "Future provider secret values are never serialized in public API responses.",
            "Future provider secret environment names are internal-only and not returned publicly.",
            "Provider activation remains blocked until a real provider audit validates secret management.",
        ]
    )

    model_config = ConfigDict(extra="forbid")


class ProviderPreflightSafetyReview(BaseModel):
    status: Literal["blocked_until_real_provider_preflight_approved"] = (
        "blocked_until_real_provider_preflight_approved"
    )
    real_provider_preparation_ready: Literal[False] = False
    providers_enabled: Literal[False] = False
    network_calls_enabled: Literal[False] = False
    credentials_configured: Literal[False] = False
    db_ingestion_enabled: Literal[False] = False
    api_football_connected: Literal[False] = False
    blocking_reasons: list[str] = Field(default_factory=lambda: list(PROVIDER_PREFLIGHT_BLOCKING_REASONS))
    future_checklist: list[str] = Field(default_factory=lambda: list(PROVIDER_PREFLIGHT_FUTURE_CHECKLIST))
    decision: Literal["blocked"] = "blocked"
    decision_rationale: str = (
        "Real-provider preparation remains blocked until secret management, egress, quota, license, "
        "monitoring, reconciliation and independent audit evidence are approved."
    )

    model_config = ConfigDict(extra="forbid")


class ProviderRealProviderShellStatus(BaseModel):
    label: Literal["api_football_future_provider_shell"] = "api_football_future_provider_shell"
    status: Literal["blocked_shell_only"] = "blocked_shell_only"
    provider_enabled: Literal[False] = False
    providers_enabled: Literal[False] = False
    api_football_connected: Literal[False] = False
    network_calls_enabled: Literal[False] = False
    credentials_configured: Literal[False] = False
    http_client_enabled: Literal[False] = False
    provider_base_url_configured: Literal[False] = False
    provider_endpoint_configured: Literal[False] = False
    real_requests_enabled: Literal[False] = False
    db_ingestion_enabled: Literal[False] = False
    prediction_creation_enabled: Literal[False] = False
    production_payloads_enabled: Literal[False] = False
    safeguards: list[str] = Field(
        default_factory=lambda: [
            "Real provider adapter shell is informational and blocked in Phase 14.",
            "No HTTP client, provider URL, endpoint path, credential or request execution is configured.",
            "Provider egress guard blocks all future real-provider network attempts.",
        ]
    )

    model_config = ConfigDict(extra="forbid")


class ProviderFinalActivationPrerequisites(BaseModel):
    license_review_completed: Literal[False] = False
    provider_terms_accepted: Literal[False] = False
    quota_limits_documented: Literal[False] = False
    rate_limits_documented: Literal[False] = False
    latency_budget_defined: Literal[False] = False
    egress_policy_defined: Literal[False] = False
    secret_manager_validated: Literal[False] = False
    log_redaction_validated: Literal[False] = False
    monitoring_defined: Literal[False] = False
    alerting_defined: Literal[False] = False
    reconciliation_plan_defined: Literal[False] = False
    rollback_plan_defined: Literal[False] = False
    anonymized_real_golden_payloads_approved: Literal[False] = False
    security_audit_completed: Literal[False] = False

    model_config = ConfigDict(extra="forbid")


class ProviderActivationReadinessFinalGate(BaseModel):
    status: Literal["blocked_until_provider_activation_final_gate_approved"] = (
        "blocked_until_provider_activation_final_gate_approved"
    )
    can_activate_provider: Literal[False] = False
    providers_enabled: Literal[False] = False
    api_football_connected: Literal[False] = False
    network_calls_enabled: Literal[False] = False
    db_ingestion_enabled: Literal[False] = False
    credentials_accepted: Literal[False] = False
    production_provider_allowed: Literal[False] = False
    prerequisites: ProviderFinalActivationPrerequisites = Field(default_factory=ProviderFinalActivationPrerequisites)
    required_prerequisites: list[str] = Field(default_factory=lambda: list(PROVIDER_FINAL_ACTIVATION_PREREQUISITES))
    blocking_reasons: list[str] = Field(default_factory=lambda: list(PROVIDER_FINAL_ACTIVATION_BLOCKING_REASONS))
    decision: Literal["blocked"] = "blocked"
    decision_rationale: str = (
        "Real provider activation remains blocked until license, terms, quotas, rate limits, latency, egress, "
        "secret management, redaction, monitoring, alerting, reconciliation, rollback, anonymized real golden "
        "payloads and security audit evidence are approved."
    )

    model_config = ConfigDict(extra="forbid")


class ProviderApiFootballReadOnlyAdapterStatus(BaseModel):
    label: Literal["api_football_read_only_adapter"] = "api_football_read_only_adapter"
    status: Literal["disabled_until_provider_activation_gate_approved"] = (
        "disabled_until_provider_activation_gate_approved"
    )
    enabled: Literal[False] = False
    connected: Literal[False] = False
    network_calls_enabled: Literal[False] = False
    db_ingestion_enabled: Literal[False] = False
    credentials_loaded: Literal[False] = False
    prediction_creation_enabled: Literal[False] = False
    betting_enabled: Literal[False] = False
    safeguards: list[str] = Field(
        default_factory=lambda: [
            "API-Football read-only adapter is disabled by default in Phase 16.",
            "Network access, credentials, DB ingestion, prediction creation and betting remain blocked.",
            "Provider activation readiness final gate must be approved before any real provider call exists.",
        ]
    )

    model_config = ConfigDict(extra="forbid")


class ProviderApiFootballTestTransportContractsStatus(BaseModel):
    label: Literal["api_football_test_transport_contracts"] = "api_football_test_transport_contracts"
    status: Literal["test_only_contracts_no_public_runtime"] = "test_only_contracts_no_public_runtime"
    test_transport_enabled: Literal[False] = False
    public_endpoint_enabled: Literal[False] = False
    network_calls_enabled: Literal[False] = False
    db_ingestion_enabled: Literal[False] = False
    credentials_loaded: Literal[False] = False
    prediction_creation_enabled: Literal[False] = False
    betting_enabled: Literal[False] = False
    production_payloads_enabled: Literal[False] = False
    real_provider_connected: Literal[False] = False
    response_contracts: list[str] = Field(default_factory=lambda: list(API_FOOTBALL_TEST_RESPONSE_CONTRACTS))
    required_markers: list[str] = Field(default_factory=lambda: ["TEST_ONLY", "DEMO_NON_PROD", "PLACEHOLDER"])
    safeguards: list[str] = Field(
        default_factory=lambda: [
            "API-Football test transport contracts are internal test-only contracts.",
            "No public endpoint, provider network call, credential, DB ingestion, prediction creation or betting is enabled.",
            "Payloads must remain TEST_ONLY, DEMO_NON_PROD and PLACEHOLDER.",
        ]
    )

    model_config = ConfigDict(extra="forbid")


class ProviderApiFootballSmokeClientStatus(BaseModel):
    label: Literal["api_football_env_gated_smoke_client"] = "api_football_env_gated_smoke_client"
    status: Literal["disabled_until_explicit_local_smoke_env"] = "disabled_until_explicit_local_smoke_env"
    enabled_by_default: Literal[False] = False
    smoke_mode_enabled: Literal[False] = False
    network_calls_enabled_by_default: Literal[False] = False
    public_endpoint_enabled: Literal[False] = False
    db_ingestion_enabled: Literal[False] = False
    credentials_exposed: Literal[False] = False
    prediction_creation_enabled: Literal[False] = False
    betting_enabled: Literal[False] = False
    real_provider_connected: Literal[False] = False
    safeguards: list[str] = Field(
        default_factory=lambda: [
            "API-Football smoke client is internal and disabled by default in Phase 18.",
            "Smoke execution requires explicit local non-production opt-in and an injected transport.",
            "Public readiness never exposes smoke environment variable names, values, provider URLs or credentials.",
            "Smoke responses are not ingested into the database and cannot create predictions or betting actions.",
        ]
    )

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
            raise ValueError("provider capabilities must remain disabled in Phase 14")
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
                raise ValueError("provider capability matrix must remain fully disabled in Phase 14")
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
    secret_safety: ProviderSecretSafetySummary = Field(default_factory=ProviderSecretSafetySummary)
    preflight_review: ProviderPreflightSafetyReview = Field(default_factory=ProviderPreflightSafetyReview)
    real_provider_shell_status: ProviderRealProviderShellStatus = Field(
        default_factory=ProviderRealProviderShellStatus
    )
    activation_readiness_final_gate: ProviderActivationReadinessFinalGate = Field(
        default_factory=ProviderActivationReadinessFinalGate
    )
    api_football_read_only_adapter_status: ProviderApiFootballReadOnlyAdapterStatus = Field(
        default_factory=ProviderApiFootballReadOnlyAdapterStatus
    )
    api_football_test_transport_contracts_status: ProviderApiFootballTestTransportContractsStatus = Field(
        default_factory=ProviderApiFootballTestTransportContractsStatus
    )
    api_football_smoke_client_status: ProviderApiFootballSmokeClientStatus = Field(
        default_factory=ProviderApiFootballSmokeClientStatus
    )
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
    secret_safety: ProviderSecretSafetySummary = Field(default_factory=ProviderSecretSafetySummary)
    preflight_review: ProviderPreflightSafetyReview = Field(default_factory=ProviderPreflightSafetyReview)
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
    from app.modules.providers.activation_readiness_final_gate import (
        build_provider_activation_readiness_final_gate,
    )
    from app.modules.providers.api_football_adapter import build_api_football_read_only_adapter_status
    from app.modules.providers.api_football_smoke_client import build_api_football_smoke_client_status
    from app.modules.providers.api_football_transport import build_api_football_test_transport_contracts_status
    from app.modules.providers.real_provider_shell import build_real_provider_shell_status
    from app.modules.providers.secret_safety import build_provider_secret_safety_summary

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
        secret_safety=build_provider_secret_safety_summary(),
        preflight_review=ProviderPreflightSafetyReview(),
        real_provider_shell_status=build_real_provider_shell_status(),
        activation_readiness_final_gate=build_provider_activation_readiness_final_gate(),
        api_football_read_only_adapter_status=build_api_football_read_only_adapter_status(),
        api_football_test_transport_contracts_status=build_api_football_test_transport_contracts_status(),
        api_football_smoke_client_status=build_api_football_smoke_client_status(),
        safeguards=[
            "Provider contracts are defined but no provider connector is active.",
            "API-Football is not connected.",
            "API-Football read-only adapter is present only as a disabled Phase 16 structure.",
            "API-Football test transport contracts are internal TEST_ONLY structures with no public runtime.",
            "API-Football smoke client is an internal Phase 18 structure gated by explicit local configuration.",
            "API-Football manual smoke runner and local HTTP smoke harness stay local-only and are never public endpoints.",
            "No outbound provider network calls are enabled.",
            "No provider credentials are configured or exposed.",
            "Provider onboarding gate blocks activation until a real provider audit is completed.",
            "Future provider secret names and values are never exposed in public API responses.",
            "Future provider secret placeholders must remain empty until secure secret management exists.",
            "Production mock fallback is forbidden.",
            "Provider QA requires license review, quotas, redaction, monitoring and independent audit.",
            "Provider onboarding requires quota, rate-limit, latency, pagination, retry, circuit breaker, reconciliation and security audit readiness before activation.",
            "Rate-limit and quota contracts are readiness-only; no scheduler, queue, retry execution or provider network call is enabled.",
            "Provider reconciliation readiness is documented without database writes or canonical overwrites.",
            "Provider preflight review remains blocked until a future explicit audit approval.",
            "Real provider adapter shell is present only as a blocked structure with no URL, credential, HTTP client or request path.",
            "Provider activation readiness final gate remains blocked until all final prerequisites are approved.",
            "API-Football read-only adapter refuses fixtures, results, team statistics, standings, lineups and events by default.",
            "API-Football test transport payloads must stay DEMO_NON_PROD placeholders and must never be production fallback.",
            "Sandbox provider status is informational, non-production and does not enable providers.",
            "Post-Match Learning may use only verified post_match_outcomes in a future phase.",
        ],
    )
