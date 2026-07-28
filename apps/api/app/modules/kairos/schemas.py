from __future__ import annotations

from datetime import date, datetime
import math
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


Sha256Hex = Annotated[
    str,
    Field(pattern=r"^[0-9a-fA-F]{64}$"),
]


class KairosProbabilities(BaseModel):
    home_win: float = Field(ge=0, le=1)
    draw: float = Field(ge=0, le=1)
    away_win: float = Field(ge=0, le=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def probabilities_sum_to_one(self) -> KairosProbabilities:
        values = (self.home_win, self.draw, self.away_win)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Kairos probabilities must be finite.")
        if abs(sum(values) - 1.0) > 1e-6:
            raise ValueError("Kairos probabilities must sum to one.")
        return self


class KairosMarketProbabilities(BaseModel):
    home_win: float = Field(ge=0, le=1)
    draw: float = Field(ge=0, le=1)
    away_win: float = Field(ge=0, le=1)
    home_or_draw: float = Field(ge=0, le=1)
    away_or_draw: float = Field(ge=0, le=1)
    home_or_away: float = Field(ge=0, le=1)
    over_2_5: float = Field(ge=0, le=1)
    under_2_5: float = Field(ge=0, le=1)
    btts: float = Field(ge=0, le=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_market_probabilities(self) -> KairosMarketProbabilities:
        values = tuple(self.__dict__.values())
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Kairos market probabilities must be finite.")
        if abs(self.home_win + self.draw + self.away_win - 1.0) > 1e-6:
            raise ValueError("Kairos 1X2 probabilities must sum to one.")
        if abs(self.over_2_5 + self.under_2_5 - 1.0) > 1e-6:
            raise ValueError("Kairos totals probabilities must sum to one.")
        if abs(self.home_or_draw - self.home_win - self.draw) > 1e-6:
            raise ValueError("home_or_draw is inconsistent with 1X2.")
        if abs(self.away_or_draw - self.away_win - self.draw) > 1e-6:
            raise ValueError("away_or_draw is inconsistent with 1X2.")
        if abs(self.home_or_away - self.home_win - self.away_win) > 1e-6:
            raise ValueError("home_or_away is inconsistent with 1X2.")
        return self


class KairosReason(BaseModel):
    code: str
    message: str
    direction: Literal["home", "draw", "away", "neutral"]

    model_config = ConfigDict(extra="forbid")


class KairosWarning(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning", "blocking"]

    model_config = ConfigDict(extra="forbid")


class KairosFeatureAvailability(BaseModel):
    home_samples: int = Field(ge=0)
    away_samples: int = Field(ge=0)
    required_samples_per_team: int = Field(ge=1)
    coverage_score: float = Field(ge=0, le=100)
    available_for_both_teams: bool

    model_config = ConfigDict(extra="forbid")


class KairosDataFreshness(BaseModel):
    as_of: datetime
    max_available_at: datetime
    target_fetched_at: datetime
    target_age_minutes: int = Field(ge=0)
    status: Literal["fresh", "stale"]
    threshold_minutes: int = Field(ge=1)

    model_config = ConfigDict(extra="forbid")


class KairosProvenance(BaseModel):
    provider: Literal["api-football"] = "api-football"
    source_observation_count: int = Field(ge=1)
    source_observation_ids: list[str]
    source_raw_hashes: list[Sha256Hex]
    max_available_at: datetime
    feature_snapshot_hash: Sha256Hex

    model_config = ConfigDict(extra="forbid")


class KairosTeamSummary(BaseModel):
    provider_team_id: int = Field(gt=0)
    team_name: str
    recent_result_sample_size: int = Field(ge=0)
    venue_sample_size: int = Field(ge=0)
    form_points_per_game: float | None = Field(default=None, ge=0, le=3)
    goals_for_average: float | None = Field(default=None, ge=0)
    goals_against_average: float | None = Field(default=None, ge=0)
    standing_rank: int | None = Field(default=None, ge=1)

    model_config = ConfigDict(extra="forbid")


class KairosSuggestionReason(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=500)
    impact: Literal["positive", "negative", "neutral"]
    category: Literal["analytical", "guardrail"] = "analytical"
    critical: bool = False

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_reason_category(self) -> KairosSuggestionReason:
        if self.critical and self.category != "guardrail":
            raise ValueError("Only guardrail reasons can be critical.")
        return self


class KairosSuggestion(BaseModel):
    suggestion_version: Literal["kairos_daily_suggestions_v1"] = (
        "kairos_daily_suggestions_v1"
    )
    provider_match_id: int = Field(gt=0)
    kickoff_at: datetime
    home_team_name: str = Field(min_length=1, max_length=200)
    away_team_name: str = Field(min_length=1, max_length=200)
    recommendation: Literal[
        "Home Win",
        "Away Win",
        "Draw",
        "Double Chance",
        "Over 2.5",
        "Under 2.5",
        "BTTS",
        "NO_BET",
    ]
    recommendation_code: Literal[
        "HOME_WIN",
        "AWAY_WIN",
        "DRAW",
        "HOME_OR_DRAW",
        "AWAY_OR_DRAW",
        "HOME_OR_AWAY",
        "OVER_2_5",
        "UNDER_2_5",
        "BTTS",
        "NO_BET",
    ]
    kairos_score: float = Field(ge=0, le=100)
    confidence_level: Literal["blocked", "low", "medium", "high"]
    risk_level: Literal["high", "elevated", "guarded"]
    no_bet: bool
    reasons: list[KairosSuggestionReason] = Field(max_length=12)
    market_probabilities: KairosMarketProbabilities | None
    data_quality_score: float = Field(ge=0, le=100)
    technical_confidence_score: float = Field(ge=0, le=65)
    feature_snapshot_hash: Sha256Hex
    decision_hash: Sha256Hex
    analysis_path: str = Field(pattern=r"^/api/v1/kairos/matches/[1-9][0-9]*/analysis$")
    read_only: Literal[True] = True
    persisted: Literal[False] = False
    provider_calls: Literal[False] = False
    bookmaker_data_used: Literal[False] = False
    automatic_betting_enabled: Literal[False] = False
    live_automatic_enabled: Literal[False] = False
    not_for_betting: Literal[True] = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_recommendation_contract(self) -> KairosSuggestion:
        if self.no_bet != (self.recommendation == "NO_BET"):
            raise ValueError("NO_BET flag and recommendation must match.")
        if self.no_bet != (self.recommendation_code == "NO_BET"):
            raise ValueError("NO_BET flag and recommendation code must match.")
        if not self.no_bet and self.market_probabilities is None:
            raise ValueError("A suggestion requires market probabilities.")
        if not self.no_bet and self.kairos_score < 40:
            raise ValueError("A suggestion below the confidence gate is forbidden.")
        return self


class KairosAnalysisResponse(BaseModel):
    provider_match_id: int = Field(gt=0)
    kickoff_at: datetime
    prediction_id: UUID
    model_version: str
    feature_snapshot_id: UUID
    prediction_time: datetime
    market: Literal["1X2_PRE_MATCH"] = "1X2_PRE_MATCH"
    probabilities: KairosProbabilities | None
    market_probabilities: KairosMarketProbabilities | None
    home_win_probability: float | None = Field(default=None, ge=0, le=1)
    draw_probability: float | None = Field(default=None, ge=0, le=1)
    away_win_probability: float | None = Field(default=None, ge=0, le=1)
    calibration_bucket: Literal["UNCALIBRATED_B2_2_BASELINE"] = (
        "UNCALIBRATED_B2_2_BASELINE"
    )
    safety_decision: Literal["NO_BET", "INSUFFICIENT_DATA"] = Field(
        description=(
            "Garde-fou Kairos. Ce champ n'est jamais une recommandation de pari."
        )
    )
    decision: Literal["NO_BET", "INSUFFICIENT_DATA"] = Field(
        description=(
            "Alias de compatibilité de safety_decision; ne pas utiliser comme "
            "suggestion analytique."
        )
    )
    confidence_score: float = Field(ge=0, le=65)
    confidence_score_type: Literal[
        "analysis_reliability_not_outcome_probability"
    ] = "analysis_reliability_not_outcome_probability"
    data_quality_score: float = Field(ge=0, le=100)
    reasons: list[KairosReason]
    warnings: list[KairosWarning]
    data_freshness: KairosDataFreshness
    data_availability: dict[str, KairosFeatureAvailability]
    home_team: KairosTeamSummary
    away_team: KairosTeamSummary
    provenance: KairosProvenance
    analytical_suggestion: KairosSuggestion = Field(
        description=(
            "Suggestion analytique non calibrée, distincte du garde-fou Kairos."
        )
    )
    suggestion: KairosSuggestion = Field(
        description="Alias de compatibilité de analytical_suggestion."
    )
    odds_snapshot_id: None = None
    immutable_hash: Sha256Hex
    analysis_status: Literal["ready", "insufficient_data"]
    read_only: Literal[True] = True
    persisted: Literal[False] = False
    official_prediction_published: Literal[False] = False
    automatic_betting_enabled: Literal[False] = False
    live_automatic_enabled: Literal[False] = False
    not_for_betting: Literal[True] = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_probability_contract(self) -> KairosAnalysisResponse:
        if self.decision != self.safety_decision:
            raise ValueError("decision must mirror safety_decision.")
        if self.suggestion != self.analytical_suggestion:
            raise ValueError(
                "suggestion must mirror analytical_suggestion."
            )
        flat = (
            self.home_win_probability,
            self.draw_probability,
            self.away_win_probability,
        )
        if self.probabilities is None:
            if any(value is not None for value in flat):
                raise ValueError("Flat probabilities require a probability object.")
            if self.market_probabilities is not None:
                raise ValueError("Market probabilities require a 1X2 baseline.")
            if self.safety_decision != "INSUFFICIENT_DATA":
                raise ValueError("Missing probabilities require INSUFFICIENT_DATA.")
            if self.analysis_status != "insufficient_data":
                raise ValueError("Missing probabilities require insufficient_data.")
            if self.confidence_score != 0:
                raise ValueError("Missing probabilities require zero confidence.")
            return self

        expected = (
            self.probabilities.home_win,
            self.probabilities.draw,
            self.probabilities.away_win,
        )
        if any(value is None for value in flat):
            raise ValueError("All flat probabilities are required.")
        if any(
            abs(float(actual) - expected_value) > 1e-9
            for actual, expected_value in zip(flat, expected, strict=True)
        ):
            raise ValueError("Flat and nested probabilities must match.")
        if (
            self.safety_decision != "NO_BET"
            or self.analysis_status != "ready"
        ):
            raise ValueError("A computed B2.2 analysis remains NO_BET and ready.")
        if self.market_probabilities is None:
            raise ValueError("Ready analyses require market probabilities.")
        market_1x2 = (
            self.market_probabilities.home_win,
            self.market_probabilities.draw,
            self.market_probabilities.away_win,
        )
        if any(
            abs(actual - expected_value) > 1e-9
            for actual, expected_value in zip(
                market_1x2, expected, strict=True
            )
        ):
            raise ValueError("Market and 1X2 probabilities must match.")
        return self


class KairosFeatureDefinition(BaseModel):
    name: str
    version: str
    domain: Literal["pre_match_1x2"] = "pre_match_1x2"
    window_matches: int = Field(ge=1)
    ttl_minutes: int = Field(ge=1)
    dependencies: list[str]
    missing_policy: Literal["explicit_null_no_imputation"] = (
        "explicit_null_no_imputation"
    )

    model_config = ConfigDict(extra="forbid")


class KairosMethodologyResponse(BaseModel):
    model_version: str
    feature_schema_version: str
    market: Literal["1X2_PRE_MATCH"] = "1X2_PRE_MATCH"
    engine_type: Literal["deterministic_poisson_baseline"] = (
        "deterministic_poisson_baseline"
    )
    recent_window_matches: int
    minimum_results_per_team: int
    confidence_score_cap: int
    suggestion_version: Literal["kairos_daily_suggestions_v1"] = (
        "kairos_daily_suggestions_v1"
    )
    supported_suggestions: list[
        Literal[
            "Home Win",
            "Away Win",
            "Draw",
            "Double Chance",
            "Over 2.5",
            "Under 2.5",
            "BTTS",
            "NO_BET",
        ]
    ]
    suggestion_score_method: Literal[
        "minimum_of_normalized_signal_data_quality_and_technical_reliability"
    ] = "minimum_of_normalized_signal_data_quality_and_technical_reliability"
    suggestion_score_gate: Literal[40] = 40
    feature_registry: list[KairosFeatureDefinition]
    restrictions: list[str]
    calibration_status: Literal["not_calibrated"] = "not_calibrated"
    drift_monitoring_status: Literal["not_available"] = "not_available"
    read_only: Literal[True] = True
    db_writes: Literal[False] = False
    provider_calls: Literal[False] = False
    automatic_betting_enabled: Literal[False] = False
    live_automatic_enabled: Literal[False] = False
    not_for_betting: Literal[True] = True

    model_config = ConfigDict(extra="forbid")


class KairosDailySuggestionsResponse(BaseModel):
    local_date: date
    timezone: Literal["Africa/Kinshasa"] = "Africa/Kinshasa"
    as_of: datetime
    suggestion_count: int = Field(ge=0, le=12)
    evaluated_match_count: int = Field(ge=0, le=16)
    skipped_unsafe_match_count: int = Field(ge=0, le=16)
    suggestions: list[KairosSuggestion] = Field(max_length=12)
    warnings: list[str] = Field(max_length=4)
    read_only: Literal[True] = True
    db_writes: Literal[False] = False
    provider_calls: Literal[False] = False
    automatic_betting_enabled: Literal[False] = False
    live_automatic_enabled: Literal[False] = False
    not_for_betting: Literal[True] = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_daily_contract(self) -> KairosDailySuggestionsResponse:
        if self.suggestion_count != len(self.suggestions):
            raise ValueError("suggestion_count must match suggestions.")
        if (
            self.evaluated_match_count + self.skipped_unsafe_match_count
            > 16
        ):
            raise ValueError("Daily evaluation bound exceeded.")
        return self


__all__ = [
    "KairosAnalysisResponse",
    "KairosDailySuggestionsResponse",
    "KairosDataFreshness",
    "KairosFeatureAvailability",
    "KairosFeatureDefinition",
    "KairosMethodologyResponse",
    "KairosMarketProbabilities",
    "KairosProbabilities",
    "KairosProvenance",
    "KairosReason",
    "KairosTeamSummary",
    "KairosSuggestion",
    "KairosSuggestionReason",
    "KairosWarning",
]
