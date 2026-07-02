from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
import hashlib
import json
from typing import Any, Literal, Protocol, Self, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.providers import ProviderApiFootballTestTransportContractsStatus

API_FOOTBALL_TEST_PROVIDER_NAME = "api-football-test-transport"
API_FOOTBALL_TEST_SOURCE_VERSION = "API_FOOTBALL_TEST_TRANSPORT_DEMO_NON_PROD_v1"
TEST_ONLY_MARKER = "TEST_ONLY"
DEMO_NON_PROD_MARKER = "DEMO_NON_PROD"
PLACEHOLDER_MARKER = "PLACEHOLDER"
API_FOOTBALL_TEST_QUALITY_FLAGS = (
    TEST_ONLY_MARKER,
    DEMO_NON_PROD_MARKER,
    PLACEHOLDER_MARKER,
    "API_FOOTBALL_TEST_TRANSPORT",
)
API_FOOTBALL_RESPONSE_KINDS = (
    "fixtures",
    "results",
    "team_statistics",
    "standings",
    "lineups",
    "events",
)

SENSITIVE_PAYLOAD_KEY_PARTS = (
    "api_key",
    "token",
    "authorization",
    "secret",
    "password",
    "bearer",
    "credential",
    "provider_credentials",
)
FORBIDDEN_PRODUCTION_DATA_KEY_PARTS = (
    "score",
    "scores",
    "winner",
    "odds",
    "bookmaker",
    "stake",
    "betting",
)
FORBIDDEN_PUBLIC_URL_FRAGMENTS = (
    "http://",
    "https://",
    "api-football.com",
    "api-sports",
    "rapidapi",
    "x-rapidapi",
    "www.",
)
FORBIDDEN_REAL_SPORTS_VALUES = (
    "Manchester",
    "Real Madrid",
    "Barcelona",
    "PSG",
    "Liverpool",
    "Chelsea",
    "Bayern",
    "Juventus",
    "Premier League",
    "Champions League",
    "Ligue 1",
    "Serie A",
    "La Liga",
    "Bundesliga",
)


def _json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, Mapping):
        return {str(key): _json_ready(nested_value) for key, nested_value in value.items()}

    if isinstance(value, list | tuple):
        return [_json_ready(item) for item in value]

    return value


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def stable_raw_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _walk_mapping_keys(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        keys: list[str] = [str(key) for key in value]
        for nested_value in value.values():
            keys.extend(_walk_mapping_keys(nested_value))
        return keys

    if isinstance(value, list | tuple):
        keys = []
        for item in value:
            keys.extend(_walk_mapping_keys(item))
        return keys

    return []


def _walk_values(value: Any) -> list[Any]:
    if isinstance(value, Mapping):
        values: list[Any] = []
        for nested_value in value.values():
            values.extend(_walk_values(nested_value))
        return values

    if isinstance(value, list | tuple):
        values = []
        for item in value:
            values.extend(_walk_values(item))
        return values

    return [value]


def _contains_part(value: str, parts: tuple[str, ...]) -> bool:
    normalized_value = value.lower()
    return any(part.lower() in normalized_value for part in parts)


def _assert_payload_safe(payload: Mapping[str, Any]) -> None:
    for key in _walk_mapping_keys(payload):
        if _contains_part(key, SENSITIVE_PAYLOAD_KEY_PARTS):
            raise ValueError("API-Football test payload must not contain credential fields")
        if _contains_part(key, FORBIDDEN_PRODUCTION_DATA_KEY_PARTS):
            raise ValueError("API-Football test payload must not contain production sports data fields")

    for value in _walk_values(payload):
        if isinstance(value, str):
            if _contains_part(value, FORBIDDEN_PUBLIC_URL_FRAGMENTS):
                raise ValueError("API-Football test payload must not contain real provider URLs")
            if _contains_part(value, FORBIDDEN_REAL_SPORTS_VALUES):
                raise ValueError("API-Football test payload must not contain real sports names")
            if _contains_part(value, SENSITIVE_PAYLOAD_KEY_PARTS):
                raise ValueError("API-Football test payload must not contain credential values")


class ApiFootballTransportResponse(BaseModel):
    response_kind: str = Field(min_length=1)
    payload_marker: Literal["TEST_ONLY"] = TEST_ONLY_MARKER
    environment_marker: Literal["DEMO_NON_PROD"] = DEMO_NON_PROD_MARKER
    provider_name: str = Field(min_length=1)
    provider_event_id: str = Field(min_length=1)
    observed_at: datetime
    available_at: datetime
    fetched_at: datetime
    source_version: str = Field(min_length=1)
    raw_hash: str = Field(min_length=1)
    quality_flags: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    @field_validator("observed_at", "available_at", "fetched_at")
    @classmethod
    def timestamps_must_be_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("API-Football test transport timestamps must be timezone-aware")
        return value

    @model_validator(mode="after")
    def validate_test_transport_contract(self) -> Self:
        if self.provider_name != API_FOOTBALL_TEST_PROVIDER_NAME:
            raise ValueError("API-Football test transport provider_name is invalid")
        if not self.observed_at <= self.available_at <= self.fetched_at:
            raise ValueError("API-Football test timestamps must satisfy observed_at <= available_at <= fetched_at")
        for marker in (TEST_ONLY_MARKER, DEMO_NON_PROD_MARKER, PLACEHOLDER_MARKER):
            if marker not in self.quality_flags:
                raise ValueError(f"API-Football test payload missing required marker: {marker}")
        _assert_payload_safe(self.hash_source())
        if self.raw_hash != stable_raw_hash(self.hash_source()):
            raise ValueError("API-Football test payload raw_hash must match canonical payload")
        return self

    def hash_source(self) -> dict[str, Any]:
        return {
            "response_kind": self.response_kind,
            "payload_marker": self.payload_marker,
            "environment_marker": self.environment_marker,
            "provider_name": self.provider_name,
            "provider_event_id": self.provider_event_id,
            "observed_at": self.observed_at,
            "available_at": self.available_at,
            "fetched_at": self.fetched_at,
            "source_version": self.source_version,
            "quality_flags": list(self.quality_flags),
            "data": self.data,
        }


class ApiFootballFixtureResponse(ApiFootballTransportResponse):
    response_kind: Literal["fixtures"] = "fixtures"


class ApiFootballResultResponse(ApiFootballTransportResponse):
    response_kind: Literal["results"] = "results"


class ApiFootballTeamStatisticsResponse(ApiFootballTransportResponse):
    response_kind: Literal["team_statistics"] = "team_statistics"


class ApiFootballStandingsResponse(ApiFootballTransportResponse):
    response_kind: Literal["standings"] = "standings"


class ApiFootballLineupsResponse(ApiFootballTransportResponse):
    response_kind: Literal["lineups"] = "lineups"


class ApiFootballEventsResponse(ApiFootballTransportResponse):
    response_kind: Literal["events"] = "events"


@runtime_checkable
class ApiFootballTransportProtocol(Protocol):
    def fetch_fixtures(self, query: Mapping[str, Any] | None = None) -> ApiFootballFixtureResponse: ...

    def fetch_results(self, query: Mapping[str, Any] | None = None) -> ApiFootballResultResponse: ...

    def fetch_team_statistics(
        self,
        query: Mapping[str, Any] | None = None,
    ) -> ApiFootballTeamStatisticsResponse: ...

    def fetch_standings(self, query: Mapping[str, Any] | None = None) -> ApiFootballStandingsResponse: ...

    def fetch_lineups(self, query: Mapping[str, Any] | None = None) -> ApiFootballLineupsResponse: ...

    def fetch_events(self, query: Mapping[str, Any] | None = None) -> ApiFootballEventsResponse: ...


class ApiFootballTestTransport:
    """In-memory TEST_ONLY transport for API-Football response contract tests."""

    test_only = True
    demo_non_prod = True
    network_calls_enabled = False
    db_ingestion_enabled = False
    prediction_creation_enabled = False
    betting_enabled = False

    def fetch_fixtures(self, query: Mapping[str, Any] | None = None) -> ApiFootballFixtureResponse:
        _ = query
        return self._build_response(
            ApiFootballFixtureResponse,
            "fixtures",
            "PLACEHOLDER_API_FOOTBALL_FIXTURE_001",
            {
                "fixture_label": "PLACEHOLDER_FIXTURE_A",
                "competition_label": "PLACEHOLDER_COMPETITION",
                "home_entity_label": "PLACEHOLDER_HOME_ENTITY",
                "away_entity_label": "PLACEHOLDER_AWAY_ENTITY",
                "data_state": "PLACEHOLDER_NO_PRODUCTION_DATA",
            },
        )

    def fetch_results(self, query: Mapping[str, Any] | None = None) -> ApiFootballResultResponse:
        _ = query
        return self._build_response(
            ApiFootballResultResponse,
            "results",
            "PLACEHOLDER_API_FOOTBALL_OUTCOME_001",
            {
                "fixture_label": "PLACEHOLDER_FIXTURE_A",
                "outcome_state": "PLACEHOLDER_NO_OFFICIAL_OUTCOME",
                "data_state": "PLACEHOLDER_NO_PRODUCTION_DATA",
            },
        )

    def fetch_team_statistics(
        self,
        query: Mapping[str, Any] | None = None,
    ) -> ApiFootballTeamStatisticsResponse:
        _ = query
        return self._build_response(
            ApiFootballTeamStatisticsResponse,
            "team_statistics",
            "PLACEHOLDER_API_FOOTBALL_TEAM_STATS_001",
            {
                "team_entity_label": "PLACEHOLDER_TEAM_ENTITY",
                "fixture_label": "PLACEHOLDER_FIXTURE_A",
                "statistics_state": "PLACEHOLDER_NO_PRODUCTION_STATS",
                "metric_values": [],
            },
        )

    def fetch_standings(self, query: Mapping[str, Any] | None = None) -> ApiFootballStandingsResponse:
        _ = query
        return self._build_response(
            ApiFootballStandingsResponse,
            "standings",
            "PLACEHOLDER_API_FOOTBALL_STANDINGS_001",
            {
                "competition_label": "PLACEHOLDER_COMPETITION",
                "table_state": "PLACEHOLDER_NO_TABLE_DATA",
                "rows": [],
            },
        )

    def fetch_lineups(self, query: Mapping[str, Any] | None = None) -> ApiFootballLineupsResponse:
        _ = query
        return self._build_response(
            ApiFootballLineupsResponse,
            "lineups",
            "PLACEHOLDER_API_FOOTBALL_LINEUPS_001",
            {
                "fixture_label": "PLACEHOLDER_FIXTURE_A",
                "lineup_state": "PLACEHOLDER_NO_CONFIRMED_LINEUP",
                "participants": [],
            },
        )

    def fetch_events(self, query: Mapping[str, Any] | None = None) -> ApiFootballEventsResponse:
        _ = query
        return self._build_response(
            ApiFootballEventsResponse,
            "events",
            "PLACEHOLDER_API_FOOTBALL_EVENTS_001",
            {
                "fixture_label": "PLACEHOLDER_FIXTURE_A",
                "event_state": "PLACEHOLDER_NO_LIVE_EVENTS",
                "items": [],
            },
        )

    def _build_response(
        self,
        response_model: type[ApiFootballTransportResponse],
        response_kind: str,
        provider_event_id: str,
        data: dict[str, Any],
    ) -> ApiFootballTransportResponse:
        observed_at = datetime(2026, 1, 1, 8, 0, tzinfo=UTC)
        source_payload = {
            "response_kind": response_kind,
            "payload_marker": TEST_ONLY_MARKER,
            "environment_marker": DEMO_NON_PROD_MARKER,
            "provider_name": API_FOOTBALL_TEST_PROVIDER_NAME,
            "provider_event_id": provider_event_id,
            "observed_at": observed_at,
            "available_at": observed_at + timedelta(minutes=5),
            "fetched_at": observed_at + timedelta(minutes=10),
            "source_version": API_FOOTBALL_TEST_SOURCE_VERSION,
            "quality_flags": list(API_FOOTBALL_TEST_QUALITY_FLAGS),
            "data": data,
        }
        return response_model(
            **source_payload,
            raw_hash=stable_raw_hash(source_payload),
        )


def build_api_football_test_transport_contracts_status() -> ProviderApiFootballTestTransportContractsStatus:
    return ProviderApiFootballTestTransportContractsStatus()
