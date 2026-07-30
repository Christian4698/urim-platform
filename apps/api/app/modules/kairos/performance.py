from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Final

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.db import models
from app.modules.kairos.opportunity_config import OPPORTUNITY_MARKET_GROUPS
from app.modules.kairos.schemas import (
    KairosPerformanceResponse,
    KairosPerformanceSegment,
)
from app.modules.sports_data.provider import API_FOOTBALL_PROVIDER


MINIMUM_PERFORMANCE_SAMPLE: Final = 30
MAX_COMPETITION_SEGMENTS: Final = 100
VALID_OUTCOMES: Final = ("SUCCESS", "FAILURE")
MARKET_LABELS: Final = {
    "FIRST_HALF_MORE_GOALS": "Plus de buts en première période",
    "SECOND_HALF_MORE_GOALS": "Plus de buts en seconde période",
    "EQUAL_HALF_GOALS": "Autant de buts dans chaque période",
    "FIRST_HALF_OVER_0_5": "Première période · au moins un but",
    "SECOND_HALF_OVER_0_5": "Seconde période · au moins un but",
    "SECOND_HALF_OVER_1_5": "Seconde période · au moins deux buts",
    "HOME_OR_DRAW": "Domicile ou nul",
    "AWAY_OR_DRAW": "Extérieur ou nul",
    "HOME_OR_AWAY": "Sans nul",
}


class KairosPerformanceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def report(self, *, generated_at: datetime) -> KairosPerformanceResponse:
        if (
            generated_at.tzinfo is None
            or generated_at.tzinfo.utcoffset(generated_at) is None
        ):
            raise ValueError("generated_at must be timezone-aware.")

        journal = models.kairos_analysis_journal
        resolution = models.kairos_analysis_resolutions
        base = journal.outerjoin(
            resolution,
            resolution.c.analysis_id == journal.c.analysis_id,
        )
        overall = self.session.execute(
            sa.select(
                sa.func.count(journal.c.analysis_id).label(
                    "total_snapshots"
                ),
                _resolved_count(resolution).label("resolved_sample_size"),
                _void_count(resolution).label("void_count"),
                _unresolved_count(resolution).label("unresolved_count"),
                _success_count(resolution).label("success_count"),
                sa.func.max(resolution.c.resolved_at).label(
                    "last_resolution_at"
                ),
            ).select_from(base)
        ).mappings().one()

        market_rows = self._segments(
            from_clause=base,
            key_expression=journal.c.market,
            label_expression=journal.c.market,
        )
        markets_by_key = {segment.key: segment for segment in market_rows}
        performance_by_market = [
            markets_by_key.get(market)
            or _empty_segment(market, MARKET_LABELS[market])
            for market in OPPORTUNITY_MARKET_GROUPS
        ]

        match_table = models.api_football_matches
        latest_match = (
            sa.select(match_table.c.provider_competition_id)
            .where(
                match_table.c.provider == API_FOOTBALL_PROVIDER,
                match_table.c.provider_match_id
                == journal.c.provider_match_id,
                match_table.c.available_at <= journal.c.analysis_time,
                match_table.c.fetched_at <= journal.c.analysis_time,
                match_table.c.created_at <= journal.c.analysis_time,
            )
            .order_by(
                match_table.c.available_at.desc(),
                match_table.c.fetched_at.desc(),
                match_table.c.created_at.desc(),
            )
            .limit(1)
            .correlate(journal)
            .lateral("latest_match_as_of_analysis")
        )
        competition_key = sa.func.coalesce(
            sa.cast(
                latest_match.c.provider_competition_id,
                sa.String(),
            ),
            "unknown",
        )
        competition_table = models.api_football_competitions
        latest_competition = (
            sa.select(competition_table.c.name)
            .where(
                competition_table.c.provider == API_FOOTBALL_PROVIDER,
                competition_table.c.provider_competition_id
                == latest_match.c.provider_competition_id,
                competition_table.c.available_at
                <= journal.c.analysis_time,
                competition_table.c.fetched_at
                <= journal.c.analysis_time,
                competition_table.c.created_at
                <= journal.c.analysis_time,
            )
            .order_by(
                competition_table.c.available_at.desc(),
                competition_table.c.fetched_at.desc(),
                competition_table.c.created_at.desc(),
            )
            .limit(1)
            .correlate(journal, latest_match)
            .lateral("latest_competition_as_of_analysis")
        )
        competition_label = sa.func.coalesce(
            latest_competition.c.name,
            "Compétition inconnue",
        )
        competition_base = (
            base.outerjoin(latest_match, sa.true())
            .outerjoin(latest_competition, sa.true())
        )
        performance_by_competition = self._segments(
            from_clause=competition_base,
            key_expression=competition_key,
            label_expression=competition_label,
            limit=MAX_COMPETITION_SEGMENTS,
        )

        probability_key = sa.case(
            (
                journal.c.estimated_probability < Decimal("0.70"),
                "below_0_70",
            ),
            (
                journal.c.estimated_probability < Decimal("0.75"),
                "0_70_0_74",
            ),
            (
                journal.c.estimated_probability < Decimal("0.80"),
                "0_75_0_79",
            ),
            else_="0_80_plus",
        )
        probability_label = sa.case(
            (
                journal.c.estimated_probability < Decimal("0.70"),
                "Sous le gate historique",
            ),
            (
                journal.c.estimated_probability < Decimal("0.75"),
                "70 % à 74,9 %",
            ),
            (
                journal.c.estimated_probability < Decimal("0.80"),
                "75 % à 79,9 %",
            ),
            else_="80 % et plus",
        )
        probability_segments = self._segments(
            from_clause=base,
            key_expression=probability_key,
            label_expression=probability_label,
        )

        quality_key = sa.case(
            (
                journal.c.data_quality_score < Decimal("75"),
                "quality_65_74",
            ),
            (
                journal.c.data_quality_score < Decimal("85"),
                "quality_75_84",
            ),
            else_="quality_85_plus",
        )
        quality_label = sa.case(
            (
                journal.c.data_quality_score < Decimal("75"),
                "Qualité 65 à 74",
            ),
            (
                journal.c.data_quality_score < Decimal("85"),
                "Qualité 75 à 84",
            ),
            else_="Qualité 85 et plus",
        )
        quality_segments = self._segments(
            from_clause=base,
            key_expression=quality_key,
            label_expression=quality_label,
        )
        calibration_key = sa.case(
            (
                journal.c.estimated_probability < Decimal("0.70"),
                "calibration_below_0_70",
            ),
            (
                journal.c.estimated_probability < Decimal("0.80"),
                "calibration_0_70_0_79",
            ),
            (
                journal.c.estimated_probability < Decimal("0.90"),
                "calibration_0_80_0_89",
            ),
            else_="calibration_0_90_1_00",
        )
        calibration_label = sa.case(
            (
                journal.c.estimated_probability < Decimal("0.70"),
                "Calibration sous 70 %",
            ),
            (
                journal.c.estimated_probability < Decimal("0.80"),
                "Calibration 70 % à 79,9 %",
            ),
            (
                journal.c.estimated_probability < Decimal("0.90"),
                "Calibration 80 % à 89,9 %",
            ),
            else_="Calibration 90 % à 100 %",
        )
        calibration_segments = self._segments(
            from_clause=base,
            key_expression=calibration_key,
            label_expression=calibration_label,
        )

        resolved_sample_size = int(
            overall["resolved_sample_size"] or 0
        )
        success_count = int(overall["success_count"] or 0)
        return KairosPerformanceResponse(
            generated_at=generated_at,
            total_snapshots=int(overall["total_snapshots"] or 0),
            resolved=resolved_sample_size,
            unresolved=int(overall["unresolved_count"] or 0),
            void=int(overall["void_count"] or 0),
            resolved_sample_size=resolved_sample_size,
            success_count=success_count,
            observed_hit_rate=_observed_rate(
                success_count,
                resolved_sample_size,
            ),
            sample_status=_sample_status(resolved_sample_size),
            performance_by_market=performance_by_market,
            performance_by_competition=performance_by_competition,
            performance_by_probability_band=probability_segments,
            performance_by_quality_level=quality_segments,
            calibration_buckets=calibration_segments,
            last_resolution_at=overall["last_resolution_at"],
            last_report_generated_at=generated_at,
            warnings=[
                (
                    "Les probabilités estimées restent distinctes des taux "
                    "observés et le moteur n'est pas calibré."
                ),
                (
                    "VOID et unresolved sont exclus de tous les taux "
                    "observés."
                ),
                (
                    "Échantillon insuffisant : aucune conclusion de "
                    "performance sous 30 résolutions valides."
                    if resolved_sample_size < MINIMUM_PERFORMANCE_SAMPLE
                    else (
                        "Échantillon descriptif disponible ; il ne constitue "
                        "ni une promesse ni une preuve de performance future."
                    )
                ),
            ],
        )

    def _segments(
        self,
        *,
        from_clause: sa.FromClause,
        key_expression: sa.ColumnElement,
        label_expression: sa.ColumnElement,
        limit: int | None = None,
    ) -> list[KairosPerformanceSegment]:
        resolution = models.kairos_analysis_resolutions
        journal = models.kairos_analysis_journal
        statement = (
            sa.select(
                key_expression.label("segment_key"),
                label_expression.label("segment_label"),
                sa.func.count(journal.c.analysis_id).label(
                    "total_snapshots"
                ),
                _resolved_count(resolution).label("resolved_sample_size"),
                _void_count(resolution).label("void_count"),
                _unresolved_count(resolution).label("unresolved_count"),
                _success_count(resolution).label("success_count"),
                sa.func.avg(journal.c.estimated_probability)
                .filter(resolution.c.outcome.in_(VALID_OUTCOMES))
                .label("estimated_probability_mean"),
            )
            .select_from(from_clause)
            .group_by(key_expression, label_expression)
            .order_by(
                sa.func.count(journal.c.analysis_id).desc(),
                key_expression,
            )
        )
        if limit is not None:
            statement = statement.limit(limit)
        return [
            _segment_from_row(row)
            for row in self.session.execute(statement).mappings()
        ]


def _resolved_count(
    resolution: sa.Table,
) -> sa.ColumnElement:
    return sa.func.count(resolution.c.analysis_id).filter(
        resolution.c.outcome.in_(VALID_OUTCOMES)
    )


def _void_count(resolution: sa.Table) -> sa.ColumnElement:
    return sa.func.count(resolution.c.analysis_id).filter(
        resolution.c.outcome == "VOID"
    )


def _unresolved_count(resolution: sa.Table) -> sa.ColumnElement:
    return sa.func.count().filter(resolution.c.analysis_id.is_(None))


def _success_count(resolution: sa.Table) -> sa.ColumnElement:
    return sa.func.count(resolution.c.analysis_id).filter(
        resolution.c.outcome == "SUCCESS"
    )


def _segment_from_row(row: sa.RowMapping) -> KairosPerformanceSegment:
    resolved_sample_size = int(row["resolved_sample_size"] or 0)
    success_count = int(row["success_count"] or 0)
    probability_mean = row["estimated_probability_mean"]
    return KairosPerformanceSegment(
        key=str(row["segment_key"]),
        label=str(row["segment_label"]),
        total_snapshots=int(row["total_snapshots"] or 0),
        resolved_sample_size=resolved_sample_size,
        success_count=success_count,
        void_count=int(row["void_count"] or 0),
        unresolved_count=int(row["unresolved_count"] or 0),
        observed_hit_rate=_observed_rate(
            success_count,
            resolved_sample_size,
        ),
        estimated_probability_mean=(
            round(float(probability_mean), 4)
            if probability_mean is not None
            else None
        ),
        sample_status=_sample_status(resolved_sample_size),
    )


def _empty_segment(key: str, label: str) -> KairosPerformanceSegment:
    return KairosPerformanceSegment(
        key=key,
        label=label,
        total_snapshots=0,
        resolved_sample_size=0,
        success_count=0,
        void_count=0,
        unresolved_count=0,
        observed_hit_rate=None,
        estimated_probability_mean=None,
        sample_status="no_sample",
    )


def _observed_rate(success_count: int, sample_size: int) -> float | None:
    return round(success_count / sample_size, 4) if sample_size else None


def _sample_status(
    sample_size: int,
) -> str:
    if sample_size == 0:
        return "no_sample"
    if sample_size < MINIMUM_PERFORMANCE_SAMPLE:
        return "insufficient_sample"
    return "descriptive_sample_available"


__all__ = [
    "KairosPerformanceRepository",
    "MARKET_LABELS",
    "MINIMUM_PERFORMANCE_SAMPLE",
]
