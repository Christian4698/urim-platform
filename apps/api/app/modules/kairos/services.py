from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from hashlib import sha256
import json
import math
import re
import unicodedata
from typing import Any, Final
from uuid import NAMESPACE_DNS, uuid5

from app.modules.kairos.models import (
    EventObservation,
    KairosDataError,
    KairosMatchDataset,
    MatchObservation,
    StandingObservation,
    StatisticObservation,
    TeamFeatureProfile,
)
from app.modules.kairos.half_time import analyze_half_time_markets
from app.modules.kairos.schemas import (
    KairosAnalysisResponse,
    KairosDataFreshness,
    KairosFeatureAvailability,
    KairosFeatureDefinition,
    KairosMarketProbabilities,
    KairosMethodologyResponse,
    KairosProbabilities,
    KairosProvenance,
    KairosReason,
    KairosTeamSummary,
    KairosWarning,
)
from app.modules.kairos.suggestions import build_kairos_suggestion

MODEL_VERSION: Final = "kairos_core_b2_2_v1"
FEATURE_SCHEMA_VERSION: Final = "kairos_pre_match_features_v1"
RECENT_WINDOW_MATCHES: Final = 5
MINIMUM_RESULTS_PER_TEAM: Final = 3
CONFIDENCE_SCORE_CAP: Final = 65
DEFAULT_FEATURE_TTL_MINUTES: Final = 180
MAX_POISSON_GOALS: Final = 10
KAIROS_NAMESPACE: Final = uuid5(NAMESPACE_DNS, "urim.kairos.core")
SCHEDULED_STATUSES: Final = frozenset({"NS", "TBD"})
MAX_COUNT_STATISTIC_VALUE: Final = 1_000.0
MAX_POSSESSION_VALUE: Final = 100.0

FEATURE_WEIGHTS: Final[dict[str, float]] = {
    "recent_form": 0.16,
    "standings": 0.12,
    "home_away": 0.12,
    "goals": 0.22,
    "shots": 0.10,
    "possession": 0.09,
    "corners": 0.08,
    "cards": 0.06,
    "provenance": 0.05,
}

SIGNAL_WEIGHTS: Final[dict[str, float]] = {
    "recent_form": 0.18,
    "standings": 0.16,
    "home_away": 0.12,
    "shots": 0.08,
    "possession": 0.06,
    "corners": 0.05,
    "cards": 0.04,
}

STATISTIC_ALIASES: Final[dict[str, frozenset[str]]] = {
    "shots": frozenset({"total shots", "shots total"}),
    "shots_on_goal": frozenset({"shots on goal", "shots on target"}),
    "possession": frozenset({"ball possession", "possession"}),
    "corners": frozenset({"corner kicks", "corners"}),
    "yellow_cards": frozenset({"yellow cards", "yellow card"}),
    "red_cards": frozenset({"red cards", "red card"}),
}


class KairosAnalysisService:
    def __init__(
        self,
        *,
        freshness_threshold_minutes: int = DEFAULT_FEATURE_TTL_MINUTES,
    ) -> None:
        if freshness_threshold_minutes <= 0:
            raise ValueError("freshness_threshold_minutes must be positive.")
        self.freshness_threshold_minutes = freshness_threshold_minutes

    def analyze(self, dataset: KairosMatchDataset) -> KairosAnalysisResponse:
        dataset.validate_temporal_integrity()
        dataset.validate_data_integrity()
        if dataset.target.status_short not in SCHEDULED_STATUSES:
            raise KairosDataError("target_match_is_not_scheduled")

        statistic_index = _statistic_index(dataset.statistics)
        card_event_index = _card_event_index(dataset.events)
        standing_index = {
            standing.provider_team_id: standing
            for standing in dataset.standings
        }
        home_profile = _build_team_profile(
            team_id=dataset.target.home_team_provider_id,
            team_name=dataset.target.home_team_name,
            history=dataset.home_history,
            venue="home",
            standing=standing_index.get(
                dataset.target.home_team_provider_id
            ),
            statistic_index=statistic_index,
            card_event_index=card_event_index,
        )
        away_profile = _build_team_profile(
            team_id=dataset.target.away_team_provider_id,
            team_name=dataset.target.away_team_name,
            history=dataset.away_history,
            venue="away",
            standing=standing_index.get(
                dataset.target.away_team_provider_id
            ),
            statistic_index=statistic_index,
            card_event_index=card_event_index,
        )

        availability = _feature_availability(home_profile, away_profile)
        sources = dataset.source_observations()
        freshness = _freshness(
            dataset,
            threshold_minutes=self.freshness_threshold_minutes,
        )
        data_quality_score = _data_quality_score(
            availability,
            sources=sources,
            target_is_stale=freshness.status == "stale",
        )
        feature_hash = _feature_snapshot_hash(
            dataset,
            home_profile=home_profile,
            away_profile=away_profile,
            availability=availability,
        )
        feature_snapshot_id = uuid5(
            KAIROS_NAMESPACE,
            f"feature-snapshot:{feature_hash}",
        )
        prediction_id = uuid5(
            KAIROS_NAMESPACE,
            f"analysis:{feature_hash}:{MODEL_VERSION}",
        )

        warnings = _base_warnings(
            availability,
            home_profile=home_profile,
            away_profile=away_profile,
            target_is_stale=freshness.status == "stale",
        )
        sufficient_results = (
            home_profile.result_sample_size >= MINIMUM_RESULTS_PER_TEAM
            and away_profile.result_sample_size >= MINIMUM_RESULTS_PER_TEAM
        )

        probabilities: KairosProbabilities | None = None
        market_probabilities: KairosMarketProbabilities | None = None
        confidence_score = 0.0
        decision = "INSUFFICIENT_DATA"
        analysis_status = "insufficient_data"
        signals: dict[str, float | None] = {}
        expected_home_goals: float | None = None
        expected_away_goals: float | None = None

        if sufficient_results:
            expected_home_goals, expected_away_goals, signals = (
                _expected_goals(home_profile, away_profile)
            )
            market_probabilities = _poisson_market_probabilities(
                expected_home_goals,
                expected_away_goals,
            )
            probabilities = KairosProbabilities(
                home_win=market_probabilities.home_win,
                draw=market_probabilities.draw,
                away_win=market_probabilities.away_win,
            )
            confidence_score = _confidence_score(
                data_quality_score,
                home_profile=home_profile,
                away_profile=away_profile,
                signals=signals,
            )
            decision = "NO_BET"
            analysis_status = "ready"
        else:
            warnings.append(
                KairosWarning(
                    code="INSUFFICIENT_RESULT_HISTORY",
                    message=(
                        "Au moins trois résultats complets par équipe sont "
                        "requis; aucune probabilité n'est fabriquée."
                    ),
                    severity="blocking",
                )
            )

        reasons = _reasons(
            home_profile,
            away_profile,
            signals=signals,
            expected_home_goals=expected_home_goals,
            expected_away_goals=expected_away_goals,
            sufficient_results=sufficient_results,
        )
        provenance = KairosProvenance(
            source_observation_count=len(sources),
            source_observation_ids=[
                source.observation_id for source in sources
            ],
            source_raw_hashes=sorted(
                {source.raw_hash for source in sources}
            ),
            max_available_at=max(
                source.available_at for source in sources
            ),
            feature_snapshot_hash=feature_hash,
        )
        home_summary = _team_summary(home_profile)
        away_summary = _team_summary(away_profile)
        suggestion = build_kairos_suggestion(
            provider_match_id=dataset.target.provider_match_id,
            kickoff_at=dataset.target.kickoff_at,
            home_team_name=dataset.target.home_team_name,
            away_team_name=dataset.target.away_team_name,
            competition_name=dataset.target.competition_name,
            market_probabilities=market_probabilities,
            confidence_score=confidence_score,
            data_quality_score=data_quality_score,
            freshness_status=freshness.status,
            analysis_reasons=reasons,
            analysis_warnings=warnings,
            feature_snapshot_hash=feature_hash,
        )
        immutable_hash = _immutable_analysis_hash(
            prediction_id=str(prediction_id),
            feature_hash=feature_hash,
            prediction_time=dataset.as_of.isoformat(),
            probabilities=(
                probabilities.model_dump(mode="json")
                if probabilities is not None
                else None
            ),
            market_probabilities=(
                market_probabilities.model_dump(mode="json")
                if market_probabilities is not None
                else None
            ),
            confidence_score=confidence_score,
            data_quality_score=data_quality_score,
            safety_decision=decision,
            decision=decision,
            reasons=[
                reason.model_dump(mode="json") for reason in reasons
            ],
            warnings=[
                warning.model_dump(mode="json") for warning in warnings
            ],
            suggestion=suggestion.model_dump(mode="json"),
        )

        return KairosAnalysisResponse(
            provider_match_id=dataset.target.provider_match_id,
            kickoff_at=dataset.target.kickoff_at,
            prediction_id=prediction_id,
            model_version=MODEL_VERSION,
            feature_snapshot_id=feature_snapshot_id,
            prediction_time=dataset.as_of,
            probabilities=probabilities,
            market_probabilities=market_probabilities,
            home_win_probability=(
                probabilities.home_win if probabilities else None
            ),
            draw_probability=probabilities.draw if probabilities else None,
            away_win_probability=(
                probabilities.away_win if probabilities else None
            ),
            safety_decision=decision,
            decision=decision,
            confidence_score=confidence_score,
            data_quality_score=data_quality_score,
            reasons=reasons,
            warnings=warnings,
            data_freshness=freshness,
            data_availability=availability,
            home_team=home_summary,
            away_team=away_summary,
            provenance=provenance,
            analytical_suggestion=suggestion,
            suggestion=suggestion,
            immutable_hash=immutable_hash,
            analysis_status=analysis_status,
            half_time_analysis=list(
                analyze_half_time_markets(
                    dataset,
                    freshness_threshold_minutes=(
                        self.freshness_threshold_minutes
                    ),
                )
            ),
        )


def build_kairos_methodology(
    *,
    ttl_minutes: int = DEFAULT_FEATURE_TTL_MINUTES,
) -> KairosMethodologyResponse:
    definitions = [
        (
            "recent_form",
            ["api_football_matches", "completed results", "as_of"],
        ),
        (
            "standings",
            ["api_football_standings", "competition", "season", "as_of"],
        ),
        (
            "home_away",
            ["api_football_matches", "venue split", "as_of"],
        ),
        (
            "goals",
            ["api_football_matches", "fulltime scores", "as_of"],
        ),
        (
            "shots",
            ["api_football_match_statistics", "as_of"],
        ),
        (
            "possession",
            ["api_football_match_statistics", "as_of"],
        ),
        (
            "corners",
            ["api_football_match_statistics", "as_of"],
        ),
        (
            "cards",
            [
                "api_football_match_statistics",
                "api_football_match_events",
                "as_of",
            ],
        ),
    ]
    return KairosMethodologyResponse(
        model_version=MODEL_VERSION,
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        recent_window_matches=RECENT_WINDOW_MATCHES,
        minimum_results_per_team=MINIMUM_RESULTS_PER_TEAM,
        confidence_score_cap=CONFIDENCE_SCORE_CAP,
        supported_suggestions=[
            "Home Win",
            "Away Win",
            "Draw",
            "Double Chance",
            "Over 2.5",
            "Under 2.5",
            "BTTS",
            "NO_BET",
        ],
        feature_registry=[
            KairosFeatureDefinition(
                name=name,
                version=f"{name}_v1",
                window_matches=RECENT_WINDOW_MATCHES,
                ttl_minutes=ttl_minutes,
                dependencies=dependencies,
            )
            for name, dependencies in definitions
        ],
        restrictions=[
            "Analyse pré-match uniquement.",
            "Baseline déterministe non calibrée hors échantillon.",
            "Aucun appel fournisseur et aucune écriture en base.",
            "Aucune cote, aucun bookmaker et aucune exécution de pari.",
            "Aucune automatisation live.",
            "Les données manquantes restent nulles et réduisent la qualité.",
            (
                "Les suggestions B2.2 sont analytiques, non calibrées, "
                "sans cote ni mise, et ne constituent pas un conseil de pari."
            ),
            (
                "Le score est le minimum du signal normalisé, de la "
                "qualité des données et de la confiance technique normalisée."
            ),
        ],
    )


def _build_team_profile(
    *,
    team_id: int,
    team_name: str,
    history: tuple[MatchObservation, ...],
    venue: str,
    standing: StandingObservation | None,
    statistic_index: dict[tuple[int, int], dict[str, float]],
    card_event_index: dict[tuple[int, int], float],
) -> TeamFeatureProfile:
    recent = history[:RECENT_WINDOW_MATCHES]
    result_rows = [
        (match, score)
        for match in recent
        if (score := match.score_for(team_id)) is not None
    ]
    venue_rows: list[tuple[MatchObservation, tuple[int, int]]] = []
    for match in history:
        is_requested_venue = (
            venue == "home"
            and match.home_team_provider_id == team_id
        ) or (
            venue == "away"
            and match.away_team_provider_id == team_id
        )
        score = match.score_for(team_id)
        if is_requested_venue and score is not None:
            venue_rows.append((match, score))
        if len(venue_rows) >= RECENT_WINDOW_MATCHES:
            break

    points = [_points_for(score) for _, score in result_rows]
    goals_for = [float(score[0]) for _, score in result_rows]
    goals_against = [float(score[1]) for _, score in result_rows]
    venue_points = [_points_for(score) for _, score in venue_rows]
    venue_goals_for = [float(score[0]) for _, score in venue_rows]
    venue_goals_against = [float(score[1]) for _, score in venue_rows]

    metric_values: dict[str, list[float]] = defaultdict(list)
    for match in recent:
        key = (match.provider_match_id, team_id)
        statistics = statistic_index.get(key, {})
        shots = _first_value(
            statistics,
            ("shots", "shots_on_goal"),
        )
        possession = statistics.get("possession")
        corners = statistics.get("corners")
        cards = _cards_value(statistics, card_event_index.get(key))
        for metric_name, metric_value in (
            ("shots", shots),
            ("possession", possession),
            ("corners", corners),
            ("cards", cards),
        ):
            if metric_value is not None:
                metric_values[metric_name].append(metric_value)

    standing_points_per_game = None
    if (
        standing is not None
        and standing.points is not None
        and standing.played is not None
        and standing.played > 0
    ):
        standing_points_per_game = standing.points / standing.played

    return TeamFeatureProfile(
        team_id=team_id,
        team_name=team_name,
        result_sample_size=len(result_rows),
        venue_sample_size=len(venue_rows),
        form_points_per_game=_average(points),
        goals_for_average=_average(goals_for),
        goals_against_average=_average(goals_against),
        venue_points_per_game=_average(venue_points),
        venue_goals_for_average=_average(venue_goals_for),
        venue_goals_against_average=_average(venue_goals_against),
        shots_average=_average(metric_values["shots"]),
        shots_sample_size=len(metric_values["shots"]),
        possession_average=_average(metric_values["possession"]),
        possession_sample_size=len(metric_values["possession"]),
        corners_average=_average(metric_values["corners"]),
        corners_sample_size=len(metric_values["corners"]),
        cards_average=_average(metric_values["cards"]),
        cards_sample_size=len(metric_values["cards"]),
        standing_rank=standing.rank if standing else None,
        standing_points_per_game=standing_points_per_game,
    )


def _feature_availability(
    home: TeamFeatureProfile,
    away: TeamFeatureProfile,
) -> dict[str, KairosFeatureAvailability]:
    definitions = {
        "recent_form": (
            home.result_sample_size,
            away.result_sample_size,
            RECENT_WINDOW_MATCHES,
        ),
        "standings": (
            int(home.standing_rank is not None),
            int(away.standing_rank is not None),
            1,
        ),
        "home_away": (
            home.venue_sample_size,
            away.venue_sample_size,
            MINIMUM_RESULTS_PER_TEAM,
        ),
        "goals": (
            home.result_sample_size,
            away.result_sample_size,
            RECENT_WINDOW_MATCHES,
        ),
        "shots": (
            home.shots_sample_size,
            away.shots_sample_size,
            RECENT_WINDOW_MATCHES,
        ),
        "possession": (
            home.possession_sample_size,
            away.possession_sample_size,
            RECENT_WINDOW_MATCHES,
        ),
        "corners": (
            home.corners_sample_size,
            away.corners_sample_size,
            RECENT_WINDOW_MATCHES,
        ),
        "cards": (
            home.cards_sample_size,
            away.cards_sample_size,
            RECENT_WINDOW_MATCHES,
        ),
        "provenance": (1, 1, 1),
    }
    return {
        feature_name: _availability(
            home_samples,
            away_samples,
            required_samples,
        )
        for feature_name, (
            home_samples,
            away_samples,
            required_samples,
        ) in definitions.items()
    }


def _availability(
    home_samples: int,
    away_samples: int,
    required_samples: int,
) -> KairosFeatureAvailability:
    home_coverage = min(home_samples / required_samples, 1.0)
    away_coverage = min(away_samples / required_samples, 1.0)
    return KairosFeatureAvailability(
        home_samples=home_samples,
        away_samples=away_samples,
        required_samples_per_team=required_samples,
        coverage_score=round(
            100 * (home_coverage + away_coverage) / 2,
            1,
        ),
        available_for_both_teams=home_samples > 0 and away_samples > 0,
    )


def _data_quality_score(
    availability: dict[str, KairosFeatureAvailability],
    *,
    sources: tuple[Any, ...],
    target_is_stale: bool,
) -> float:
    weighted_coverage = sum(
        FEATURE_WEIGHTS[name]
        * availability[name].coverage_score
        / 100
        for name in FEATURE_WEIGHTS
    )
    score = weighted_coverage * 100

    unsafe_flag_count = sum(
        1
        for source in sources
        for flag in source.quality_flags
        if any(
            marker in flag.upper()
            for marker in ("INVALID", "CONFLICT", "STALE", "UNKNOWN")
        )
    )
    score -= min(unsafe_flag_count * 2.0, 20.0)
    if target_is_stale:
        score -= 10.0

    # B2.1 has only one provider. A perfect multi-source quality score would
    # overstate what the current data foundation can prove.
    return round(max(0.0, min(score, 85.0)), 1)


def _expected_goals(
    home: TeamFeatureProfile,
    away: TeamFeatureProfile,
) -> tuple[float, float, dict[str, float | None]]:
    home_base = _required_average(
        (
            home.goals_for_average,
            away.goals_against_average,
            home.venue_goals_for_average,
            away.venue_goals_against_average,
        )
    )
    away_base = _required_average(
        (
            away.goals_for_average,
            home.goals_against_average,
            away.venue_goals_for_average,
            home.venue_goals_against_average,
        )
    )
    signals = {
        "goals": _clamp((home_base - away_base) / 2.0),
        "recent_form": _difference_signal(
            home.form_points_per_game,
            away.form_points_per_game,
            scale=3.0,
        ),
        "standings": _standing_signal(home, away),
        "home_away": _difference_signal(
            home.venue_points_per_game,
            away.venue_points_per_game,
            scale=3.0,
        ),
        "shots": _difference_signal(
            home.shots_average,
            away.shots_average,
            scale=8.0,
        ),
        "possession": _difference_signal(
            home.possession_average,
            away.possession_average,
            scale=20.0,
        ),
        "corners": _difference_signal(
            home.corners_average,
            away.corners_average,
            scale=6.0,
        ),
        "cards": _difference_signal(
            away.cards_average,
            home.cards_average,
            scale=4.0,
        ),
    }

    log_adjustment = sum(
        SIGNAL_WEIGHTS[name] * signal
        for name, signal in signals.items()
        if name in SIGNAL_WEIGHTS and signal is not None
    )
    expected_home_goals = _clamp_goal_rate(
        home_base * math.exp(log_adjustment)
    )
    expected_away_goals = _clamp_goal_rate(
        away_base * math.exp(-log_adjustment)
    )
    return expected_home_goals, expected_away_goals, signals


def _poisson_market_probabilities(
    expected_home_goals: float,
    expected_away_goals: float,
) -> KairosMarketProbabilities:
    if (
        not math.isfinite(expected_home_goals)
        or not math.isfinite(expected_away_goals)
        or expected_home_goals <= 0
        or expected_away_goals <= 0
    ):
        raise KairosDataError("invalid_poisson_rate")
    home_goal_probabilities = _poisson_distribution(expected_home_goals)
    away_goal_probabilities = _poisson_distribution(expected_away_goals)
    home_win = 0.0
    draw = 0.0
    away_win = 0.0
    over_2_5 = 0.0
    btts = 0.0
    for home_goals, home_probability in enumerate(
        home_goal_probabilities
    ):
        for away_goals, away_probability in enumerate(
            away_goal_probabilities
        ):
            joint = home_probability * away_probability
            if home_goals > away_goals:
                home_win += joint
            elif home_goals == away_goals:
                draw += joint
            else:
                away_win += joint
            if home_goals + away_goals >= 3:
                over_2_5 += joint
            if home_goals > 0 and away_goals > 0:
                btts += joint

    total = home_win + draw + away_win
    if not math.isfinite(total) or total <= 0:
        raise KairosDataError("invalid_probability_total")
    home_rounded = round(home_win / total, 6)
    draw_rounded = round(draw / total, 6)
    away_rounded = round(1.0 - home_rounded - draw_rounded, 6)
    over_rounded = round(over_2_5 / total, 6)
    under_rounded = round(1.0 - over_rounded, 6)
    return KairosMarketProbabilities(
        home_win=home_rounded,
        draw=draw_rounded,
        away_win=away_rounded,
        home_or_draw=round(home_rounded + draw_rounded, 6),
        away_or_draw=round(away_rounded + draw_rounded, 6),
        home_or_away=round(home_rounded + away_rounded, 6),
        over_2_5=over_rounded,
        under_2_5=under_rounded,
        btts=round(btts / total, 6),
    )


def _poisson_distribution(rate: float) -> list[float]:
    probabilities = [math.exp(-rate)]
    for goals in range(1, MAX_POISSON_GOALS + 1):
        probabilities.append(probabilities[-1] * rate / goals)
    return probabilities


def _confidence_score(
    data_quality_score: float,
    *,
    home_profile: TeamFeatureProfile,
    away_profile: TeamFeatureProfile,
    signals: dict[str, float | None],
) -> float:
    sample_sufficiency = (
        min(home_profile.result_sample_size / RECENT_WINDOW_MATCHES, 1.0)
        + min(away_profile.result_sample_size / RECENT_WINDOW_MATCHES, 1.0)
    ) / 2
    directional = [
        signal
        for signal in signals.values()
        if signal is not None and abs(signal) >= 0.05
    ]
    if directional:
        positive = sum(signal > 0 for signal in directional)
        negative = sum(signal < 0 for signal in directional)
        signal_consistency = max(positive, negative) / len(directional)
    else:
        signal_consistency = 0.5
    score = (
        data_quality_score * 0.50
        + sample_sufficiency * 15.0
        + signal_consistency * 5.0
    )
    return round(min(score, float(CONFIDENCE_SCORE_CAP)), 1)


def _reasons(
    home: TeamFeatureProfile,
    away: TeamFeatureProfile,
    *,
    signals: dict[str, float | None],
    expected_home_goals: float | None,
    expected_away_goals: float | None,
    sufficient_results: bool,
) -> list[KairosReason]:
    if not sufficient_results:
        return [
            KairosReason(
                code="RESULT_SAMPLE_BELOW_MINIMUM",
                message=(
                    f"Historique exploitable: {home.result_sample_size} "
                    f"match(s) pour {home.team_name} et "
                    f"{away.result_sample_size} pour {away.team_name}."
                ),
                direction="neutral",
            )
        ]

    assert expected_home_goals is not None
    assert expected_away_goals is not None
    reasons = [
        KairosReason(
            code="GOAL_RATE_BASELINE",
            message=(
                "La combinaison attaque/défense produit des taux de buts "
                f"de {expected_home_goals:.2f} à domicile et "
                f"{expected_away_goals:.2f} à l'extérieur."
            ),
            direction=_direction(
                expected_home_goals - expected_away_goals
            ),
        )
    ]
    reason_specs = (
        (
            "recent_form",
            "RECENT_FORM",
            home.form_points_per_game,
            away.form_points_per_game,
            "points par match récents",
        ),
        (
            "standings",
            "STANDINGS",
            float(home.standing_rank)
            if home.standing_rank is not None
            else None,
            float(away.standing_rank)
            if away.standing_rank is not None
            else None,
            "rang au classement",
        ),
        (
            "home_away",
            "HOME_AWAY_SPLIT",
            home.venue_points_per_game,
            away.venue_points_per_game,
            "points par match dans le contexte domicile/extérieur",
        ),
        (
            "shots",
            "SHOTS",
            home.shots_average,
            away.shots_average,
            "tirs moyens",
        ),
        (
            "possession",
            "POSSESSION",
            home.possession_average,
            away.possession_average,
            "possession moyenne",
        ),
        (
            "corners",
            "CORNERS",
            home.corners_average,
            away.corners_average,
            "corners moyens",
        ),
        (
            "cards",
            "CARDS",
            home.cards_average,
            away.cards_average,
            "charge moyenne de cartons",
        ),
    )
    for signal_name, code, home_value, away_value, label in reason_specs:
        signal = signals.get(signal_name)
        if signal is None or home_value is None or away_value is None:
            continue
        reasons.append(
            KairosReason(
                code=code,
                message=(
                    f"{label.capitalize()}: {home_value:.2f} pour "
                    f"{home.team_name}, {away_value:.2f} pour "
                    f"{away.team_name}."
                ),
                direction=_direction(signal),
            )
        )
    return reasons


def _base_warnings(
    availability: dict[str, KairosFeatureAvailability],
    *,
    home_profile: TeamFeatureProfile,
    away_profile: TeamFeatureProfile,
    target_is_stale: bool,
) -> list[KairosWarning]:
    warnings = [
        KairosWarning(
            code="UNCALIBRATED_BASELINE",
            message=(
                "La baseline B2.1 n'est pas encore calibrée ni validée "
                "hors échantillon."
            ),
            severity="warning",
        ),
        KairosWarning(
            code="ANALYSIS_ONLY_NO_BETTING",
            message=(
                "Sortie d'analyse sportive uniquement; les suggestions "
                "B2.2 n'utilisent ni cote, ni mise, ni exécution de pari."
            ),
            severity="info",
        ),
        KairosWarning(
            code="LIVE_AUTOMATION_DISABLED",
            message="Le calcul est pré-match; toute automatisation live est désactivée.",
            severity="info",
        ),
        KairosWarning(
            code="SINGLE_PROVIDER",
            message=(
                "Les observations proviennent d'un seul fournisseur et "
                "ne sont pas réconciliées avec une seconde source."
            ),
            severity="warning",
        ),
        KairosWarning(
            code="DRIFT_MONITORING_UNAVAILABLE",
            message=(
                "Aucune mesure de drift n'est disponible sans historique "
                "versionné d'analyses B2.1."
            ),
            severity="warning",
        ),
    ]
    for feature_name, feature_availability in availability.items():
        if (
            feature_name != "provenance"
            and feature_availability.coverage_score < 100
        ):
            warnings.append(
                KairosWarning(
                    code=f"PARTIAL_{feature_name.upper()}",
                    message=(
                        f"Couverture partielle pour {feature_name}: "
                        f"{feature_availability.coverage_score:.1f}%."
                    ),
                    severity="warning",
                )
            )
    if (
        home_profile.result_sample_size < RECENT_WINDOW_MATCHES
        or away_profile.result_sample_size < RECENT_WINDOW_MATCHES
    ):
        warnings.append(
            KairosWarning(
                code="SMALL_RECENT_SAMPLE",
                message=(
                    "La fenêtre récente de cinq résultats n'est pas "
                    "complète pour les deux équipes."
                ),
                severity="warning",
            )
        )
    if target_is_stale:
        warnings.append(
            KairosWarning(
                code="STALE_TARGET_DATA",
                message=(
                    "L'observation du match cible dépasse le TTL de "
                    "fraîcheur configuré."
                ),
                severity="warning",
            )
        )
    return warnings


def _freshness(
    dataset: KairosMatchDataset,
    *,
    threshold_minutes: int,
) -> KairosDataFreshness:
    sources = dataset.source_observations()
    target_age_minutes = max(
        0,
        int(
            (
                dataset.as_of - dataset.target.source.fetched_at
            ).total_seconds()
            // 60
        ),
    )
    return KairosDataFreshness(
        as_of=dataset.as_of,
        max_available_at=max(source.available_at for source in sources),
        target_fetched_at=dataset.target.source.fetched_at,
        target_age_minutes=target_age_minutes,
        status=(
            "fresh"
            if target_age_minutes <= threshold_minutes
            else "stale"
        ),
        threshold_minutes=threshold_minutes,
    )


def _feature_snapshot_hash(
    dataset: KairosMatchDataset,
    *,
    home_profile: TeamFeatureProfile,
    away_profile: TeamFeatureProfile,
    availability: dict[str, KairosFeatureAvailability],
) -> str:
    payload = {
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "model_version": MODEL_VERSION,
        "as_of": dataset.as_of.isoformat(),
        "target": {
            "provider_match_id": dataset.target.provider_match_id,
            "provider_competition_id": (
                dataset.target.provider_competition_id
            ),
            "season": dataset.target.season,
            "kickoff_at": dataset.target.kickoff_at.isoformat(),
            "home_team_provider_id": (
                dataset.target.home_team_provider_id
            ),
            "away_team_provider_id": (
                dataset.target.away_team_provider_id
            ),
        },
        "home_profile": asdict(home_profile),
        "away_profile": asdict(away_profile),
        "availability": {
            name: value.model_dump(mode="json")
            for name, value in sorted(availability.items())
        },
        "sources": [
            {
                "id": source.observation_id,
                "provider": source.provider,
                "provider_event_id": source.provider_event_id,
                "observed_at": source.observed_at.isoformat(),
                "available_at": source.available_at.isoformat(),
                "fetched_at": source.fetched_at.isoformat(),
                "created_at": source.created_at.isoformat(),
                "source_version": source.source_version,
                "quality_flags": list(source.quality_flags),
                "raw_hash": source.raw_hash,
                "freshness_status": source.freshness_status,
            }
            for source in dataset.source_observations()
        ],
    }
    return _sha256_json(payload)


def _immutable_analysis_hash(**payload: Any) -> str:
    return _sha256_json(payload)


def _sha256_json(payload: Any) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def _statistic_index(
    statistics: tuple[StatisticObservation, ...],
) -> dict[tuple[int, int], dict[str, float]]:
    output: dict[tuple[int, int], dict[str, float]] = defaultdict(dict)
    for statistic in statistics:
        metric_name = _metric_name(statistic.statistic_type)
        value = _numeric_value(statistic.statistic_value)
        if (
            metric_name is not None
            and value is not None
            and _metric_value_is_valid(metric_name, value)
        ):
            output[
                (statistic.provider_match_id, statistic.provider_team_id)
            ][metric_name] = value
    return dict(output)


def _card_event_index(
    events: tuple[EventObservation, ...],
) -> dict[tuple[int, int], float]:
    output: dict[tuple[int, int], float] = defaultdict(float)
    for event in events:
        if event.provider_team_id is None:
            continue
        detail = _normalized_text(event.detail or "")
        if "yellow" in detail:
            value = 1.0
        elif "red" in detail:
            value = 2.0
        else:
            continue
        output[(event.provider_match_id, event.provider_team_id)] += value
    return dict(output)


def _metric_name(statistic_type: str) -> str | None:
    normalized = _normalized_text(statistic_type)
    for metric_name, aliases in STATISTIC_ALIASES.items():
        if normalized in aliases:
            return metric_name
    return None


def _normalized_text(value: str) -> str:
    without_accents = "".join(
        character
        for character in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", without_accents).strip().lower()


def _numeric_value(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        if isinstance(value, int | float):
            parsed = float(value)
        elif isinstance(value, str):
            if len(value) > 64:
                return None
            normalized = value.strip().replace("%", "").replace(",", ".")
            parsed = float(normalized)
        else:
            return None
    except (OverflowError, TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _metric_value_is_valid(metric_name: str, value: float) -> bool:
    maximum = (
        MAX_POSSESSION_VALUE
        if metric_name == "possession"
        else MAX_COUNT_STATISTIC_VALUE
    )
    return 0.0 <= value <= maximum


def _cards_value(
    statistics: dict[str, float],
    event_value: float | None,
) -> float | None:
    yellow = statistics.get("yellow_cards")
    red = statistics.get("red_cards")
    if yellow is not None and red is not None:
        return yellow + 2.0 * red
    return event_value


def _first_value(
    values: dict[str, float],
    names: tuple[str, ...],
) -> float | None:
    for name in names:
        if name in values:
            return values[name]
    return None


def _points_for(score: tuple[int, int]) -> float:
    goals_for, goals_against = score
    if goals_for > goals_against:
        return 3.0
    if goals_for == goals_against:
        return 1.0
    return 0.0


def _average(values: list[float]) -> float | None:
    finite_values = [value for value in values if math.isfinite(value)]
    return (
        math.fsum(finite_values) / len(finite_values)
        if finite_values
        else None
    )


def _required_average(values: tuple[float | None, ...]) -> float:
    available = [
        value
        for value in values
        if value is not None and math.isfinite(value)
    ]
    if not available:
        raise KairosDataError("goal_features_missing")
    return math.fsum(available) / len(available)


def _difference_signal(
    home_value: float | None,
    away_value: float | None,
    *,
    scale: float,
) -> float | None:
    if home_value is None or away_value is None:
        return None
    return _clamp((home_value - away_value) / scale)


def _standing_signal(
    home: TeamFeatureProfile,
    away: TeamFeatureProfile,
) -> float | None:
    parts: list[float] = []
    if home.standing_rank is not None and away.standing_rank is not None:
        parts.append(
            _clamp(
                (away.standing_rank - home.standing_rank) / 10.0
            )
        )
    points_signal = _difference_signal(
        home.standing_points_per_game,
        away.standing_points_per_game,
        scale=3.0,
    )
    if points_signal is not None:
        parts.append(points_signal)
    return sum(parts) / len(parts) if parts else None


def _clamp(value: float, minimum: float = -1.0, maximum: float = 1.0) -> float:
    if not math.isfinite(value):
        raise KairosDataError("non_finite_feature_value")
    return max(minimum, min(value, maximum))


def _clamp_goal_rate(value: float) -> float:
    if not math.isfinite(value):
        raise KairosDataError("non_finite_goal_rate")
    return max(0.05, min(value, 4.5))


def _direction(value: float, neutral_threshold: float = 0.05) -> str:
    if value > neutral_threshold:
        return "home"
    if value < -neutral_threshold:
        return "away"
    return "neutral"


def _team_summary(profile: TeamFeatureProfile) -> KairosTeamSummary:
    return KairosTeamSummary(
        provider_team_id=profile.team_id,
        team_name=profile.team_name,
        recent_result_sample_size=profile.result_sample_size,
        venue_sample_size=profile.venue_sample_size,
        form_points_per_game=_rounded(profile.form_points_per_game),
        goals_for_average=_rounded(profile.goals_for_average),
        goals_against_average=_rounded(profile.goals_against_average),
        standing_rank=profile.standing_rank,
    )


def _rounded(value: float | None) -> float | None:
    return round(value, 3) if value is not None else None


__all__ = [
    "CONFIDENCE_SCORE_CAP",
    "DEFAULT_FEATURE_TTL_MINUTES",
    "FEATURE_SCHEMA_VERSION",
    "MINIMUM_RESULTS_PER_TEAM",
    "MODEL_VERSION",
    "RECENT_WINDOW_MATCHES",
    "KairosAnalysisService",
    "build_kairos_methodology",
]
