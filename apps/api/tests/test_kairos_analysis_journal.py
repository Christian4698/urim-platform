from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from app.db import models
from app.modules.kairos import journal as journal_module
from app.modules.kairos.journal import (
    KairosJournalRepository,
    evaluate_market_outcome,
)


class _EmptyResult:
    def mappings(self) -> tuple[object, ...]:
        return ()


class _RecordingSession:
    def __init__(self) -> None:
        self.statement = None

    def execute(self, statement):
        self.statement = statement
        return _EmptyResult()


def test_market_resolution_uses_only_real_ht_and_ft_scores() -> None:
    scores = {
        "halftime_home": 1,
        "halftime_away": 0,
        "fulltime_home": 2,
        "fulltime_away": 2,
    }

    assert evaluate_market_outcome(
        "FIRST_HALF_MORE_GOALS", **scores
    ) == "FAILURE"
    assert evaluate_market_outcome(
        "SECOND_HALF_MORE_GOALS", **scores
    ) == "SUCCESS"
    assert evaluate_market_outcome(
        "FIRST_HALF_OVER_0_5", **scores
    ) == "SUCCESS"
    assert evaluate_market_outcome(
        "SECOND_HALF_OVER_1_5", **scores
    ) == "SUCCESS"
    assert evaluate_market_outcome("HOME_OR_DRAW", **scores) == "SUCCESS"
    assert evaluate_market_outcome("HOME_OR_AWAY", **scores) == "FAILURE"


def test_missing_or_inconsistent_scores_resolve_void_not_failure() -> None:
    assert evaluate_market_outcome(
        "SECOND_HALF_OVER_0_5",
        halftime_home=None,
        halftime_away=None,
        fulltime_home=2,
        fulltime_away=1,
    ) == "VOID"
    assert evaluate_market_outcome(
        "SECOND_HALF_OVER_0_5",
        halftime_home=3,
        halftime_away=2,
        fulltime_home=2,
        fulltime_away=1,
    ) == "VOID"
    assert evaluate_market_outcome(
        "UNSUPPORTED_MARKET",
        halftime_home=0,
        halftime_away=0,
        fulltime_home=0,
        fulltime_away=0,
    ) == "VOID"


def test_observed_metrics_query_excludes_unresolved_and_void_rows() -> None:
    session = _RecordingSession()
    repository = KairosJournalRepository(cast(Session, session))

    assert repository.resolved_metrics() == {}
    compiled = session.statement.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    sql = str(compiled).upper()

    assert "JOIN KAIROS_ANALYSIS_RESOLUTIONS" in sql
    assert "SUCCESS" in sql
    assert "FAILURE" in sql
    assert "VOID" not in sql


def test_resolution_ranks_all_states_before_requiring_completed() -> None:
    session = _RecordingSession()
    repository = KairosJournalRepository(cast(Session, session))

    summary = repository.resolve_completed(
        as_of=datetime(2026, 7, 28, 18, tzinfo=UTC),
    )

    assert summary.received == 0
    compiled = session.statement.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    sql = str(compiled).upper()
    assert sql.count("STATUS_SHORT IN") == 1


def test_resolution_voids_result_that_breaks_pre_match_timeline() -> None:
    analysis_time = datetime(2026, 7, 28, 10, tzinfo=UTC)
    journal_kickoff = datetime(2026, 7, 28, 18, tzinfo=UTC)
    value = journal_module._resolution_value(
        cast(
            object,
            {
                "analysis_id": uuid4(),
                "provider_match_id": 999,
                "market": "SECOND_HALF_OVER_0_5",
                "analysis_time": analysis_time,
                "kickoff_at": journal_kickoff,
                "match_kickoff_at": datetime(
                    2026,
                    7,
                    28,
                    9,
                    tzinfo=UTC,
                ),
                "match_available_at": datetime(
                    2026,
                    7,
                    28,
                    12,
                    tzinfo=UTC,
                ),
                "match_status_short": "FT",
                "score_halftime_home": 0,
                "score_halftime_away": 0,
                "score_fulltime_home": 1,
                "score_fulltime_away": 0,
                "match_provider_event_id": "fixture:999",
                "match_source_version": "football-v3-test",
                "match_raw_hash": "a" * 64,
            },
        ),
        as_of=datetime(2026, 7, 28, 20, tzinfo=UTC),
    )

    assert value["outcome"] == "VOID"
    assert value["outcome_payload"]["temporal_mismatch"] is True


def test_journal_tables_are_distinct_from_official_predictions() -> None:
    journal_unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in models.kairos_analysis_journal.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }
    resolution_unique_columns = {
        tuple(column.name for column in constraint.columns)
        for constraint in models.kairos_analysis_resolutions.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    }

    assert ("analysis_id",) in journal_unique_columns
    assert ("immutable_hash",) in journal_unique_columns
    assert ("analysis_id",) in resolution_unique_columns
    assert models.kairos_analysis_journal is not models.predictions


def test_migration_installs_append_only_guards_and_rls() -> None:
    migration = Path(
        "alembic/versions/"
        "202607280001_kairos_b2_4_analysis_journal.py"
    ).read_text(encoding="utf-8")

    assert "prevent_append_only_mutation" in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "BEFORE UPDATE OR DELETE" in migration
    assert "analysis_time <= created_at AND created_at < kickoff_at" in migration
    assert "enforce_kairos_analysis_resolution_integrity" in migration
    assert "BEFORE INSERT ON kairos_analysis_resolutions" in migration
    assert "resolution identity does not match journal" in migration
    assert "resolution predates kickoff" in migration
    assert "non-void resolution outcome is incoherent" in migration
    assert "authenticated" in migration
