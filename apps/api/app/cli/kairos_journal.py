from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date
import json
import sys
from typing import Sequence

from app.core.business_time import utc_bounds_for_business_date, utc_now
from app.core.config import settings
from app.db.session import get_session_factory
from app.modules.kairos.journal import (
    JournalWriteSummary,
    KairosJournalRepository,
)
from app.modules.kairos.models import (
    KairosDataError,
    KairosPreMatchWindowClosedError,
    KairosTemporalIntegrityError,
)
from app.modules.kairos.opportunities import KairosOpportunityService
from app.modules.kairos.performance import KairosPerformanceRepository
from app.modules.kairos.repository import (
    MAX_DAILY_TARGET_MATCHES,
    KairosRepository,
)
from app.modules.kairos.services import RECENT_WINDOW_MATCHES

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="urim-kairos-journal",
        description=(
            "Journal analytique Kairos append-only, sans appel fournisseur "
            "ni action de pari."
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True)
    snapshot = commands.add_parser("snapshot")
    snapshot.add_argument("--date", required=True, type=_parse_date)
    resolve = commands.add_parser("resolve")
    resolve.add_argument("--date", required=True, type=_parse_date)
    commands.add_parser("report")
    return parser


def run_command(args: argparse.Namespace) -> dict[str, object]:
    if not settings.database_url:
        raise RuntimeError("kairos_journal_database_unavailable")
    now = utc_now()
    session_factory = get_session_factory()
    with session_factory() as session:
        journal = KairosJournalRepository(session)
        if args.command == "snapshot":
            starts_at, ends_at = utc_bounds_for_business_date(args.date)
            repository = KairosRepository(session)
            targets = repository.list_target_matches_as_of(
                starts_at=starts_at,
                ends_at=ends_at,
                as_of=now,
                limit=MAX_DAILY_TARGET_MATCHES,
            )
            service = KairosOpportunityService(
                freshness_threshold_minutes=(
                    settings.api_football_freshness_minutes
                )
            )
            total = JournalWriteSummary(0, 0, 0)
            blocked = 0
            opportunity_count = 0
            no_bet_count = 0
            insufficient_data_count = 0
            stale_data_count = 0
            for target in targets:
                try:
                    dataset = repository.load_match_dataset_for_target(
                        target,
                        as_of=now,
                        recent_window=RECENT_WINDOW_MATCHES,
                    )
                    opportunity = service.analyze(dataset)
                    if opportunity.safety_decision == "ANALYSIS_ALLOWED":
                        opportunity_count += 1
                    elif opportunity.safety_decision == "INSUFFICIENT_DATA":
                        insufficient_data_count += 1
                    else:
                        no_bet_count += 1
                    if "stale_data" in opportunity.rejection_reasons:
                        stale_data_count += 1
                    summary = journal.append_opportunity(
                        opportunity,
                        analysis_time=now,
                    )
                    total = _sum_summaries(total, summary)
                except (
                    KairosDataError,
                    KairosPreMatchWindowClosedError,
                    KairosTemporalIntegrityError,
                ):
                    blocked += 1
            session.commit()
            return {
                "command": "snapshot",
                "local_date": args.date.isoformat(),
                "matches_evaluated": len(targets),
                "matches_blocked": blocked,
                "opportunities_generated": opportunity_count,
                "no_bet_count": no_bet_count,
                "insufficient_data_count": insufficient_data_count,
                "stale_data_count": stale_data_count,
                "snapshots_created": total.inserted,
                **asdict(total),
                "provider_calls": False,
                "betting_actions": False,
            }
        if args.command == "resolve":
            starts_at, ends_at = utc_bounds_for_business_date(args.date)
            summary = journal.resolve_completed(
                as_of=now,
                starts_at=starts_at,
                ends_at=ends_at,
            )
            session.commit()
            return {
                "command": "resolve",
                "local_date": args.date.isoformat(),
                **asdict(summary),
                "provider_calls": False,
                "betting_actions": False,
            }
        if args.command == "report":
            metrics = journal.resolved_metrics()
            performance = KairosPerformanceRepository(session).report(
                generated_at=now
            )
            return {
                "command": "report",
                "segments": {
                    market: asdict(metric)
                    for market, metric in metrics.items()
                },
                "performance": performance.model_dump(mode="json"),
                "resolved_only": True,
                "provider_calls": False,
                "betting_actions": False,
            }
    raise ValueError("kairos_journal_command_invalid")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_command(args)
    except Exception:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error": {"code": "kairos_journal_unavailable"},
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps({"status": "completed", **result}, sort_keys=True))
    return 0


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "La date doit utiliser YYYY-MM-DD."
        ) from exc


def _sum_summaries(
    left: JournalWriteSummary,
    right: JournalWriteSummary,
) -> JournalWriteSummary:
    return JournalWriteSummary(
        received=left.received + right.received,
        inserted=left.inserted + right.inserted,
        duplicate=left.duplicate + right.duplicate,
    )


if __name__ == "__main__":
    raise SystemExit(main())
