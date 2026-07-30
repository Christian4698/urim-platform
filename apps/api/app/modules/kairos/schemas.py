from __future__ import annotations

from datetime import date, datetime
import math
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.kairos.opportunity_config import (
    HALF_TIME_CONFIDENCE_CAP,
    HALF_TIME_H2H_LIMIT,
    HALF_TIME_QUALITY_CAP,
    HALF_TIME_RECENT_WINDOW,
    MAX_DAILY_OPPORTUNITIES,
    OPPORTUNITY_DATA_QUALITY_THRESHOLD,
    OPPORTUNITY_MARKET_GROUPS,
    OPPORTUNITY_PROBABILITY_THRESHOLD,
    OPPORTUNITY_TECHNICAL_CONFIDENCE_THRESHOLD,
)


Sha256Hex = Annotated[
    str,
    Field(pattern=r"^[0-9a-fA-F]{64}$"),
]

KairosRejectionReason = Literal[
    "insufficient_half_time_data",
    "low_data_quality",
    "low_technical_confidence",
    "estimated_probability_below_threshold",
    "stale_data",
    "critical_guardrail",
    "correlated_market_excluded",
    "provider_data_partial",
]
KairosMissingData = Literal[
    "half_time_scores",
    "goal_events",
    "h2h",
    "standings",
    "match_statistics",
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
    half_time_analysis: list[KairosHalfTimeMarketAnalysis] = Field(
        default_factory=list,
        max_length=6,
    )
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


class KairosHalfTimeMarketAnalysis(BaseModel):
    model_version: Literal["kairos_half_time_b2_4_v1"] = (
        "kairos_half_time_b2_4_v1"
    )
    market: Literal[
        "FIRST_HALF_MORE_GOALS",
        "SECOND_HALF_MORE_GOALS",
        "EQUAL_HALF_GOALS",
        "FIRST_HALF_OVER_0_5",
        "SECOND_HALF_OVER_0_5",
        "SECOND_HALF_OVER_1_5",
    ]
    estimated_probability: float | None = Field(default=None, ge=0, le=1)
    data_quality_score: float = Field(ge=0, le=HALF_TIME_QUALITY_CAP)
    technical_confidence_score: float = Field(
        ge=0,
        le=HALF_TIME_CONFIDENCE_CAP,
    )
    sample_size: int = Field(ge=0, le=HALF_TIME_RECENT_WINDOW * 2)
    h2h_sample_size: int = Field(ge=0, le=HALF_TIME_H2H_LIMIT)
    risk: Literal["high", "elevated", "guarded"]
    reasons: list[str] = Field(min_length=1, max_length=6)
    guardrails: list[str] = Field(max_length=6)
    eligible_for_opportunity: bool
    insufficient_data: bool
    analysis_hash: Sha256Hex

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_half_time_gate(self) -> KairosHalfTimeMarketAnalysis:
        if self.insufficient_data and self.estimated_probability is not None:
            raise ValueError("Insufficient data cannot expose a probability.")
        if self.eligible_for_opportunity and (
            self.insufficient_data
            or self.estimated_probability is None
            or self.estimated_probability
            < OPPORTUNITY_PROBABILITY_THRESHOLD
            or self.data_quality_score
            < OPPORTUNITY_DATA_QUALITY_THRESHOLD
            or self.technical_confidence_score
            < OPPORTUNITY_TECHNICAL_CONFIDENCE_THRESHOLD
            or self.guardrails
        ):
            raise ValueError("Opportunity thresholds are not satisfied.")
        return self


class KairosOpportunityCandidate(BaseModel):
    market: Literal[
        "FIRST_HALF_MORE_GOALS",
        "SECOND_HALF_MORE_GOALS",
        "EQUAL_HALF_GOALS",
        "FIRST_HALF_OVER_0_5",
        "SECOND_HALF_OVER_0_5",
        "SECOND_HALF_OVER_1_5",
        "HOME_OR_DRAW",
        "AWAY_OR_DRAW",
        "HOME_OR_AWAY",
    ]
    estimated_probability: float = Field(ge=0, le=1)
    data_quality_score: float = Field(ge=0, le=100)
    technical_confidence_score: float = Field(
        ge=0,
        le=HALF_TIME_CONFIDENCE_CAP,
    )
    sample_size: int = Field(ge=0, le=50)
    risk: Literal["high", "elevated", "guarded"]
    reasons: list[str] = Field(min_length=1, max_length=6)
    guardrails: list[str] = Field(max_length=6)
    eligible_for_opportunity: Literal[True] = True
    analysis_hash: Sha256Hex

    model_config = ConfigDict(extra="forbid")


class KairosMatchOpportunity(BaseModel):
    provider_match_id: int = Field(gt=0)
    kickoff_at: datetime
    home_team_name: str = Field(min_length=1, max_length=200)
    away_team_name: str = Field(min_length=1, max_length=200)
    section: Literal[
        "ABOVE_70",
        "HALF_TIME",
        "GOAL_MARKETS",
        "DOUBLE_CHANCE",
        "WATCH",
        "NO_BET",
        "INSUFFICIENT_DATA",
    ]
    safety_decision: Literal[
        "ANALYSIS_ALLOWED",
        "NO_BET",
        "INSUFFICIENT_DATA",
    ]
    primary_analysis: KairosOpportunityCandidate | None
    alternative_analyses: list[KairosOpportunityCandidate] = Field(
        max_length=2
    )
    evaluated_markets: list[KairosHalfTimeMarketAnalysis] = Field(
        max_length=6
    )
    rejection_reasons: list[KairosRejectionReason] = Field(
        default_factory=list,
        max_length=8,
    )
    missing_data: list[KairosMissingData] = Field(
        default_factory=list,
        max_length=5,
    )
    data_freshness: Literal["fresh", "stale"] = "fresh"
    read_only: Literal[True] = True
    persisted_by_request: Literal[False] = False
    not_for_betting: Literal[True] = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_primary_contract(self) -> KairosMatchOpportunity:
        if self.safety_decision == "ANALYSIS_ALLOWED":
            if self.primary_analysis is None:
                raise ValueError("Allowed analysis requires one primary.")
        elif self.primary_analysis is not None or self.alternative_analyses:
            raise ValueError("Blocked analysis cannot expose selections.")
        if self.safety_decision == "ANALYSIS_ALLOWED":
            if self.rejection_reasons:
                raise ValueError("Allowed analysis cannot expose rejections.")
        elif not self.rejection_reasons:
            raise ValueError("Blocked analysis requires a safe rejection reason.")
        if (
            self.safety_decision == "INSUFFICIENT_DATA"
            and self.section != "INSUFFICIENT_DATA"
        ):
            raise ValueError(
                "Insufficient data must use its dedicated section."
            )
        primary_market = (
            self.primary_analysis.market if self.primary_analysis else None
        )
        alternative_markets = [
            candidate.market for candidate in self.alternative_analyses
        ]
        if primary_market in alternative_markets:
            raise ValueError("Primary cannot be duplicated as an alternative.")
        if len(alternative_markets) != len(set(alternative_markets)):
            raise ValueError("Alternatives must be distinct.")
        selection_markets = (
            [primary_market] if primary_market is not None else []
        )
        selection_markets.extend(alternative_markets)
        selection_groups = [
            OPPORTUNITY_MARKET_GROUPS[market]
            for market in selection_markets
        ]
        if len(selection_groups) != len(set(selection_groups)):
            raise ValueError(
                "Correlated markets cannot be selected together."
            )
        return self


class KairosOpportunityDataFreshness(BaseModel):
    status: Literal["fresh", "stale", "partial", "missing"]
    fresh_match_count: int = Field(ge=0, le=16)
    stale_match_count: int = Field(ge=0, le=16)
    partial_match_count: int = Field(ge=0, le=16)

    model_config = ConfigDict(extra="forbid")


class KairosResolvedJournalMetric(BaseModel):
    resolved_sample_size: int = Field(ge=1)
    success_count: int = Field(ge=0)
    observed_hit_rate: float = Field(ge=0, le=1)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_resolved_metric(self) -> KairosResolvedJournalMetric:
        if self.success_count > self.resolved_sample_size:
            raise ValueError("Success count exceeds resolved sample.")
        expected = self.success_count / self.resolved_sample_size
        if abs(self.observed_hit_rate - expected) > 0.0001:
            raise ValueError("Observed rate is inconsistent with counts.")
        return self


class KairosDailyOpportunitiesResponse(BaseModel):
    local_date: date
    timezone: Literal["Africa/Kinshasa"] = "Africa/Kinshasa"
    as_of: datetime
    generated_at: datetime
    opportunity_count: int = Field(
        ge=0,
        le=MAX_DAILY_OPPORTUNITIES,
    )
    evaluated_match_count: int = Field(ge=0, le=16)
    skipped_unsafe_match_count: int = Field(ge=0, le=16)
    watchlist_count: int = Field(ge=0, le=16)
    no_bet_count: int = Field(ge=0, le=16)
    insufficient_data_count: int = Field(ge=0, le=16)
    stale_data_count: int = Field(ge=0, le=16)
    rejection_reason_counts: dict[KairosRejectionReason, int]
    message_code: Literal[
        "opportunities_available",
        "no_solid_opportunity",
        "insufficient_data",
        "partial_sync",
    ]
    message: str = Field(min_length=1, max_length=280)
    data_freshness: KairosOpportunityDataFreshness
    opportunities: list[KairosMatchOpportunity] = Field(
        max_length=MAX_DAILY_OPPORTUNITIES
    )
    evaluated_matches: list[KairosMatchOpportunity] = Field(max_length=16)
    warnings: list[str] = Field(max_length=6)
    thresholds: dict[str, float]
    calibration_status: Literal["not_calibrated"] = "not_calibrated"
    resolved_journal_sample_size: int = Field(default=0, ge=0)
    observed_hit_rate: float | None = Field(default=None, ge=0, le=1)
    resolved_metrics_by_market: dict[
        str,
        KairosResolvedJournalMetric,
    ] = Field(default_factory=dict)
    read_only: Literal[True] = True
    db_writes: Literal[False] = False
    provider_calls: Literal[False] = False
    automatic_betting_enabled: Literal[False] = False
    live_automatic_enabled: Literal[False] = False
    not_for_betting: Literal[True] = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_opportunity_count(self) -> KairosDailyOpportunitiesResponse:
        if self.opportunity_count != len(self.opportunities):
            raise ValueError("opportunity_count must match opportunities.")
        if self.evaluated_match_count != len(self.evaluated_matches):
            raise ValueError(
                "evaluated_match_count must match evaluated_matches."
            )
        if any(
            item.safety_decision != "ANALYSIS_ALLOWED"
            for item in self.opportunities
        ):
            raise ValueError("Opportunities must contain allowed analyses only.")
        if (
            self.opportunity_count
            + self.watchlist_count
            + self.no_bet_count
            + self.insufficient_data_count
            != self.evaluated_match_count
        ):
            raise ValueError("Daily opportunity categories are inconsistent.")
        if (
            self.evaluated_match_count + self.skipped_unsafe_match_count
            > 16
        ):
            raise ValueError("Daily opportunity evaluation bound exceeded.")
        if self.observed_hit_rate is not None and self.resolved_journal_sample_size == 0:
            raise ValueError("Observed rate requires resolved observations.")
        return self


class KairosPerformanceSegment(BaseModel):
    key: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=1, max_length=160)
    total_snapshots: int = Field(ge=0)
    resolved_sample_size: int = Field(ge=0)
    success_count: int = Field(ge=0)
    void_count: int = Field(ge=0)
    unresolved_count: int = Field(ge=0)
    observed_hit_rate: float | None = Field(default=None, ge=0, le=1)
    estimated_probability_mean: float | None = Field(
        default=None,
        ge=0,
        le=1,
    )
    sample_status: Literal[
        "no_sample",
        "insufficient_sample",
        "descriptive_sample_available",
    ]

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_performance_segment(self) -> KairosPerformanceSegment:
        if self.success_count > self.resolved_sample_size:
            raise ValueError("Success count exceeds resolved sample.")
        if (
            self.resolved_sample_size
            + self.void_count
            + self.unresolved_count
            != self.total_snapshots
        ):
            raise ValueError("Performance segment counts are inconsistent.")
        if self.resolved_sample_size == 0:
            if self.observed_hit_rate is not None:
                raise ValueError("An empty segment cannot expose a hit rate.")
            if self.sample_status != "no_sample":
                raise ValueError("An empty segment must report no_sample.")
        else:
            expected = self.success_count / self.resolved_sample_size
            if (
                self.observed_hit_rate is None
                or abs(self.observed_hit_rate - expected) > 0.0001
            ):
                raise ValueError("Observed rate is inconsistent with counts.")
        return self


class KairosPerformanceResponse(BaseModel):
    generated_at: datetime
    total_snapshots: int = Field(ge=0)
    resolved: int = Field(ge=0)
    unresolved: int = Field(ge=0)
    void: int = Field(ge=0)
    resolved_sample_size: int = Field(ge=0)
    success_count: int = Field(ge=0)
    observed_hit_rate: float | None = Field(default=None, ge=0, le=1)
    sample_status: Literal[
        "no_sample",
        "insufficient_sample",
        "descriptive_sample_available",
    ]
    performance_by_market: list[KairosPerformanceSegment]
    performance_by_competition: list[KairosPerformanceSegment]
    performance_by_probability_band: list[KairosPerformanceSegment]
    performance_by_quality_level: list[KairosPerformanceSegment]
    calibration_buckets: list[KairosPerformanceSegment]
    last_resolution_at: datetime | None
    last_report_generated_at: datetime
    warnings: list[str] = Field(max_length=6)
    calibration_status: Literal["not_calibrated"] = "not_calibrated"
    read_only: Literal[True] = True
    db_writes: Literal[False] = False
    provider_calls: Literal[False] = False
    automatic_betting_enabled: Literal[False] = False
    not_for_betting: Literal[True] = True

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_performance_counts(self) -> KairosPerformanceResponse:
        if self.resolved != self.resolved_sample_size:
            raise ValueError("Resolved count and sample size must match.")
        if self.resolved + self.unresolved + self.void != self.total_snapshots:
            raise ValueError("Performance totals are inconsistent.")
        if self.success_count > self.resolved_sample_size:
            raise ValueError("Success count exceeds resolved sample.")
        if self.resolved_sample_size == 0:
            if self.observed_hit_rate is not None:
                raise ValueError("An empty report cannot expose a hit rate.")
            if self.sample_status != "no_sample":
                raise ValueError("An empty report must report no_sample.")
        else:
            expected = self.success_count / self.resolved_sample_size
            if (
                self.observed_hit_rate is None
                or abs(self.observed_hit_rate - expected) > 0.0001
            ):
                raise ValueError("Observed rate is inconsistent with counts.")
        return self


__all__ = [
    "KairosAnalysisResponse",
    "KairosDailyOpportunitiesResponse",
    "KairosDailySuggestionsResponse",
    "KairosDataFreshness",
    "KairosFeatureAvailability",
    "KairosFeatureDefinition",
    "KairosMethodologyResponse",
    "KairosHalfTimeMarketAnalysis",
    "KairosMatchOpportunity",
    "KairosMissingData",
    "KairosMarketProbabilities",
    "KairosOpportunityDataFreshness",
    "KairosPerformanceResponse",
    "KairosPerformanceSegment",
    "KairosProbabilities",
    "KairosProvenance",
    "KairosRejectionReason",
    "KairosResolvedJournalMetric",
    "KairosOpportunityCandidate",
    "KairosReason",
    "KairosTeamSummary",
    "KairosSuggestion",
    "KairosSuggestionReason",
    "KairosWarning",
]
