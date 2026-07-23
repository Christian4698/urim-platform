from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
from datetime import date, timedelta
import json
import sys
from typing import Sequence

from app.db.session import get_session_factory
from app.modules.sports_data.provider import (
    ApiFootballDisabledError,
    ApiFootballRequestError,
)
from app.modules.sports_data.sync import SportsSyncService, SyncSummary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="urim-sports-sync",
        description=(
            "Synchronisation API-Football contrôlée, backend-only et sans live "
            "automatique."
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("competitions")
    commands.add_parser("seasons")
    commands.add_parser("teams")
    commands.add_parser("standings")

    match_date = commands.add_parser("matches-date")
    match_date.add_argument("--date", required=True, type=_parse_date)

    upcoming = commands.add_parser("upcoming")
    upcoming.add_argument("--days", type=int, default=None)

    results = commands.add_parser("results")
    results.add_argument("--from", dest="starts_on", required=True, type=_parse_date)
    results.add_argument("--to", dest="ends_on", required=True, type=_parse_date)

    statistics = commands.add_parser("statistics")
    statistics.add_argument(
        "--from",
        dest="starts_on",
        type=_parse_date,
        default=date.today() - timedelta(days=7),
    )
    statistics.add_argument(
        "--to",
        dest="ends_on",
        type=_parse_date,
        default=date.today(),
    )
    statistics.add_argument(
        "--statistics-only",
        action="store_true",
        help="Ne synchronise pas les événements, compositions et blessures.",
    )
    return parser


async def run_command(args: argparse.Namespace) -> SyncSummary:
    session_factory = get_session_factory()
    with session_factory() as session:
        service = SportsSyncService(session)
        if args.command == "competitions":
            return await service.sync_competitions()
        if args.command == "seasons":
            return await service.sync_seasons()
        if args.command == "teams":
            return await service.sync_teams()
        if args.command == "standings":
            return await service.sync_standings()
        if args.command == "matches-date":
            return await service.sync_matches_for_date(args.date)
        if args.command == "upcoming":
            return await service.sync_upcoming(days=args.days)
        if args.command == "results":
            return await service.sync_results(
                starts_on=args.starts_on,
                ends_on=args.ends_on,
            )
        if args.command == "statistics":
            return await service.sync_statistics(
                starts_on=args.starts_on,
                ends_on=args.ends_on,
                include_related=not args.statistics_only,
            )
    raise ValueError("Unknown synchronization command.")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = asyncio.run(run_command(args))
    except ApiFootballDisabledError:
        _write_public_error("provider_disabled")
        return 2
    except ApiFootballRequestError as exc:
        _write_public_error(exc.public_code)
        return 3
    except (RuntimeError, ValueError):
        _write_public_error("synchronization_configuration_invalid")
        return 4
    except Exception:
        _write_public_error("synchronization_internal_error")
        return 5
    print(
        json.dumps(
            {"status": "completed", "summary": asdict(summary)},
            sort_keys=True,
        )
    )
    return 0


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("La date doit utiliser YYYY-MM-DD.") from exc


def _write_public_error(code: str) -> None:
    print(
        json.dumps(
            {
                "status": "failed",
                "error": {
                    "code": code,
                    "message": "La synchronisation sportive n'a pas pu être terminée.",
                },
            },
            sort_keys=True,
        ),
        file=sys.stderr,
    )


if __name__ == "__main__":
    raise SystemExit(main())
