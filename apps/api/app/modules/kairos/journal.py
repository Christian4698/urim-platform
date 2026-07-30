from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from typing import Any, Final, Literal
from uuid import NAMESPACE_DNS, uuid5

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db import models
from app.modules.kairos.models import API_FOOTBALL_PROVIDER
from app.modules.kairos.repository import (
    COMPLETED_MATCH_STATUSES,
    build_latest_as_of_subquery,
)
from app.modules.kairos.schemas import (
    KairosMatchOpportunity,
    KairosOpportunityCandidate,
)


JOURNAL_NAMESPACE: Final = uuid5(NAMESPACE_DNS, "urim.kairos.journal.b2.4")
RESOLUTION_LIMIT: Final = 200
ResolutionOutcome = Literal["SUCCESS", "FAILURE", "VOID"]


@dataclass(frozen=True, slots=True)
class JournalWriteSummary:
    received: int
    inserted: int
    duplicate: int


@dataclass(frozen=True, slots=True)
class ResolvedMetric:
    resolved_sample_size: int
    success_count: int
    observed_hit_rate: float | None


class KairosJournalRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def append_opportunity(
        self,
        opportunity: KairosMatchOpportunity,
        *,
        analysis_time: datetime,
    ) -> JournalWriteSummary:
        if opportunity.safety_decision != "ANALYSIS_ALLOWED":
            return JournalWriteSummary(received=0, inserted=0, duplicate=0)
        if analysis_time.tzinfo is None or analysis_time >= opportunity.kickoff_at:
            raise ValueError("Journal snapshots must be timezone-aware pre-match.")
        candidates = (
            [opportunity.primary_analysis]
            if opportunity.primary_analysis is not None
            else []
        )
        candidates.extend(opportunity.alternative_analyses)
        values = [
            _journal_value(
                opportunity,
                candidate,
                analysis_time=analysis_time,
            )
            for candidate in candidates
        ]
        if not values:
            return JournalWriteSummary(received=0, inserted=0, duplicate=0)
        statement = (
            pg_insert(models.kairos_analysis_journal)
            .values(values)
            .on_conflict_do_nothing()
            .returning(models.kairos_analysis_journal.c.id)
        )
        inserted = len(self.session.execute(statement).scalars().all())
        return JournalWriteSummary(
            received=len(values),
            inserted=inserted,
            duplicate=len(values) - inserted,
        )

    def resolve_completed(
        self,
        *,
        as_of: datetime,
        starts_at: datetime | None = None,
        ends_at: datetime | None = None,
        limit: int = RESOLUTION_LIMIT,
    ) -> JournalWriteSummary:
        if as_of.tzinfo is None:
            raise ValueError("Resolution as_of must be timezone-aware.")
        if limit < 1 or limit > RESOLUTION_LIMIT:
            raise ValueError("Resolution limit is outside the safe range.")
        match_table = models.api_football_matches
        latest_match = build_latest_as_of_subquery(
            match_table,
            (match_table.c.provider_match_id,),
            as_of=as_of,
        )
        journal = models.kairos_analysis_journal
        resolution = models.kairos_analysis_resolutions
        statement = (
            sa.select(
                journal,
                latest_match.c.kickoff_at.label("match_kickoff_at"),
                latest_match.c.status_short.label("match_status_short"),
                latest_match.c.score_halftime_home,
                latest_match.c.score_halftime_away,
                latest_match.c.score_fulltime_home,
                latest_match.c.score_fulltime_away,
                latest_match.c.available_at.label(
                    "match_available_at"
                ),
                latest_match.c.provider_event_id.label(
                    "match_provider_event_id"
                ),
                latest_match.c.source_version.label(
                    "match_source_version"
                ),
                latest_match.c.raw_hash.label("match_raw_hash"),
            )
            .join(
                latest_match,
                sa.and_(
                    latest_match.c.provider_match_id
                    == journal.c.provider_match_id,
                    latest_match.c.observation_rank == 1,
                ),
            )
            .outerjoin(
                resolution,
                resolution.c.analysis_id == journal.c.analysis_id,
            )
            .where(
                resolution.c.analysis_id.is_(None),
                journal.c.kickoff_at < as_of,
                latest_match.c.status_short.in_(COMPLETED_MATCH_STATUSES),
            )
            .order_by(journal.c.kickoff_at, journal.c.analysis_id)
            .limit(limit)
        )
        if starts_at is not None:
            statement = statement.where(journal.c.kickoff_at >= starts_at)
        if ends_at is not None:
            statement = statement.where(journal.c.kickoff_at < ends_at)
        rows = self.session.execute(statement).mappings()
        values = [
            _resolution_value(row, as_of=as_of)
            for row in rows
        ]
        if not values:
            return JournalWriteSummary(received=0, inserted=0, duplicate=0)
        insert_statement = (
            pg_insert(resolution)
            .values(values)
            .on_conflict_do_nothing()
            .returning(resolution.c.id)
        )
        inserted = len(
            self.session.execute(insert_statement).scalars().all()
        )
        return JournalWriteSummary(
            received=len(values),
            inserted=inserted,
            duplicate=len(values) - inserted,
        )

    def resolved_metrics(self) -> dict[str, ResolvedMetric]:
        journal = models.kairos_analysis_journal
        resolution = models.kairos_analysis_resolutions
        statement = (
            sa.select(
                journal.c.market,
                sa.func.count().label("resolved_sample_size"),
                sa.func.sum(
                    sa.case((resolution.c.outcome == "SUCCESS", 1), else_=0)
                ).label("success_count"),
            )
            .join(
                resolution,
                resolution.c.analysis_id == journal.c.analysis_id,
            )
            .where(resolution.c.outcome.in_(("SUCCESS", "FAILURE")))
            .group_by(journal.c.market)
            .order_by(journal.c.market)
        )
        output: dict[str, ResolvedMetric] = {}
        for row in self.session.execute(statement).mappings():
            sample_size = int(row["resolved_sample_size"])
            success_count = int(row["success_count"] or 0)
            output[str(row["market"])] = ResolvedMetric(
                resolved_sample_size=sample_size,
                success_count=success_count,
                observed_hit_rate=(
                    round(success_count / sample_size, 4)
                    if sample_size
                    else None
                ),
            )
        return output


def evaluate_market_outcome(
    market: str,
    *,
    halftime_home: int | None,
    halftime_away: int | None,
    fulltime_home: int | None,
    fulltime_away: int | None,
) -> ResolutionOutcome:
    values = (
        halftime_home,
        halftime_away,
        fulltime_home,
        fulltime_away,
    )
    if any(
        value is not None
        and (isinstance(value, bool) or value < 0 or value > 100)
        for value in values
    ):
        return "VOID"
    if fulltime_home is None or fulltime_away is None:
        return "VOID"
    if market == "HOME_OR_DRAW":
        return "SUCCESS" if fulltime_home >= fulltime_away else "FAILURE"
    if market == "AWAY_OR_DRAW":
        return "SUCCESS" if fulltime_away >= fulltime_home else "FAILURE"
    if market == "HOME_OR_AWAY":
        return "SUCCESS" if fulltime_home != fulltime_away else "FAILURE"
    if halftime_home is None or halftime_away is None:
        return "VOID"
    first_half = halftime_home + halftime_away
    full_match = fulltime_home + fulltime_away
    if first_half > full_match:
        return "VOID"
    second_half = full_match - first_half
    conditions = {
        "FIRST_HALF_MORE_GOALS": first_half > second_half,
        "SECOND_HALF_MORE_GOALS": second_half > first_half,
        "EQUAL_HALF_GOALS": first_half == second_half,
        "FIRST_HALF_OVER_0_5": first_half >= 1,
        "SECOND_HALF_OVER_0_5": second_half >= 1,
        "SECOND_HALF_OVER_1_5": second_half >= 2,
    }
    if market not in conditions:
        return "VOID"
    return "SUCCESS" if conditions[market] else "FAILURE"


def _journal_value(
    opportunity: KairosMatchOpportunity,
    candidate: KairosOpportunityCandidate,
    *,
    analysis_time: datetime,
) -> dict[str, Any]:
    analysis_id = uuid5(
        JOURNAL_NAMESPACE,
        (
            f"{opportunity.provider_match_id}:{candidate.market}:"
            f"{candidate.analysis_hash}"
        ),
    )
    payload = candidate.model_dump(mode="json")
    immutable_hash = _hash(
        {
            "analysis_id": str(analysis_id),
            "analysis_time": analysis_time.isoformat(),
            "kickoff_at": opportunity.kickoff_at.isoformat(),
            "payload": payload,
        }
    )
    return {
        "analysis_id": analysis_id,
        "provider_match_id": opportunity.provider_match_id,
        "kickoff_at": opportunity.kickoff_at,
        "analysis_time": analysis_time,
        "model_version": (
            "kairos_core_b2_2_v1"
            if candidate.market
            in {"HOME_OR_DRAW", "AWAY_OR_DRAW", "HOME_OR_AWAY"}
            else "kairos_half_time_b2_4_v1"
        ),
        "market": candidate.market,
        "estimated_probability": candidate.estimated_probability,
        "data_quality_score": candidate.data_quality_score,
        "technical_confidence_score": (
            candidate.technical_confidence_score
        ),
        "sample_size": candidate.sample_size,
        "safety_decision": opportunity.safety_decision,
        "analysis_hash": candidate.analysis_hash,
        "analysis_payload": payload,
        "immutable_hash": immutable_hash,
    }


def _resolution_value(
    row: sa.RowMapping,
    *,
    as_of: datetime,
) -> dict[str, Any]:
    match_kickoff_at = row["match_kickoff_at"]
    match_available_at = row["match_available_at"]
    temporal_mismatch = (
        match_kickoff_at <= row["analysis_time"]
        or match_available_at < row["kickoff_at"]
    )
    outcome: ResolutionOutcome = (
        "VOID"
        if temporal_mismatch
        else evaluate_market_outcome(
            str(row["market"]),
            halftime_home=_optional_int(row.get("score_halftime_home")),
            halftime_away=_optional_int(row.get("score_halftime_away")),
            fulltime_home=_optional_int(row.get("score_fulltime_home")),
            fulltime_away=_optional_int(row.get("score_fulltime_away")),
        )
    )
    payload = {
        "match_kickoff_at": match_kickoff_at.isoformat(),
        "score_halftime_home": row.get("score_halftime_home"),
        "score_halftime_away": row.get("score_halftime_away"),
        "score_fulltime_home": row.get("score_fulltime_home"),
        "score_fulltime_away": row.get("score_fulltime_away"),
        "status_short": row.get("match_status_short"),
        "temporal_mismatch": temporal_mismatch,
    }
    immutable_hash = _hash(
        {
            "analysis_id": str(row["analysis_id"]),
            "outcome": outcome,
            "outcome_available_at": match_available_at.isoformat(),
            "payload": payload,
            "raw_hash": row["match_raw_hash"],
        }
    )
    return {
        "analysis_id": row["analysis_id"],
        "provider_match_id": row["provider_match_id"],
        "market": row["market"],
        "outcome": outcome,
        "outcome_available_at": match_available_at,
        "resolved_at": as_of,
        "provider": API_FOOTBALL_PROVIDER,
        "provider_event_id": row["match_provider_event_id"],
        "source_version": row["match_source_version"],
        "raw_hash": row["match_raw_hash"],
        "outcome_payload": payload,
        "immutable_hash": immutable_hash,
    }


def _hash(value: dict[str, Any]) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _optional_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    return int(value)


__all__ = [
    "JournalWriteSummary",
    "KairosJournalRepository",
    "ResolvedMetric",
    "evaluate_market_outcome",
]
