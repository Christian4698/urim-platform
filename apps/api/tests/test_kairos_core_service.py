from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest
from pydantic import ValidationError

from app.modules.kairos.models import (
    KairosDataError,
    KairosMatchDataset,
    KairosPreMatchWindowClosedError,
    KairosTemporalIntegrityError,
    MatchObservation,
    SourceObservation,
    StandingObservation,
    StatisticObservation,
)
from app.modules.kairos.schemas import KairosProbabilities
from app.modules.kairos.services import (
    CONFIDENCE_SCORE_CAP,
    FEATURE_SCHEMA_VERSION,
    MINIMUM_RESULTS_PER_TEAM,
    MODEL_VERSION,
    RECENT_WINDOW_MATCHES,
    KairosAnalysisService,
    build_kairos_methodology,
)

AS_OF = datetime(2026, 7, 27, 12, tzinfo=UTC)
TARGET_KICKOFF = AS_OF + timedelta(hours=8)
HOME_TEAM_ID = 10
AWAY_TEAM_ID = 20


def _source(
    identity: str,
    *,
    target: bool = False,
) -> SourceObservation:
    fetched_offset = timedelta(minutes=10 if target else 60)
    fetched_at = AS_OF - fetched_offset
    available_at = fetched_at - timedelta(minutes=1)
    observed_at = available_at - timedelta(minutes=1)
    return SourceObservation(
        observation_id=identity,
        provider="api-football",
        provider_event_id=identity,
        observed_at=observed_at,
        available_at=available_at,
        fetched_at=fetched_at,
        created_at=fetched_at + timedelta(seconds=1),
        source_version="football-v3",
        quality_flags=("REAL_PROVIDER_DATA", "NORMALIZED"),
        raw_hash=sha256(identity.encode()).hexdigest(),
        freshness_status="fresh",
    )


def _target() -> MatchObservation:
    return MatchObservation(
        source=_source("match:999", target=True),
        provider_match_id=999,
        provider_competition_id=39,
        season=2026,
        kickoff_at=TARGET_KICKOFF,
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


def _history(
    team_id: int,
    *,
    start_match_id: int,
    home_context: bool,
    scores: tuple[tuple[int, int], ...],
) -> tuple[MatchObservation, ...]:
    matches: list[MatchObservation] = []
    for index, score_for_team in enumerate(scores):
        requested_context = index < 3
        team_is_home = (
            requested_context if home_context else not requested_context
        )
        opponent_id = start_match_id + 100 + index
        if team_is_home:
            home_id, away_id = team_id, opponent_id
            home_name, away_name = f"Team {team_id}", f"Opponent {index}"
            home_score, away_score = score_for_team
        else:
            home_id, away_id = opponent_id, team_id
            home_name, away_name = f"Opponent {index}", f"Team {team_id}"
            away_score, home_score = score_for_team
        match_id = start_match_id + index
        matches.append(
            MatchObservation(
                source=_source(f"match:{match_id}"),
                provider_match_id=match_id,
                provider_competition_id=39,
                season=2026,
                kickoff_at=AS_OF - timedelta(days=index + 1),
                status_short="FT",
                home_team_provider_id=home_id,
                home_team_name=home_name,
                away_team_provider_id=away_id,
                away_team_name=away_name,
                goals_home=home_score,
                goals_away=away_score,
                score_fulltime_home=home_score,
                score_fulltime_away=away_score,
            )
        )
    return tuple(matches)


def _statistics(
    histories: tuple[tuple[int, tuple[MatchObservation, ...]], ...],
    *,
    zero_values: bool = False,
) -> tuple[StatisticObservation, ...]:
    rows: list[StatisticObservation] = []
    for team_id, history in histories:
        for match in history:
            values: tuple[tuple[str, object], ...] = (
                ("Total Shots", 0 if zero_values else 12),
                ("Ball Possession", "0%" if zero_values else "54%"),
                ("Corner Kicks", 0 if zero_values else 5),
                ("Yellow Cards", 0 if zero_values else 2),
                ("Red Cards", 0),
            )
            for statistic_type, value in values:
                identity = (
                    f"stat:{match.provider_match_id}:{team_id}:"
                    f"{statistic_type}"
                )
                rows.append(
                    StatisticObservation(
                        source=_source(identity),
                        provider_match_id=match.provider_match_id,
                        provider_team_id=team_id,
                        statistic_type=statistic_type,
                        statistic_value=value,
                    )
                )
    return tuple(rows)


def _dataset(
    *,
    home_scores: tuple[tuple[int, int], ...] = (
        (2, 0),
        (2, 1),
        (1, 0),
        (1, 1),
        (3, 1),
    ),
    away_scores: tuple[tuple[int, int], ...] = (
        (0, 1),
        (1, 1),
        (1, 2),
        (0, 0),
        (1, 3),
    ),
    include_statistics: bool = True,
    zero_statistics: bool = False,
) -> KairosMatchDataset:
    home_history = _history(
        HOME_TEAM_ID,
        start_match_id=100,
        home_context=True,
        scores=home_scores,
    )
    away_history = _history(
        AWAY_TEAM_ID,
        start_match_id=200,
        home_context=False,
        scores=away_scores,
    )
    statistics = (
        _statistics(
            (
                (HOME_TEAM_ID, home_history),
                (AWAY_TEAM_ID, away_history),
            ),
            zero_values=zero_statistics,
        )
        if include_statistics
        else ()
    )
    return KairosMatchDataset(
        as_of=AS_OF,
        target=_target(),
        home_history=home_history,
        away_history=away_history,
        standings=(
            StandingObservation(
                source=_source("standing:home"),
                provider_team_id=HOME_TEAM_ID,
                rank=2,
                points=40,
                played=20,
                goals_diff=18,
            ),
            StandingObservation(
                source=_source("standing:away"),
                provider_team_id=AWAY_TEAM_ID,
                rank=12,
                points=22,
                played=20,
                goals_diff=-8,
            ),
        ),
        statistics=statistics,
        events=(),
    )


def test_kairos_core_produces_deterministic_probabilities_and_audit_metadata() -> None:
    dataset = _dataset()
    first = KairosAnalysisService().analyze(dataset)
    second = KairosAnalysisService().analyze(dataset)

    assert first.analysis_status == "ready"
    assert first.decision == "NO_BET"
    assert first.safety_decision == "NO_BET"
    assert first.analytical_suggestion == first.suggestion
    assert first.model_version == MODEL_VERSION
    assert first.probabilities is not None
    assert first.market_probabilities is not None
    assert first.home_win_probability is not None
    assert first.draw_probability is not None
    assert first.away_win_probability is not None
    assert (
        first.home_win_probability
        + first.draw_probability
        + first.away_win_probability
    ) == pytest.approx(1.0)
    assert first.home_win_probability > first.away_win_probability
    assert (
        first.market_probabilities.over_2_5
        + first.market_probabilities.under_2_5
    ) == pytest.approx(1.0)
    assert first.market_probabilities.home_or_draw == pytest.approx(
        first.home_win_probability + first.draw_probability
    )
    assert first.suggestion.provider_match_id == 999
    assert first.suggestion.recommendation in {
        "Home Win",
        "Away Win",
        "Draw",
        "Double Chance",
        "Over 2.5",
        "Under 2.5",
        "BTTS",
        "NO_BET",
    }
    assert first.suggestion.confidence_level != "high"
    assert first.suggestion.risk_level in {"high", "elevated"}
    assert first.suggestion.bookmaker_data_used is False
    assert first.suggestion.not_for_betting is True
    assert first.suggestion.decision_hash == second.suggestion.decision_hash
    assert 0 < first.confidence_score <= CONFIDENCE_SCORE_CAP
    assert 0 < first.data_quality_score <= 85
    assert first.automatic_betting_enabled is False
    assert first.live_automatic_enabled is False
    assert first.persisted is False
    assert first.prediction_id == second.prediction_id
    assert first.feature_snapshot_id == second.feature_snapshot_id
    assert first.immutable_hash == second.immutable_hash
    assert len(first.provenance.feature_snapshot_hash) == 64
    assert first.provenance.source_observation_count > 1
    assert len(first.model_dump_json()) < 64_000
    assert {reason.code for reason in first.reasons} >= {
        "GOAL_RATE_BASELINE",
        "RECENT_FORM",
        "STANDINGS",
        "HOME_AWAY_SPLIT",
        "SHOTS",
        "POSSESSION",
        "CORNERS",
        "CARDS",
    }
    assert {warning.code for warning in first.warnings} >= {
        "UNCALIBRATED_BASELINE",
        "ANALYSIS_ONLY_NO_BETTING",
        "LIVE_AUTOMATION_DISABLED",
        "SINGLE_PROVIDER",
        "DRIFT_MONITORING_UNAVAILABLE",
    }


def test_concurrent_analysis_is_deterministic_for_the_same_snapshot() -> None:
    dataset = _dataset()
    service = KairosAnalysisService()

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = tuple(
            executor.map(lambda _: service.analyze(dataset), range(32))
        )

    assert len({result.prediction_id for result in results}) == 1
    assert len({result.feature_snapshot_id for result in results}) == 1
    assert len({result.immutable_hash for result in results}) == 1
    assert {
        (
            result.home_win_probability,
            result.draw_probability,
            result.away_win_probability,
        )
        for result in results
    } == {
        (
            results[0].home_win_probability,
            results[0].draw_probability,
            results[0].away_win_probability,
        )
    }


def test_missing_statistics_reduce_quality_without_blocking_goal_baseline() -> None:
    complete = KairosAnalysisService().analyze(_dataset())
    partial = KairosAnalysisService().analyze(
        _dataset(include_statistics=False)
    )

    assert partial.analysis_status == "ready"
    assert partial.probabilities is not None
    assert partial.data_quality_score < complete.data_quality_score
    assert partial.data_availability["shots"].coverage_score == 0
    assert {
        warning.code for warning in partial.warnings
    } >= {
        "PARTIAL_SHOTS",
        "PARTIAL_POSSESSION",
        "PARTIAL_CORNERS",
        "PARTIAL_CARDS",
    }


def test_zero_statistics_are_observations_and_not_treated_as_missing() -> None:
    result = KairosAnalysisService().analyze(
        _dataset(zero_statistics=True)
    )

    assert result.analysis_status == "ready"
    assert result.data_availability["shots"].coverage_score == 100
    assert result.data_availability["possession"].coverage_score == 100
    assert result.data_availability["corners"].coverage_score == 100
    assert result.data_availability["cards"].coverage_score == 100


def test_insufficient_history_returns_null_probabilities() -> None:
    dataset = _dataset(
        home_scores=((1, 0), (0, 0)),
        away_scores=((0, 1), (1, 1)),
    )
    result = KairosAnalysisService().analyze(dataset)

    assert MINIMUM_RESULTS_PER_TEAM == 3
    assert result.analysis_status == "insufficient_data"
    assert result.decision == "INSUFFICIENT_DATA"
    assert result.safety_decision == "INSUFFICIENT_DATA"
    assert result.analytical_suggestion == result.suggestion
    assert result.probabilities is None
    assert result.home_win_probability is None
    assert result.draw_probability is None
    assert result.away_win_probability is None
    assert result.confidence_score == 0
    assert result.market_probabilities is None
    assert result.suggestion.recommendation == "NO_BET"
    assert result.suggestion.no_bet is True
    assert result.suggestion.confidence_level == "blocked"
    assert "INSUFFICIENT_RESULT_HISTORY" in {
        warning.code for warning in result.warnings
    }
    insufficient_reason = next(
        reason
        for reason in result.suggestion.reasons
        if reason.code == "INSUFFICIENT_RESULT_HISTORY"
    )
    assert insufficient_reason.category == "guardrail"
    assert insufficient_reason.critical is True


def test_stale_target_is_an_explicit_critical_guardrail() -> None:
    dataset = _dataset()
    stale_fetched_at = AS_OF - timedelta(hours=4)
    stale_source = replace(
        dataset.target.source,
        observed_at=stale_fetched_at - timedelta(minutes=2),
        available_at=stale_fetched_at - timedelta(minutes=1),
        fetched_at=stale_fetched_at,
        created_at=stale_fetched_at + timedelta(seconds=1),
        freshness_status="stale",
    )
    stale_dataset = replace(
        dataset,
        target=replace(dataset.target, source=stale_source),
    )

    result = KairosAnalysisService().analyze(stale_dataset)

    assert result.safety_decision == "NO_BET"
    assert result.suggestion.no_bet is True
    stale_reason = next(
        reason
        for reason in result.suggestion.reasons
        if reason.code == "STALE_TARGET_DATA"
    )
    assert stale_reason.category == "guardrail"
    assert stale_reason.critical is True


def test_future_observation_is_blocked_by_adversarial_temporal_guard() -> None:
    dataset = _dataset()
    statistic = dataset.statistics[0]
    future_source = replace(
        statistic.source,
        available_at=AS_OF + timedelta(minutes=1),
        fetched_at=AS_OF + timedelta(minutes=2),
        created_at=AS_OF + timedelta(minutes=3),
    )
    contaminated = replace(
        dataset,
        statistics=(
            replace(statistic, source=future_source),
            *dataset.statistics[1:],
        ),
    )

    with pytest.raises(
        KairosTemporalIntegrityError,
        match="future_available_observation_detected",
    ):
        KairosAnalysisService().analyze(contaminated)


@pytest.mark.parametrize(
    ("timestamp_field", "expected_error"),
    [
        ("fetched_at", "future_fetched_observation_detected"),
        ("created_at", "future_persisted_observation_detected"),
    ],
)
def test_each_local_future_timestamp_is_blocked(
    timestamp_field: str,
    expected_error: str,
) -> None:
    dataset = _dataset()
    statistic = dataset.statistics[0]
    future_source = replace(
        statistic.source,
        **{timestamp_field: AS_OF + timedelta(minutes=1)},
    )
    contaminated = replace(
        dataset,
        statistics=(
            replace(statistic, source=future_source),
            *dataset.statistics[1:],
        ),
    )

    with pytest.raises(KairosTemporalIntegrityError, match=expected_error):
        KairosAnalysisService().analyze(contaminated)


def test_created_at_before_fetched_at_is_blocked() -> None:
    dataset = _dataset()
    statistic = dataset.statistics[0]
    out_of_order_source = replace(
        statistic.source,
        created_at=statistic.source.available_at,
    )
    contaminated = replace(
        dataset,
        statistics=(
            replace(statistic, source=out_of_order_source),
            *dataset.statistics[1:],
        ),
    )

    with pytest.raises(
        KairosTemporalIntegrityError,
        match="observation_temporal_order_invalid",
    ):
        KairosAnalysisService().analyze(contaminated)


def test_completed_match_kicking_off_after_as_of_is_blocked() -> None:
    dataset = _dataset()
    future_history = replace(
        dataset.home_history[0],
        kickoff_at=AS_OF + timedelta(minutes=1),
    )
    contaminated = replace(
        dataset,
        home_history=(future_history, *dataset.home_history[1:]),
    )

    with pytest.raises(
        KairosTemporalIntegrityError,
        match="future_history_match_detected",
    ):
        KairosAnalysisService().analyze(contaminated)


def test_live_target_status_is_blocked_even_with_future_kickoff() -> None:
    dataset = _dataset()
    contaminated = replace(
        dataset,
        target=replace(dataset.target, status_short="1H"),
    )

    with pytest.raises(KairosDataError, match="target_match_is_not_scheduled"):
        KairosAnalysisService().analyze(contaminated)


def test_non_completed_history_status_is_blocked() -> None:
    dataset = _dataset()
    contaminated = replace(
        dataset,
        home_history=(
            replace(dataset.home_history[0], status_short="NS"),
            *dataset.home_history[1:],
        ),
    )

    with pytest.raises(KairosDataError, match="history_match_not_completed"):
        KairosAnalysisService().analyze(contaminated)


def test_target_match_cannot_leak_into_its_own_history() -> None:
    dataset = _dataset()
    contaminated = replace(
        dataset,
        home_history=(dataset.target, *dataset.home_history),
    )

    with pytest.raises(
        KairosTemporalIntegrityError,
        match="target_match_leaked_into_history",
    ):
        KairosAnalysisService().analyze(contaminated)


def test_analysis_is_blocked_at_or_after_kickoff() -> None:
    dataset = replace(_dataset(), as_of=TARGET_KICKOFF)

    with pytest.raises(
        KairosPreMatchWindowClosedError,
        match="pre_match_window_closed",
    ):
        KairosAnalysisService().analyze(dataset)


def test_probability_schema_rejects_non_normalized_distribution() -> None:
    with pytest.raises(ValidationError):
        KairosProbabilities(
            home_win=0.5,
            draw=0.3,
            away_win=0.3,
        )


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf")])
def test_probability_schema_rejects_non_finite_values(
    non_finite: float,
) -> None:
    with pytest.raises(ValidationError):
        KairosProbabilities(
            home_win=non_finite,
            draw=0.5,
            away_win=0.5,
        )


def test_invalid_numeric_statistics_are_missing_and_never_nan() -> None:
    dataset = _dataset()
    invalid_values: dict[str, object] = {
        "Total Shots": float("nan"),
        "Ball Possession": "Infinity",
        "Corner Kicks": -1,
        "Yellow Cards": 10**1000,
        "Red Cards": None,
    }
    contaminated = replace(
        dataset,
        statistics=tuple(
            replace(
                statistic,
                statistic_value=invalid_values[statistic.statistic_type],
            )
            for statistic in dataset.statistics
        ),
    )

    result = KairosAnalysisService().analyze(contaminated)

    assert result.analysis_status == "ready"
    assert result.probabilities is not None
    assert result.data_availability["shots"].coverage_score == 0
    assert result.data_availability["possession"].coverage_score == 0
    assert result.data_availability["corners"].coverage_score == 0
    assert result.data_availability["cards"].coverage_score == 0
    assert all(
        value is not None and value == value
        for value in (
            result.home_win_probability,
            result.draw_probability,
            result.away_win_probability,
        )
    )


def test_oversized_numeric_string_is_treated_as_missing() -> None:
    dataset = _dataset()
    contaminated = replace(
        dataset,
        statistics=tuple(
            replace(statistic, statistic_value="9" * 100_000)
            for statistic in dataset.statistics
        ),
    )

    result = KairosAnalysisService().analyze(contaminated)

    assert result.analysis_status == "ready"
    assert all(
        result.data_availability[name].coverage_score == 0
        for name in ("shots", "possession", "corners", "cards")
    )


def test_invalid_scores_are_missing_instead_of_extreme_features() -> None:
    dataset = _dataset()
    contaminated_home = tuple(
        replace(
            match,
            goals_home=-1,
            goals_away=0,
            score_fulltime_home=-1,
            score_fulltime_away=0,
        )
        for match in dataset.home_history
    )

    result = KairosAnalysisService().analyze(
        replace(dataset, home_history=contaminated_home)
    )

    assert result.analysis_status == "insufficient_data"
    assert result.probabilities is None
    assert result.confidence_score == 0


def test_spoofed_provider_and_invalid_raw_hash_are_blocked() -> None:
    dataset = _dataset()
    spoofed = replace(
        dataset,
        target=replace(
            dataset.target,
            source=replace(
                dataset.target.source,
                provider="spoofed-provider",
            ),
        ),
    )
    invalid_hash = replace(
        dataset,
        target=replace(
            dataset.target,
            source=replace(dataset.target.source, raw_hash="not-a-sha256"),
        ),
    )

    with pytest.raises(KairosDataError, match="unexpected_source_provider"):
        KairosAnalysisService().analyze(spoofed)
    with pytest.raises(KairosDataError, match="invalid_source_raw_hash"):
        KairosAnalysisService().analyze(invalid_hash)


@pytest.mark.parametrize(
    "source_change",
    (
        {"quality_flags": tuple(f"flag-{index}" for index in range(33))},
        {"quality_flags": ("x" * 161,)},
        {"freshness_status": "forged"},
        {"provider_event_id": "x" * 241},
    ),
)
def test_unbounded_or_forged_provenance_is_blocked(
    source_change: dict[str, object],
) -> None:
    dataset = _dataset()
    contaminated = replace(
        dataset,
        target=replace(
            dataset.target,
            source=replace(dataset.target.source, **source_change),
        ),
    )

    with pytest.raises(
        KairosDataError,
        match="invalid_source_provenance_shape",
    ):
        KairosAnalysisService().analyze(contaminated)


def test_conflicting_observation_identity_is_blocked() -> None:
    dataset = _dataset()
    statistic = dataset.statistics[0]
    conflicting = replace(
        statistic,
        source=replace(
            statistic.source,
            observation_id=dataset.target.source.observation_id,
        ),
    )

    with pytest.raises(
        KairosDataError,
        match="conflicting_source_observation_identity",
    ):
        KairosAnalysisService().analyze(
            replace(
                dataset,
                statistics=(conflicting, *dataset.statistics[1:]),
            )
        )


def test_provenance_metadata_changes_feature_snapshot_hash() -> None:
    dataset = _dataset()
    baseline = KairosAnalysisService().analyze(dataset)
    changed_source = replace(
        dataset.target.source,
        source_version="football-v3-corrected",
    )
    changed = KairosAnalysisService().analyze(
        replace(dataset, target=replace(dataset.target, source=changed_source))
    )

    assert (
        changed.provenance.feature_snapshot_hash
        != baseline.provenance.feature_snapshot_hash
    )
    assert changed.feature_snapshot_id != baseline.feature_snapshot_id


def test_statistic_tampering_changes_feature_snapshot_and_immutable_hash() -> None:
    dataset = _dataset()
    baseline = KairosAnalysisService().analyze(dataset)
    statistic = dataset.statistics[0]
    tampered = KairosAnalysisService().analyze(
        replace(
            dataset,
            statistics=(
                replace(statistic, statistic_value=13),
                *dataset.statistics[1:],
            ),
        )
    )

    assert (
        tampered.provenance.feature_snapshot_hash
        != baseline.provenance.feature_snapshot_hash
    )
    assert tampered.feature_snapshot_id != baseline.feature_snapshot_id
    assert tampered.immutable_hash != baseline.immutable_hash


def test_methodology_registers_versioned_features_and_restrictions() -> None:
    methodology = build_kairos_methodology(ttl_minutes=240)

    assert methodology.model_version == MODEL_VERSION
    assert methodology.feature_schema_version == FEATURE_SCHEMA_VERSION
    assert methodology.recent_window_matches == RECENT_WINDOW_MATCHES
    assert methodology.minimum_results_per_team == MINIMUM_RESULTS_PER_TEAM
    assert methodology.calibration_status == "not_calibrated"
    assert methodology.drift_monitoring_status == "not_available"
    assert methodology.read_only is True
    assert methodology.db_writes is False
    assert methodology.provider_calls is False
    assert methodology.automatic_betting_enabled is False
    assert methodology.live_automatic_enabled is False
    assert {feature.name for feature in methodology.feature_registry} == {
        "recent_form",
        "standings",
        "home_away",
        "goals",
        "shots",
        "possession",
        "corners",
        "cards",
    }
    assert all(
        feature.window_matches == RECENT_WINDOW_MATCHES
        and feature.ttl_minutes == 240
        and feature.missing_policy == "explicit_null_no_imputation"
        for feature in methodology.feature_registry
    )
