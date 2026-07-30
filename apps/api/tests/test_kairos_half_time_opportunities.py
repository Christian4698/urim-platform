from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest
from pydantic import ValidationError

from app.modules.kairos.half_time import analyze_half_time_markets
from app.modules.kairos.models import (
    EventObservation,
    KairosMatchDataset,
    MatchObservation,
    SourceObservation,
    StandingObservation,
)
from app.modules.kairos.opportunities import KairosOpportunityService
from app.modules.kairos.schemas import KairosMatchOpportunity


AS_OF = datetime(2026, 7, 28, 10, tzinfo=UTC)
HOME_TEAM_ID = 10
AWAY_TEAM_ID = 20


def _source(identity: str, *, stale: bool = False) -> SourceObservation:
    fetched_at = AS_OF - timedelta(hours=4 if stale else 1)
    return SourceObservation(
        observation_id=identity,
        provider="api-football",
        provider_event_id=identity,
        observed_at=fetched_at - timedelta(minutes=2),
        available_at=fetched_at - timedelta(minutes=1),
        fetched_at=fetched_at,
        created_at=fetched_at + timedelta(seconds=1),
        source_version="football-v3-test",
        quality_flags=("REAL_PROVIDER_DATA", "NORMALIZED"),
        raw_hash=sha256(identity.encode()).hexdigest(),
        freshness_status="stale" if stale else "fresh",
    )


def _match(
    match_id: int,
    *,
    team_id: int,
    opponent_id: int,
    kickoff_days_ago: int,
    halftime: tuple[int, int] | None = (1, 0),
    fulltime: tuple[int, int] = (1, 2),
) -> MatchObservation:
    return MatchObservation(
        source=_source(f"match:{match_id}"),
        provider_match_id=match_id,
        provider_competition_id=39,
        season=2026,
        kickoff_at=AS_OF - timedelta(days=kickoff_days_ago),
        status_short="FT",
        home_team_provider_id=team_id,
        home_team_name=f"Team {team_id}",
        away_team_provider_id=opponent_id,
        away_team_name=f"Team {opponent_id}",
        goals_home=fulltime[0],
        goals_away=fulltime[1],
        score_fulltime_home=fulltime[0],
        score_fulltime_away=fulltime[1],
        score_halftime_home=halftime[0] if halftime else None,
        score_halftime_away=halftime[1] if halftime else None,
    )


def _dataset(
    *,
    missing_halftime: bool = False,
    stale_target: bool = False,
) -> KairosMatchDataset:
    target = MatchObservation(
        source=_source("match:999", stale=stale_target),
        provider_match_id=999,
        provider_competition_id=39,
        season=2026,
        kickoff_at=AS_OF + timedelta(hours=8),
        status_short="NS",
        home_team_provider_id=HOME_TEAM_ID,
        home_team_name="Home FC",
        away_team_provider_id=AWAY_TEAM_ID,
        away_team_name="Away FC",
        goals_home=None,
        goals_away=None,
        score_fulltime_home=None,
        score_fulltime_away=None,
    )
    halftime = None if missing_halftime else (1, 0)
    home_history = tuple(
        _match(
            100 + index,
            team_id=HOME_TEAM_ID,
            opponent_id=1000 + index,
            kickoff_days_ago=index + 1,
            halftime=halftime,
        )
        for index in range(5)
    )
    away_history = tuple(
        _match(
            200 + index,
            team_id=AWAY_TEAM_ID,
            opponent_id=2000 + index,
            kickoff_days_ago=index + 1,
            halftime=halftime,
        )
        for index in range(5)
    )
    h2h_history = tuple(
        _match(
            300 + index,
            team_id=HOME_TEAM_ID,
            opponent_id=AWAY_TEAM_ID,
            kickoff_days_ago=index + 10,
            halftime=halftime,
        )
        for index in range(3)
    )
    events = tuple(
        EventObservation(
            source=_source(f"goal:{match.provider_match_id}"),
            provider_match_id=match.provider_match_id,
            provider_team_id=(
                HOME_TEAM_ID
                if match.provider_match_id < 200
                else AWAY_TEAM_ID
            ),
            event_type="Goal",
            detail="Normal Goal",
            elapsed=60,
        )
        for match in (*home_history, *away_history)
    )
    return KairosMatchDataset(
        as_of=AS_OF,
        target=target,
        home_history=home_history,
        away_history=away_history,
        standings=(
            StandingObservation(
                source=_source("standing:home"),
                provider_team_id=HOME_TEAM_ID,
                rank=2,
                points=40,
                played=20,
                goals_diff=12,
            ),
            StandingObservation(
                source=_source("standing:away"),
                provider_team_id=AWAY_TEAM_ID,
                rank=8,
                points=28,
                played=20,
                goals_diff=1,
            ),
        ),
        statistics=(),
        events=events,
        h2h_history=h2h_history,
    )


def test_half_time_engine_exposes_all_markets_and_central_gate() -> None:
    analyses = analyze_half_time_markets(
        _dataset(),
        freshness_threshold_minutes=180,
    )

    assert {analysis.market for analysis in analyses} == {
        "FIRST_HALF_MORE_GOALS",
        "SECOND_HALF_MORE_GOALS",
        "EQUAL_HALF_GOALS",
        "FIRST_HALF_OVER_0_5",
        "SECOND_HALF_OVER_0_5",
        "SECOND_HALF_OVER_1_5",
    }
    assert all(analysis.sample_size == 10 for analysis in analyses)
    assert all(analysis.h2h_sample_size == 3 for analysis in analyses)
    assert all(analysis.estimated_probability is not None for analysis in analyses)
    eligible = [
        analysis for analysis in analyses if analysis.eligible_for_opportunity
    ]
    assert eligible
    assert all(
        analysis.estimated_probability is not None
        and analysis.estimated_probability >= 0.70
        and analysis.data_quality_score >= 65
        and analysis.technical_confidence_score >= 50
        and not analysis.guardrails
        for analysis in eligible
    )


def test_missing_half_time_scores_are_not_imputed_as_zero() -> None:
    analyses = analyze_half_time_markets(
        _dataset(missing_halftime=True),
        freshness_threshold_minutes=180,
    )

    assert all(analysis.insufficient_data for analysis in analyses)
    assert all(analysis.estimated_probability is None for analysis in analyses)
    assert all(not analysis.eligible_for_opportunity for analysis in analyses)


def test_stale_source_blocks_opportunity_even_with_strong_signal() -> None:
    analyses = analyze_half_time_markets(
        _dataset(stale_target=True),
        freshness_threshold_minutes=180,
    )

    assert all(not analysis.eligible_for_opportunity for analysis in analyses)
    assert all("STALE_SOURCE_DATA" in analysis.guardrails for analysis in analyses)


def test_opportunity_service_has_one_primary_and_non_correlated_alternatives() -> None:
    opportunity = KairosOpportunityService(
        freshness_threshold_minutes=180
    ).analyze(_dataset())

    assert opportunity.safety_decision == "ANALYSIS_ALLOWED"
    assert opportunity.primary_analysis is not None
    assert len(opportunity.alternative_analyses) <= 2
    markets = [
        opportunity.primary_analysis.market,
        *(
            alternative.market
            for alternative in opportunity.alternative_analyses
        ),
    ]
    assert len(markets) == len(set(markets))
    half_time_markets = {
        "FIRST_HALF_MORE_GOALS",
        "SECOND_HALF_MORE_GOALS",
        "EQUAL_HALF_GOALS",
        "FIRST_HALF_OVER_0_5",
        "SECOND_HALF_OVER_0_5",
        "SECOND_HALF_OVER_1_5",
    }
    assert sum(market in half_time_markets for market in markets) <= 1
    assert opportunity.read_only is True
    assert opportunity.persisted_by_request is False


def test_opportunity_schema_rejects_correlated_selections() -> None:
    opportunity = KairosOpportunityService(
        freshness_threshold_minutes=180
    ).analyze(_dataset())
    primary = next(
        market
        for market in opportunity.evaluated_markets
        if market.eligible_for_opportunity
    )
    correlated = next(
        market
        for market in opportunity.evaluated_markets
        if market.eligible_for_opportunity
        and market.market != primary.market
    )
    payload = opportunity.model_dump()
    payload["primary_analysis"] = {
        "market": primary.market,
        "estimated_probability": primary.estimated_probability,
        "data_quality_score": primary.data_quality_score,
        "technical_confidence_score": primary.technical_confidence_score,
        "sample_size": primary.sample_size,
        "risk": primary.risk,
        "reasons": primary.reasons,
        "guardrails": primary.guardrails,
        "analysis_hash": primary.analysis_hash,
    }
    payload["alternative_analyses"] = [
        {
            "market": correlated.market,
            "estimated_probability": correlated.estimated_probability,
            "data_quality_score": correlated.data_quality_score,
            "technical_confidence_score": (
                correlated.technical_confidence_score
            ),
            "sample_size": correlated.sample_size,
            "risk": correlated.risk,
            "reasons": correlated.reasons,
            "guardrails": correlated.guardrails,
            "analysis_hash": correlated.analysis_hash,
        }
    ]

    with pytest.raises(ValidationError, match="Correlated markets"):
        KairosMatchOpportunity.model_validate(payload)


def test_opportunity_service_returns_insufficient_data_without_selection() -> None:
    opportunity = KairosOpportunityService(
        freshness_threshold_minutes=180
    ).analyze(_dataset(missing_halftime=True))

    assert opportunity.safety_decision == "INSUFFICIENT_DATA"
    assert opportunity.primary_analysis is None
    assert opportunity.alternative_analyses == []


def test_h2h_below_three_has_no_influence() -> None:
    dataset = replace(_dataset(), h2h_history=_dataset().h2h_history[:2])
    analyses = analyze_half_time_markets(
        dataset,
        freshness_threshold_minutes=180,
    )

    assert all(
        any("aucune influence H2H" in reason for reason in analysis.reasons)
        for analysis in analyses
    )
