from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SportsProviderStatus(BaseModel):
    provider: Literal["api-football"] = "api-football"
    status: Literal[
        "ready",
        "disabled_by_configuration",
        "disabled_missing_credential",
        "degraded",
    ]
    enabled: bool
    configured: bool
    connected: bool
    last_success_at: datetime | None = None
    quota_remaining_daily: int | None = None
    quota_remaining_minute: int | None = None
    priority_competition_count: int = 0
    season: int | None = None
    max_requests_per_sync: int
    prediction_creation_enabled: Literal[False] = False
    live_automatic_enabled: Literal[False] = False
    bookmakers_enabled: Literal[False] = False
    betting_enabled: Literal[False] = False

    model_config = ConfigDict(extra="forbid")


class SportsProvenance(BaseModel):
    provider: Literal["api-football"] = "api-football"
    provider_event_id: str
    observed_at: datetime
    available_at: datetime
    fetched_at: datetime
    source_version: str
    quality_flags: list[str] = Field(default_factory=list)
    raw_hash: str
    freshness_status: str

    model_config = ConfigDict(extra="forbid")


class CompetitionRead(SportsProvenance):
    provider_competition_id: int
    name: str
    kind: str | None = None
    country_name: str | None = None
    country_code: str | None = None
    current_season: int | None = None
    coverage: dict[str, Any] = Field(default_factory=dict)


class MatchRead(SportsProvenance):
    provider_match_id: int
    provider_competition_id: int
    season: int
    kickoff_at: datetime
    timezone: str
    status_short: str
    status_long: str
    elapsed: int | None = None
    round: str | None = None
    venue_name: str | None = None
    venue_city: str | None = None
    home_team_provider_id: int
    home_team_name: str
    away_team_provider_id: int
    away_team_name: str
    goals_home: int | None = None
    goals_away: int | None = None
    score_halftime_home: int | None = None
    score_halftime_away: int | None = None
    score_fulltime_home: int | None = None
    score_fulltime_away: int | None = None


class MatchStatisticRead(SportsProvenance):
    provider_match_id: int
    provider_team_id: int
    statistic_type: str
    statistic_value: Any = None


class MatchEventRead(SportsProvenance):
    provider_match_id: int
    event_key: str
    elapsed: int | None = None
    extra: int | None = None
    provider_team_id: int | None = None
    team_name: str | None = None
    provider_player_id: int | None = None
    player_name: str | None = None
    provider_assist_id: int | None = None
    assist_name: str | None = None
    event_type: str
    detail: str | None = None
    comments: str | None = None


class LineupRead(SportsProvenance):
    provider_match_id: int
    provider_team_id: int
    team_name: str
    formation: str | None = None
    provider_coach_id: int | None = None
    coach_name: str | None = None
    provider_player_id: int | None = None
    player_name: str | None = None
    number: int | None = None
    position: str | None = None
    grid: str | None = None
    role: Literal["start_xi", "substitute"]


class InjuryRead(SportsProvenance):
    provider_match_id: int | None = None
    provider_competition_id: int | None = None
    season: int | None = None
    provider_team_id: int
    team_name: str
    provider_player_id: int
    player_name: str
    injury_type: str | None = None
    reason: str | None = None


class MatchDetailRead(BaseModel):
    match: MatchRead
    statistics: list[MatchStatisticRead] = Field(default_factory=list)
    events: list[MatchEventRead] = Field(default_factory=list)
    lineups: list[LineupRead] = Field(default_factory=list)
    injuries: list[InjuryRead] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class CompetitionCollection(BaseModel):
    items: list[CompetitionRead]
    count: int
    read_only: Literal[True] = True

    model_config = ConfigDict(extra="forbid")


class MatchCollection(BaseModel):
    items: list[MatchRead]
    count: int
    read_only: Literal[True] = True

    model_config = ConfigDict(extra="forbid")


class SyncRunRead(BaseModel):
    run_id: str
    sync_type: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    request_count: int
    records_received: int
    records_inserted: int
    records_duplicate: int
    records_rejected: int
    quota_remaining_daily: int | None = None
    quota_remaining_minute: int | None = None
    public_error_code: str | None = None

    model_config = ConfigDict(extra="forbid")


class SyncStatusRead(BaseModel):
    provider: Literal["api-football"] = "api-football"
    latest: SyncRunRead | None = None
    recent_errors: list[str] = Field(default_factory=list)
    read_only: Literal[True] = True

    model_config = ConfigDict(extra="forbid")


class ResourceFreshness(BaseModel):
    resource: str
    latest_fetched_at: datetime | None = None
    age_minutes: int | None = None
    status: Literal["fresh", "stale", "missing"]
    row_count: int

    model_config = ConfigDict(extra="forbid")


class FreshnessRead(BaseModel):
    as_of: datetime
    threshold_minutes: int
    resources: list[ResourceFreshness]
    read_only: Literal[True] = True

    model_config = ConfigDict(extra="forbid")


class SportsDateScope(BaseModel):
    date: date

    model_config = ConfigDict(extra="forbid")
