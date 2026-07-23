from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Final
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.db import models
from app.modules.sports_data.normalization import NormalizationResult
from app.modules.sports_data.provider import API_FOOTBALL_PROVIDER

RESOURCE_TABLES: Final[dict[str, sa.Table]] = {
    "competitions": models.api_football_competitions,
    "seasons": models.api_football_seasons,
    "teams": models.api_football_teams,
    "matches": models.api_football_matches,
    "standings": models.api_football_standings,
    "match_statistics": models.api_football_match_statistics,
    "match_events": models.api_football_match_events,
    "injuries": models.api_football_injuries,
    "lineups": models.api_football_lineups,
}
PUBLIC_ERROR_MESSAGE: Final = "La synchronisation sportive n'a pas pu etre terminee."


class SportsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def ensure_provider(self, *, enabled: bool) -> UUID:
        statement = (
            pg_insert(models.providers)
            .values(
                provider_key=API_FOOTBALL_PROVIDER,
                name="API-Football",
                enabled=enabled,
                production_mock_fallback=False,
                metadata={
                    "mode": "backend_read_only_ingestion",
                    "raw_payload_stored": False,
                    "predictions_enabled": False,
                    "bookmakers_enabled": False,
                    "live_automatic_enabled": False,
                },
            )
            .on_conflict_do_update(
                index_elements=[models.providers.c.provider_key],
                set_={
                    "name": "API-Football",
                    "enabled": enabled,
                    "production_mock_fallback": False,
                    "updated_at": sa.func.now(),
                },
            )
            .returning(models.providers.c.id)
        )
        return self.session.execute(statement).scalar_one()

    def start_run(
        self,
        *,
        provider_id: UUID,
        sync_type: str,
        scope: Mapping[str, Any],
        started_at: datetime,
    ) -> UUID:
        statement = (
            models.sports_sync_runs.insert()
            .values(
                provider_id=provider_id,
                provider=API_FOOTBALL_PROVIDER,
                sync_type=sync_type,
                status="RUNNING",
                scope=dict(scope),
                started_at=started_at,
            )
            .returning(models.sports_sync_runs.c.id)
        )
        return self.session.execute(statement).scalar_one()

    def insert_result(
        self,
        result: NormalizationResult,
        *,
        provider_id: UUID,
        run_id: UUID,
    ) -> tuple[int, int]:
        if result.resource not in RESOURCE_TABLES:
            raise ValueError("Unsupported sports-data resource.")
        if not result.rows:
            return 0, 0
        table = RESOURCE_TABLES[result.resource]
        values = [
            {
                **row,
                "provider_id": provider_id,
                "sync_run_id": run_id,
            }
            for row in result.rows
        ]
        statement = (
            pg_insert(table)
            .values(values)
            .on_conflict_do_nothing()
            .returning(table.c.id)
        )
        outcome = self.session.execute(statement)
        inserted = len(outcome.scalars().all())
        return inserted, len(values) - inserted

    def record_error(
        self,
        *,
        run_id: UUID,
        endpoint: str,
        error_code: str,
        retryable: bool,
        occurred_at: datetime,
        attempt: int = 1,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        self.session.execute(
            models.sports_sync_errors.insert().values(
                sync_run_id=run_id,
                provider=API_FOOTBALL_PROVIDER,
                endpoint=endpoint[:80],
                error_code=error_code[:80],
                public_message=PUBLIC_ERROR_MESSAGE,
                retryable=retryable,
                attempt=attempt,
                occurred_at=occurred_at,
                context=dict(context or {}),
            )
        )

    def finish_run(
        self,
        *,
        run_id: UUID,
        status: str,
        completed_at: datetime,
        request_count: int,
        records_received: int,
        records_inserted: int,
        records_duplicate: int,
        records_rejected: int,
        quota_limit_daily: int | None,
        quota_remaining_daily: int | None,
        quota_limit_minute: int | None,
        quota_remaining_minute: int | None,
        checkpoint: Mapping[str, Any] | None = None,
        public_error_code: str | None = None,
    ) -> None:
        self.session.execute(
            models.sports_sync_runs.update()
            .where(models.sports_sync_runs.c.id == run_id)
            .values(
                status=status,
                completed_at=completed_at,
                request_count=request_count,
                records_received=records_received,
                records_inserted=records_inserted,
                records_duplicate=records_duplicate,
                records_rejected=records_rejected,
                quota_limit_daily=quota_limit_daily,
                quota_remaining_daily=quota_remaining_daily,
                quota_limit_minute=quota_limit_minute,
                quota_remaining_minute=quota_remaining_minute,
                checkpoint=dict(checkpoint or {}),
                public_error_code=public_error_code,
                updated_at=sa.func.now(),
            )
        )

    def list_competitions(self, *, limit: int = 100) -> list[dict[str, Any]]:
        latest = _latest_observations(
            models.api_football_competitions,
            models.api_football_competitions.c.provider_competition_id,
        )
        statement = (
            sa.select(latest)
            .where(latest.c.observation_rank == 1)
            .order_by(latest.c.name)
            .limit(limit)
        )
        return _rows(self.session.execute(statement))

    def list_matches(
        self,
        *,
        starts_at: datetime,
        ends_at: datetime,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        latest = _latest_observations(
            models.api_football_matches,
            models.api_football_matches.c.provider_match_id,
        )
        statement = (
            sa.select(latest)
            .where(
                latest.c.observation_rank == 1,
                latest.c.kickoff_at >= starts_at,
                latest.c.kickoff_at < ends_at,
            )
            .order_by(latest.c.kickoff_at, latest.c.provider_match_id)
            .limit(limit)
        )
        return _rows(self.session.execute(statement))

    def get_match(self, provider_match_id: int) -> dict[str, Any] | None:
        latest = _latest_observations(
            models.api_football_matches,
            models.api_football_matches.c.provider_match_id,
        )
        statement = sa.select(latest).where(
            latest.c.observation_rank == 1,
            latest.c.provider_match_id == provider_match_id,
        )
        row = self.session.execute(statement).mappings().first()
        return _clean_row(row) if row else None

    def list_match_resource(
        self,
        resource: str,
        provider_match_id: int,
        *,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        if resource not in {
            "match_statistics",
            "match_events",
            "injuries",
            "lineups",
        }:
            raise ValueError("Unsupported match resource.")
        table = RESOURCE_TABLES[resource]
        latest = _latest_observations(table, table.c.provider_event_id)
        statement = (
            sa.select(latest)
            .where(
                latest.c.observation_rank == 1,
                latest.c.provider_match_id == provider_match_id,
            )
            .order_by(latest.c.provider_event_id)
            .limit(limit)
        )
        return _rows(self.session.execute(statement))

    def latest_sync_status(self) -> dict[str, Any] | None:
        statement = (
            sa.select(models.sports_sync_runs)
            .where(models.sports_sync_runs.c.provider == API_FOOTBALL_PROVIDER)
            .order_by(models.sports_sync_runs.c.started_at.desc())
            .limit(1)
        )
        row = self.session.execute(statement).mappings().first()
        return dict(row) if row else None

    def recent_public_errors(self, *, limit: int = 5) -> list[str]:
        statement = (
            sa.select(models.sports_sync_errors.c.error_code)
            .where(models.sports_sync_errors.c.provider == API_FOOTBALL_PROVIDER)
            .order_by(models.sports_sync_errors.c.occurred_at.desc())
            .limit(limit)
        )
        return [str(value) for value in self.session.execute(statement).scalars()]

    def last_successful_sync(self) -> dict[str, Any] | None:
        statement = (
            sa.select(models.sports_sync_runs)
            .where(
                models.sports_sync_runs.c.provider == API_FOOTBALL_PROVIDER,
                models.sports_sync_runs.c.status.in_(("SUCCEEDED", "PARTIAL")),
            )
            .order_by(models.sports_sync_runs.c.completed_at.desc())
            .limit(1)
        )
        row = self.session.execute(statement).mappings().first()
        return _clean_row(row) if row else None

    def resource_freshness(self) -> list[dict[str, Any]]:
        resources = (
            ("competitions", models.api_football_competitions),
            ("seasons", models.api_football_seasons),
            ("teams", models.api_football_teams),
            ("matches", models.api_football_matches),
            ("standings", models.api_football_standings),
            ("statistics", models.api_football_match_statistics),
            ("events", models.api_football_match_events),
            ("injuries", models.api_football_injuries),
            ("lineups", models.api_football_lineups),
        )
        output: list[dict[str, Any]] = []
        for resource, table in resources:
            statement = sa.select(
                sa.func.max(table.c.fetched_at).label("latest_fetched_at"),
                sa.func.count(sa.distinct(table.c.provider_event_id)).label("row_count"),
            )
            row = self.session.execute(statement).mappings().one()
            output.append(
                {
                    "resource": resource,
                    "latest_fetched_at": row["latest_fetched_at"],
                    "row_count": int(row["row_count"] or 0),
                }
            )
        return output

    def completed_match_ids_without_statistics(
        self,
        *,
        starts_at: datetime,
        ends_at: datetime,
        limit: int,
    ) -> list[int]:
        matches = self.list_matches(
            starts_at=starts_at,
            ends_at=ends_at,
            limit=max(limit * 4, limit),
        )
        completed_statuses = {"FT", "AET", "PEN"}
        candidates = [
            int(row["provider_match_id"])
            for row in matches
            if row.get("status_short") in completed_statuses
        ]
        if not candidates:
            return []
        existing = set(
            self.session.execute(
                sa.select(
                    sa.distinct(
                        models.api_football_match_statistics.c.provider_match_id
                    )
                ).where(
                    models.api_football_match_statistics.c.provider_match_id.in_(
                        candidates
                    )
                )
            ).scalars()
        )
        return [match_id for match_id in candidates if match_id not in existing][
            :limit
        ]


def apply_runtime_freshness(
    row: Mapping[str, Any],
    *,
    now: datetime,
    threshold_minutes: int,
) -> dict[str, Any]:
    output = dict(row)
    fetched_at = output.get("fetched_at")
    if not isinstance(fetched_at, datetime) or fetched_at.tzinfo is None:
        output["freshness_status"] = "unknown"
        return output
    age_seconds = (now.astimezone(UTC) - fetched_at.astimezone(UTC)).total_seconds()
    output["freshness_status"] = (
        "fresh"
        if 0 <= age_seconds <= threshold_minutes * 60
        else "stale"
    )
    return output


def _latest_observations(
    table: sa.Table,
    identity_column: sa.Column,
) -> sa.Subquery:
    return (
        sa.select(
            table,
            sa.func.row_number()
            .over(
                partition_by=identity_column,
                order_by=(table.c.available_at.desc(), table.c.created_at.desc()),
            )
            .label("observation_rank"),
        )
        .subquery()
    )


def _rows(result: sa.Result[Any]) -> list[dict[str, Any]]:
    return [_clean_row(row) for row in result.mappings()]


def _clean_row(row: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {
        "id",
        "provider_id",
        "sync_run_id",
        "created_at",
        "observation_rank",
    }
    return {key: value for key, value in row.items() if key not in excluded}


__all__ = [
    "PUBLIC_ERROR_MESSAGE",
    "RESOURCE_TABLES",
    "SportsRepository",
    "apply_runtime_freshness",
]
