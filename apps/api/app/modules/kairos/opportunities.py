from __future__ import annotations

from hashlib import sha256
import json

from app.modules.kairos.models import KairosMatchDataset
from app.modules.kairos.opportunity_config import (
    MAX_ALTERNATIVES_PER_MATCH,
    OPPORTUNITY_DATA_QUALITY_THRESHOLD,
    OPPORTUNITY_MARKET_GROUPS,
    OPPORTUNITY_PROBABILITY_THRESHOLD,
    OPPORTUNITY_TECHNICAL_CONFIDENCE_THRESHOLD,
)
from app.modules.kairos.schemas import (
    KairosAnalysisResponse,
    KairosHalfTimeMarketAnalysis,
    KairosMatchOpportunity,
    KairosMissingData,
    KairosOpportunityCandidate,
    KairosRejectionReason,
)
from app.modules.kairos.services import KairosAnalysisService

class KairosOpportunityService:
    def __init__(self, *, freshness_threshold_minutes: int) -> None:
        self.analysis_service = KairosAnalysisService(
            freshness_threshold_minutes=freshness_threshold_minutes
        )

    def analyze(self, dataset: KairosMatchDataset) -> KairosMatchOpportunity:
        analysis = self.analysis_service.analyze(dataset)
        candidates = [
            _half_time_candidate(market)
            for market in analysis.half_time_analysis
            if market.eligible_for_opportunity
        ]
        double_chance = _double_chance_candidate(analysis)
        if double_chance is not None:
            candidates.append(double_chance)
        candidates.sort(
            key=lambda candidate: (
                -candidate.estimated_probability,
                -candidate.data_quality_score,
                -candidate.technical_confidence_score,
                candidate.market,
            )
        )

        primary = candidates[0] if candidates else None
        alternatives: list[KairosOpportunityCandidate] = []
        if primary is not None:
            used_groups = {OPPORTUNITY_MARKET_GROUPS[primary.market]}
            for candidate in candidates[1:]:
                group = OPPORTUNITY_MARKET_GROUPS[candidate.market]
                if group in used_groups:
                    continue
                alternatives.append(candidate)
                used_groups.add(group)
                if len(alternatives) >= MAX_ALTERNATIVES_PER_MATCH:
                    break

        all_insufficient = all(
            market.insufficient_data for market in analysis.half_time_analysis
        )
        if primary is None:
            safety_decision = (
                "INSUFFICIENT_DATA" if all_insufficient else "NO_BET"
            )
            rejection_reasons = _rejection_reasons(analysis)
            if all_insufficient:
                section = "INSUFFICIENT_DATA"
            elif {
                "stale_data",
                "critical_guardrail",
            }.intersection(rejection_reasons):
                section = "NO_BET"
            else:
                section = "WATCH"
        else:
            safety_decision = "ANALYSIS_ALLOWED"
            section = _section(primary.market)
            rejection_reasons = []

        return KairosMatchOpportunity(
            provider_match_id=dataset.target.provider_match_id,
            kickoff_at=dataset.target.kickoff_at,
            home_team_name=dataset.target.home_team_name,
            away_team_name=dataset.target.away_team_name,
            competition_name=dataset.target.competition_name,
            section=section,
            safety_decision=safety_decision,
            primary_analysis=primary,
            alternative_analyses=alternatives,
            evaluated_markets=analysis.half_time_analysis,
            rejection_reasons=rejection_reasons,
            missing_data=_missing_data(dataset, analysis),
            data_freshness=analysis.data_freshness.status,
        )


def _half_time_candidate(
    market: KairosHalfTimeMarketAnalysis,
) -> KairosOpportunityCandidate:
    if (
        not market.eligible_for_opportunity
        or market.estimated_probability is None
    ):
        raise ValueError("Only eligible half-time analyses are candidates.")
    return KairosOpportunityCandidate(
        market=market.market,
        estimated_probability=market.estimated_probability,
        data_quality_score=market.data_quality_score,
        technical_confidence_score=market.technical_confidence_score,
        sample_size=market.sample_size,
        risk=market.risk,
        reasons=market.reasons,
        guardrails=market.guardrails,
        analysis_hash=market.analysis_hash,
    )


def _double_chance_candidate(analysis: object) -> KairosOpportunityCandidate | None:
    market_probabilities = getattr(analysis, "market_probabilities", None)
    suggestion = getattr(analysis, "analytical_suggestion", None)
    freshness = getattr(analysis, "data_freshness", None)
    if (
        market_probabilities is None
        or suggestion is None
        or freshness is None
        or suggestion.no_bet
        or freshness.status != "fresh"
        or analysis.data_quality_score < OPPORTUNITY_DATA_QUALITY_THRESHOLD
        or analysis.confidence_score
        < OPPORTUNITY_TECHNICAL_CONFIDENCE_THRESHOLD
    ):
        return None
    options = {
        "HOME_OR_DRAW": market_probabilities.home_or_draw,
        "AWAY_OR_DRAW": market_probabilities.away_or_draw,
        "HOME_OR_AWAY": market_probabilities.home_or_away,
    }
    market, probability = max(options.items(), key=lambda item: item[1])
    if probability < OPPORTUNITY_PROBABILITY_THRESHOLD:
        return None
    payload = {
        "feature_snapshot_hash": analysis.provenance.feature_snapshot_hash,
        "market": market,
        "model_version": analysis.model_version,
        "probability": probability,
    }
    analysis_hash = sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return KairosOpportunityCandidate(
        market=market,
        estimated_probability=probability,
        data_quality_score=analysis.data_quality_score,
        technical_confidence_score=analysis.confidence_score,
        sample_size=min(
            analysis.home_team.recent_result_sample_size,
            analysis.away_team.recent_result_sample_size,
        ),
        risk="elevated",
        reasons=[
            "Probabilité analytique dérivée de la baseline pré-match B2.2.",
            "Signal non calibré, sans cote, bookmaker ni automatisation.",
        ],
        guardrails=[],
        analysis_hash=analysis_hash,
    )


def _section(market: str) -> str:
    if market in {
        "FIRST_HALF_MORE_GOALS",
        "SECOND_HALF_MORE_GOALS",
        "EQUAL_HALF_GOALS",
    }:
        return "HALF_TIME"
    if market in {
        "FIRST_HALF_OVER_0_5",
        "SECOND_HALF_OVER_0_5",
        "SECOND_HALF_OVER_1_5",
    }:
        return "GOAL_MARKETS"
    return "DOUBLE_CHANCE"


def _rejection_reasons(
    analysis: KairosAnalysisResponse,
) -> list[KairosRejectionReason]:
    markets = analysis.half_time_analysis
    reasons: list[KairosRejectionReason] = []
    if markets and all(market.insufficient_data for market in markets):
        reasons.append("insufficient_half_time_data")
    if analysis.data_freshness.status == "stale" or any(
        "STALE_SOURCE_DATA" in market.guardrails for market in markets
    ):
        reasons.append("stale_data")
    if markets and max(
        market.data_quality_score for market in markets
    ) < OPPORTUNITY_DATA_QUALITY_THRESHOLD:
        reasons.append("low_data_quality")
    if markets and max(
        market.technical_confidence_score for market in markets
    ) < OPPORTUNITY_TECHNICAL_CONFIDENCE_THRESHOLD:
        reasons.append("low_technical_confidence")
    probabilities = [
        market.estimated_probability
        for market in markets
        if market.estimated_probability is not None
    ]
    if probabilities and max(probabilities) < OPPORTUNITY_PROBABILITY_THRESHOLD:
        reasons.append("estimated_probability_below_threshold")
    if any(
        warning.severity == "blocking" for warning in analysis.warnings
    ) or any(
        guardrail != "STALE_SOURCE_DATA"
        for market in markets
        for guardrail in market.guardrails
    ):
        reasons.append("critical_guardrail")
    if any(
        not availability.available_for_both_teams
        for availability in analysis.data_availability.values()
    ):
        reasons.append("provider_data_partial")
    if not reasons:
        reasons.append("critical_guardrail")
    return list(dict.fromkeys(reasons))


def _missing_data(
    dataset: KairosMatchDataset,
    analysis: KairosAnalysisResponse,
) -> list[KairosMissingData]:
    missing: list[KairosMissingData] = []
    if analysis.half_time_analysis and all(
        market.insufficient_data for market in analysis.half_time_analysis
    ):
        missing.append("half_time_scores")
    if not any(
        event.event_type.strip().lower() == "goal"
        for event in dataset.events
    ):
        missing.append("goal_events")
    if len(dataset.h2h_history) < 3:
        missing.append("h2h")
    if len(dataset.standings) < 2:
        missing.append("standings")
    if not dataset.statistics:
        missing.append("match_statistics")
    return missing


__all__ = ["KairosOpportunityService"]
