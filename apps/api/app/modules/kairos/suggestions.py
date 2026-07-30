from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Final

from app.modules.kairos.schemas import (
    KairosMarketProbabilities,
    KairosReason,
    KairosSuggestion,
    KairosSuggestionReason,
    KairosWarning,
)

SUGGESTION_VERSION: Final = "kairos_daily_suggestions_v1"
MINIMUM_SUGGESTION_SCORE: Final = 40.0
TECHNICAL_CONFIDENCE_CAP: Final = 65.0


@dataclass(frozen=True, slots=True)
class _Candidate:
    label: str
    code: str
    probability: float
    no_information_probability: float

    @property
    def signal_strength(self) -> float:
        denominator = 1.0 - self.no_information_probability
        return max(
            0.0,
            min(
                1.0,
                (self.probability - self.no_information_probability)
                / denominator,
            ),
        )


def build_kairos_suggestion(
    *,
    provider_match_id: int,
    kickoff_at: datetime,
    home_team_name: str,
    away_team_name: str,
    market_probabilities: KairosMarketProbabilities | None,
    confidence_score: float,
    data_quality_score: float,
    freshness_status: str,
    analysis_reasons: list[KairosReason],
    analysis_warnings: list[KairosWarning],
    feature_snapshot_hash: str,
    competition_name: str | None = None,
) -> KairosSuggestion:
    blocking_codes = sorted(
        warning.code
        for warning in analysis_warnings
        if warning.severity == "blocking"
        or warning.code == "STALE_TARGET_DATA"
    )
    hard_blocked = (
        market_probabilities is None
        or freshness_status != "fresh"
        or bool(blocking_codes)
    )

    candidate = (
        _best_candidate(market_probabilities)
        if market_probabilities is not None
        else None
    )
    normalized_reliability = (
        max(0.0, min(confidence_score / TECHNICAL_CONFIDENCE_CAP, 1.0))
        * 100.0
    )
    candidate_score = (
        candidate.signal_strength * 100.0 if candidate is not None else 0.0
    )
    # Conservative conjunction: no learned or arbitrary blending coefficient is
    # introduced. The least reliable component caps the published score.
    kairos_score = round(
        min(data_quality_score, normalized_reliability, candidate_score),
        1,
    )
    below_gate = (
        candidate is None
        or candidate.signal_strength <= 0
        or kairos_score < MINIMUM_SUGGESTION_SCORE
    )
    no_bet = hard_blocked or below_gate

    if no_bet:
        recommendation = "NO_BET"
        recommendation_code = "NO_BET"
    else:
        assert candidate is not None
        recommendation = candidate.label
        recommendation_code = candidate.code

    reasons = _suggestion_reasons(
        candidate=candidate,
        no_bet=no_bet,
        hard_blocked=hard_blocked,
        kairos_score=kairos_score,
        data_quality_score=data_quality_score,
        normalized_reliability=normalized_reliability,
        analysis_reasons=analysis_reasons,
        analysis_warnings=analysis_warnings,
        blocking_codes=blocking_codes,
    )
    decision_payload = {
        "suggestion_version": SUGGESTION_VERSION,
        "provider_match_id": provider_match_id,
        "kickoff_at": kickoff_at.isoformat(),
        "recommendation": recommendation,
        "recommendation_code": recommendation_code,
        "kairos_score": kairos_score,
        "feature_snapshot_hash": feature_snapshot_hash,
        "reasons": [reason.model_dump(mode="json") for reason in reasons],
    }
    decision_hash = sha256(
        json.dumps(
            decision_payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    return KairosSuggestion(
        provider_match_id=provider_match_id,
        kickoff_at=kickoff_at,
        home_team_name=home_team_name,
        away_team_name=away_team_name,
        competition_name=competition_name,
        recommendation=recommendation,
        recommendation_code=recommendation_code,
        kairos_score=kairos_score,
        confidence_level=_confidence_level(
            confidence_score,
            hard_blocked,
        ),
        risk_level=_risk_level(no_bet),
        no_bet=no_bet,
        reasons=reasons,
        market_probabilities=market_probabilities,
        data_quality_score=round(data_quality_score, 1),
        technical_confidence_score=round(confidence_score, 1),
        feature_snapshot_hash=feature_snapshot_hash,
        decision_hash=decision_hash,
        analysis_path=(
            f"/api/v1/kairos/matches/{provider_match_id}/analysis"
        ),
    )


def _best_candidate(
    probabilities: KairosMarketProbabilities,
) -> _Candidate:
    # The reference probabilities are maximum-entropy baselines: 1/3 for one
    # outcome among three, 2/3 for two outcomes, and 1/2 for binary markets.
    # The declared order is only a deterministic tie-breaker.
    candidates = (
        _Candidate("Home Win", "HOME_WIN", probabilities.home_win, 1 / 3),
        _Candidate("Away Win", "AWAY_WIN", probabilities.away_win, 1 / 3),
        _Candidate("Draw", "DRAW", probabilities.draw, 1 / 3),
        _Candidate(
            "Double Chance",
            "HOME_OR_DRAW",
            probabilities.home_or_draw,
            2 / 3,
        ),
        _Candidate(
            "Double Chance",
            "AWAY_OR_DRAW",
            probabilities.away_or_draw,
            2 / 3,
        ),
        _Candidate(
            "Double Chance",
            "HOME_OR_AWAY",
            probabilities.home_or_away,
            2 / 3,
        ),
        _Candidate("Over 2.5", "OVER_2_5", probabilities.over_2_5, 0.5),
        _Candidate("Under 2.5", "UNDER_2_5", probabilities.under_2_5, 0.5),
        _Candidate("BTTS", "BTTS", probabilities.btts, 0.5),
    )
    return max(
        enumerate(candidates),
        key=lambda item: (item[1].signal_strength, -item[0]),
    )[1]


def _suggestion_reasons(
    *,
    candidate: _Candidate | None,
    no_bet: bool,
    hard_blocked: bool,
    kairos_score: float,
    data_quality_score: float,
    normalized_reliability: float,
    analysis_reasons: list[KairosReason],
    analysis_warnings: list[KairosWarning],
    blocking_codes: list[str],
) -> list[KairosSuggestionReason]:
    reasons: list[KairosSuggestionReason] = []
    if candidate is not None:
        reasons.append(
            KairosSuggestionReason(
                code="NORMALIZED_MARKET_SIGNAL",
                message=(
                    f"Signal analytique {candidate.probability * 100:.1f}% "
                    "comparé à sa référence sans information "
                    f"({candidate.no_information_probability * 100:.1f}%)."
                ),
                impact="neutral" if no_bet else "positive",
                category="analytical",
            )
        )
    reasons.extend(
        (
            KairosSuggestionReason(
                code="DATA_QUALITY_LIMIT",
                message=(
                    f"Qualité des données disponible: "
                    f"{data_quality_score:.1f}/100."
                ),
                impact=(
                    "positive"
                    if data_quality_score >= MINIMUM_SUGGESTION_SCORE
                    else "negative"
                ),
                category="analytical",
            ),
            KairosSuggestionReason(
                code="TECHNICAL_RELIABILITY_LIMIT",
                message=(
                    "Confiance technique normalisée par le plafond B2.1: "
                    f"{normalized_reliability:.1f}/100."
                ),
                impact=(
                    "positive"
                    if normalized_reliability >= MINIMUM_SUGGESTION_SCORE
                    else "negative"
                ),
                category="analytical",
            ),
        )
    )
    if hard_blocked:
        reasons.append(
            KairosSuggestionReason(
                code="NO_BET_HARD_BLOCK",
                message=(
                    "Suggestion bloquée par fraîcheur, disponibilité ou "
                    "intégrité des données"
                    + (
                        f" ({', '.join(blocking_codes)})."
                        if blocking_codes
                        else "."
                    )
                ),
                impact="negative",
                category="guardrail",
                critical=True,
            )
        )
    elif no_bet:
        reasons.append(
            KairosSuggestionReason(
                code="NO_BET_SCORE_GATE",
                message=(
                    f"Score Kairos {kairos_score:.1f}/100 inférieur au "
                    f"seuil documenté de {MINIMUM_SUGGESTION_SCORE:.0f}."
                ),
                impact="negative",
                category="guardrail",
                critical=True,
            )
        )

    for reason in analysis_reasons[:5]:
        reasons.append(
            KairosSuggestionReason(
                code=reason.code,
                message=reason.message,
                impact=_factor_impact(reason.direction, candidate, no_bet),
                category="analytical",
            )
        )
    for warning in analysis_warnings:
        if warning.severity == "info":
            continue
        reasons.append(
            KairosSuggestionReason(
                code=warning.code,
                message=warning.message,
                impact="negative",
                category="guardrail",
                critical=(
                    warning.severity == "blocking"
                    or warning.code == "STALE_TARGET_DATA"
                ),
            )
        )
    critical_guardrails = [reason for reason in reasons if reason.critical]
    remaining_reasons = [reason for reason in reasons if not reason.critical]
    return [*critical_guardrails, *remaining_reasons][:12]


def _factor_impact(
    direction: str,
    candidate: _Candidate | None,
    no_bet: bool,
) -> str:
    if no_bet or candidate is None or direction == "neutral":
        return "neutral"
    favorable = {
        "HOME_WIN": {"home"},
        "AWAY_WIN": {"away"},
        "DRAW": {"draw"},
        "HOME_OR_DRAW": {"home", "draw"},
        "AWAY_OR_DRAW": {"away", "draw"},
        "HOME_OR_AWAY": {"home", "away"},
    }.get(candidate.code)
    if favorable is None:
        return "neutral"
    return "positive" if direction in favorable else "negative"


def _confidence_level(
    technical_confidence_score: float,
    hard_blocked: bool,
) -> str:
    if hard_blocked:
        return "blocked"
    if technical_confidence_score < 40:
        return "low"
    if technical_confidence_score < 70:
        return "medium"
    return "high"


def _risk_level(no_bet: bool) -> str:
    if no_bet:
        return "high"
    # B2.2 is explicitly uncalibrated, so it never claims a low/guarded risk.
    return "elevated"


__all__ = [
    "MINIMUM_SUGGESTION_SCORE",
    "SUGGESTION_VERSION",
    "build_kairos_suggestion",
]
