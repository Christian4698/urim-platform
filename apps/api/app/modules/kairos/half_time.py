from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
import math
from typing import Final, Literal

from app.modules.kairos.models import KairosMatchDataset, MatchObservation
from app.modules.kairos.opportunity_config import (
    HALF_TIME_CONFIDENCE_CAP,
    HALF_TIME_H2H_LIMIT,
    HALF_TIME_H2H_MAX_WEIGHT,
    HALF_TIME_H2H_MINIMUM_SAMPLE,
    HALF_TIME_MINIMUM_SAMPLE_PER_TEAM,
    HALF_TIME_QUALITY_CAP,
    HALF_TIME_RECENT_WINDOW,
    OPPORTUNITY_DATA_QUALITY_THRESHOLD,
    OPPORTUNITY_PROBABILITY_THRESHOLD,
    OPPORTUNITY_TECHNICAL_CONFIDENCE_THRESHOLD,
)
from app.modules.kairos.schemas import KairosHalfTimeMarketAnalysis


HALF_TIME_MODEL_VERSION: Final = "kairos_half_time_b2_4_v1"
HalfTimeMarket = Literal[
    "FIRST_HALF_MORE_GOALS",
    "SECOND_HALF_MORE_GOALS",
    "EQUAL_HALF_GOALS",
    "FIRST_HALF_OVER_0_5",
    "SECOND_HALF_OVER_0_5",
    "SECOND_HALF_OVER_1_5",
]
HALF_TIME_MARKETS: Final[tuple[HalfTimeMarket, ...]] = (
    "FIRST_HALF_MORE_GOALS",
    "SECOND_HALF_MORE_GOALS",
    "EQUAL_HALF_GOALS",
    "FIRST_HALF_OVER_0_5",
    "SECOND_HALF_OVER_0_5",
    "SECOND_HALF_OVER_1_5",
)


@dataclass(frozen=True, slots=True)
class _HalfSample:
    provider_match_id: int
    first_half_goals: int
    second_half_goals: int


def analyze_half_time_markets(
    dataset: KairosMatchDataset,
    *,
    freshness_threshold_minutes: int,
) -> tuple[KairosHalfTimeMarketAnalysis, ...]:
    dataset.validate_temporal_integrity()
    dataset.validate_data_integrity()
    if freshness_threshold_minutes <= 0:
        raise ValueError("freshness_threshold_minutes must be positive.")

    home_samples = _samples(dataset.home_history, HALF_TIME_RECENT_WINDOW)
    away_samples = _samples(dataset.away_history, HALF_TIME_RECENT_WINDOW)
    merged_samples = _deduplicate((*home_samples, *away_samples))
    h2h_samples = _samples(
        dataset.h2h_history,
        HALF_TIME_H2H_LIMIT,
    )
    required_history_available = (
        len(home_samples) >= HALF_TIME_MINIMUM_SAMPLE_PER_TEAM
        and len(away_samples) >= HALF_TIME_MINIMUM_SAMPLE_PER_TEAM
    )
    stale = _is_stale(
        dataset,
        freshness_threshold_minutes=freshness_threshold_minutes,
    )
    goal_event_match_count = len(
        {
            event.provider_match_id
            for event in dataset.events
            if event.event_type.strip().lower() == "goal"
            and event.elapsed is not None
            and event.elapsed >= 0
        }
    )
    quality = _quality_score(
        home_count=len(home_samples),
        away_count=len(away_samples),
        h2h_count=len(h2h_samples),
        standings_count=len(dataset.standings),
        goal_event_match_count=goal_event_match_count,
        stale=stale,
    )
    confidence = _technical_confidence(
        sample_count=len(merged_samples),
        home_count=len(home_samples),
        away_count=len(away_samples),
        h2h_count=len(h2h_samples),
        stale=stale,
    )

    if not required_history_available or not merged_samples:
        reason = (
            "Au moins trois matchs avec scores HT et FT sont requis par "
            "équipe; les valeurs manquantes ne sont jamais assimilées à zéro."
        )
        return tuple(
            _analysis(
                dataset=dataset,
                market=market,
                probability=None,
                quality=quality,
                confidence=0.0,
                sample_size=len(merged_samples),
                h2h_sample_size=len(h2h_samples),
                insufficient_data=True,
                reasons=(reason,),
                guardrails=("INSUFFICIENT_HALF_TIME_HISTORY",),
            )
            for market in HALF_TIME_MARKETS
        )

    base_probabilities = _probabilities(merged_samples)
    h2h_probabilities = (
        _probabilities(h2h_samples)
        if len(h2h_samples) >= HALF_TIME_H2H_MINIMUM_SAMPLE
        else None
    )
    reasons = [
        (
            f"{len(merged_samples)} matchs récents complets HT/FT analysés "
            "sans imputation."
        )
    ]
    if h2h_probabilities is None:
        reasons.append(
            "H2H insuffisant ou absent: aucune influence H2H appliquée."
        )
    else:
        reasons.append(
            "H2H récent utilisé comme signal secondaire plafonné à 10 %."
        )
    if goal_event_match_count:
        reasons.append(
            "Des événements de but minutés renforcent le contrôle de qualité."
        )
    else:
        reasons.append(
            "Minutes de buts indisponibles: le calcul repose sur les scores HT/FT."
        )

    analyses = []
    for market in HALF_TIME_MARKETS:
        probability = base_probabilities[market]
        if h2h_probabilities is not None:
            probability = (
                probability * (1.0 - HALF_TIME_H2H_MAX_WEIGHT)
                + h2h_probabilities[market] * HALF_TIME_H2H_MAX_WEIGHT
            )
        guardrails: list[str] = []
        if stale:
            guardrails.append("STALE_SOURCE_DATA")
        analyses.append(
            _analysis(
                dataset=dataset,
                market=market,
                probability=round(probability, 6),
                quality=quality,
                confidence=confidence,
                sample_size=len(merged_samples),
                h2h_sample_size=len(h2h_samples),
                insufficient_data=False,
                reasons=tuple(reasons),
                guardrails=tuple(guardrails),
            )
        )
    return tuple(analyses)


def _samples(
    history: tuple[MatchObservation, ...],
    limit: int,
) -> tuple[_HalfSample, ...]:
    result: list[_HalfSample] = []
    seen: set[int] = set()
    for match in history:
        if match.provider_match_id in seen:
            continue
        totals = match.half_goal_totals()
        if totals is None:
            continue
        seen.add(match.provider_match_id)
        result.append(
            _HalfSample(
                provider_match_id=match.provider_match_id,
                first_half_goals=totals[0],
                second_half_goals=totals[1],
            )
        )
        if len(result) >= limit:
            break
    return tuple(result)


def _deduplicate(samples: tuple[_HalfSample, ...]) -> tuple[_HalfSample, ...]:
    return tuple(
        {sample.provider_match_id: sample for sample in samples}.values()
    )


def _probabilities(
    samples: tuple[_HalfSample, ...],
) -> dict[HalfTimeMarket, float]:
    count = len(samples)
    comparison = Counter(
        "first"
        if sample.first_half_goals > sample.second_half_goals
        else "second"
        if sample.second_half_goals > sample.first_half_goals
        else "equal"
        for sample in samples
    )
    return {
        "FIRST_HALF_MORE_GOALS": (comparison["first"] + 1) / (count + 3),
        "SECOND_HALF_MORE_GOALS": (comparison["second"] + 1) / (count + 3),
        "EQUAL_HALF_GOALS": (comparison["equal"] + 1) / (count + 3),
        "FIRST_HALF_OVER_0_5": (
            sum(sample.first_half_goals >= 1 for sample in samples) + 1
        )
        / (count + 2),
        "SECOND_HALF_OVER_0_5": (
            sum(sample.second_half_goals >= 1 for sample in samples) + 1
        )
        / (count + 2),
        "SECOND_HALF_OVER_1_5": (
            sum(sample.second_half_goals >= 2 for sample in samples) + 1
        )
        / (count + 2),
    }


def _quality_score(
    *,
    home_count: int,
    away_count: int,
    h2h_count: int,
    standings_count: int,
    goal_event_match_count: int,
    stale: bool,
) -> float:
    history_coverage = (
        min(home_count / HALF_TIME_RECENT_WINDOW, 1.0)
        + min(away_count / HALF_TIME_RECENT_WINDOW, 1.0)
    ) / 2
    score = 25.0 + history_coverage * 45.0
    score += min(standings_count, 2) * 2.5
    score += min(goal_event_match_count, 5)
    if h2h_count >= HALF_TIME_H2H_MINIMUM_SAMPLE:
        score += 5.0
    if stale:
        score -= 20.0
    return round(max(0.0, min(score, HALF_TIME_QUALITY_CAP)), 1)


def _technical_confidence(
    *,
    sample_count: int,
    home_count: int,
    away_count: int,
    h2h_count: int,
    stale: bool,
) -> float:
    balance = min(home_count, away_count) / max(home_count, away_count, 1)
    score = 30.0 + min(sample_count / 10, 1.0) * 25.0 + balance * 5.0
    if h2h_count >= HALF_TIME_H2H_MINIMUM_SAMPLE:
        score += 5.0
    if stale:
        score -= 15.0
    return round(max(0.0, min(score, HALF_TIME_CONFIDENCE_CAP)), 1)


def _is_stale(
    dataset: KairosMatchDataset,
    *,
    freshness_threshold_minutes: int,
) -> bool:
    target_age_minutes = (
        dataset.as_of - dataset.target.source.fetched_at
    ).total_seconds() / 60
    return (
        dataset.target.source.freshness_status != "fresh"
        or target_age_minutes > freshness_threshold_minutes
    )


def _analysis(
    *,
    dataset: KairosMatchDataset,
    market: HalfTimeMarket,
    probability: float | None,
    quality: float,
    confidence: float,
    sample_size: int,
    h2h_sample_size: int,
    insufficient_data: bool,
    reasons: tuple[str, ...],
    guardrails: tuple[str, ...],
) -> KairosHalfTimeMarketAnalysis:
    eligible = (
        probability is not None
        and math.isfinite(probability)
        and probability >= OPPORTUNITY_PROBABILITY_THRESHOLD
        and quality >= OPPORTUNITY_DATA_QUALITY_THRESHOLD
        and confidence >= OPPORTUNITY_TECHNICAL_CONFIDENCE_THRESHOLD
        and not guardrails
        and not insufficient_data
    )
    risk = (
        "guarded"
        if eligible and probability is not None and probability >= 0.78
        else "elevated"
        if eligible
        else "high"
    )
    fingerprint = {
        "as_of": dataset.as_of.isoformat(),
        "market": market,
        "model_version": HALF_TIME_MODEL_VERSION,
        "probability": probability,
        "quality": quality,
        "confidence": confidence,
        "sample_size": sample_size,
        "h2h_sample_size": h2h_sample_size,
        "source_hashes": sorted(
            source.raw_hash for source in dataset.source_observations()
        ),
    }
    analysis_hash = sha256(
        json.dumps(
            fingerprint,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    return KairosHalfTimeMarketAnalysis(
        model_version=HALF_TIME_MODEL_VERSION,
        market=market,
        estimated_probability=probability,
        data_quality_score=quality,
        technical_confidence_score=confidence,
        sample_size=sample_size,
        h2h_sample_size=h2h_sample_size,
        risk=risk,
        reasons=list(reasons),
        guardrails=list(guardrails),
        eligible_for_opportunity=eligible,
        insufficient_data=insufficient_data,
        analysis_hash=analysis_hash,
    )


__all__ = [
    "HALF_TIME_MARKETS",
    "HALF_TIME_MODEL_VERSION",
    "analyze_half_time_markets",
]
