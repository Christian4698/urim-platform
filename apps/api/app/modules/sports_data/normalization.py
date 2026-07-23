from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
from typing import Any, Final

from app.modules.sports_data.provider import (
    API_FOOTBALL_PROVIDER,
    ApiFootballEnvelope,
)

COMMON_QUALITY_FLAGS: Final = (
    "REAL_PROVIDER_DATA",
    "NORMALIZED",
    "RAW_PAYLOAD_NOT_STORED",
)


class SportsNormalizationError(ValueError):
    """Raised when a provider row cannot satisfy the canonical B1 contract."""


@dataclass(frozen=True)
class NormalizationResult:
    resource: str
    rows: tuple[dict[str, Any], ...]
    rejected_count: int = 0
    error_codes: tuple[str, ...] = ()


def normalize_leagues(
    envelope: ApiFootballEnvelope,
) -> tuple[NormalizationResult, NormalizationResult]:
    competitions: list[dict[str, Any]] = []
    seasons: list[dict[str, Any]] = []
    rejected = 0
    for item in envelope.data.response:
        try:
            row = _mapping(item)
            league = _mapping(row.get("league"))
            country = _mapping_or_empty(row.get("country"))
            provider_competition_id = _required_int(league, "id")
            season_rows = row.get("seasons")
            normalized_seasons = season_rows if isinstance(season_rows, list) else []
            current_season = next(
                (
                    _optional_int(_mapping(season), "year")
                    for season in normalized_seasons
                    if _mapping(season).get("current") is True
                ),
                None,
            )
            competitions.append(
                {
                    **_provenance(
                        envelope,
                        f"competition:{provider_competition_id}",
                    ),
                    "provider_competition_id": provider_competition_id,
                    "name": _required_text(league, "name"),
                    "kind": _optional_text(league, "type"),
                    "country_name": _optional_text(country, "name"),
                    "country_code": _optional_text(country, "code"),
                    "current_season": current_season,
                    "coverage": _latest_coverage(normalized_seasons),
                }
            )
            for season_item in normalized_seasons:
                season = _mapping(season_item)
                year = _required_int(season, "year")
                seasons.append(
                    {
                        **_provenance(
                            envelope,
                            f"season:{provider_competition_id}:{year}",
                        ),
                        "provider_competition_id": provider_competition_id,
                        "year": year,
                        "starts_on": _optional_date(season, "start"),
                        "ends_on": _optional_date(season, "end"),
                        "is_current": season.get("current") is True,
                        "coverage": _safe_mapping(season.get("coverage")),
                    }
                )
        except SportsNormalizationError:
            rejected += 1
    errors = ("invalid_league_row",) if rejected else ()
    return (
        NormalizationResult(
            resource="competitions",
            rows=tuple(competitions),
            rejected_count=rejected,
            error_codes=errors,
        ),
        NormalizationResult(
            resource="seasons",
            rows=tuple(seasons),
            rejected_count=rejected,
            error_codes=errors,
        ),
    )


def normalize_teams(envelope: ApiFootballEnvelope) -> NormalizationResult:
    def normalize(item: Any) -> dict[str, Any]:
        row = _mapping(item)
        team = _mapping(row.get("team"))
        venue = _mapping_or_empty(row.get("venue"))
        provider_team_id = _required_int(team, "id")
        return {
            **_provenance(envelope, f"team:{provider_team_id}"),
            "provider_team_id": provider_team_id,
            "name": _required_text(team, "name"),
            "code": _optional_text(team, "code"),
            "country": _optional_text(team, "country"),
            "founded": _optional_int(team, "founded"),
            "is_national": team.get("national") if isinstance(team.get("national"), bool) else None,
            "venue_provider_id": _optional_int(venue, "id"),
            "venue_name": _optional_text(venue, "name"),
            "venue_city": _optional_text(venue, "city"),
            "venue_capacity": _optional_int(venue, "capacity"),
        }

    return _normalize_rows("teams", envelope, normalize)


def normalize_fixtures(envelope: ApiFootballEnvelope) -> NormalizationResult:
    def normalize(item: Any) -> dict[str, Any]:
        row = _mapping(item)
        fixture = _mapping(row.get("fixture"))
        league = _mapping(row.get("league"))
        teams = _mapping(row.get("teams"))
        home = _mapping(teams.get("home"))
        away = _mapping(teams.get("away"))
        status = _mapping(fixture.get("status"))
        goals = _mapping_or_empty(row.get("goals"))
        score = _mapping_or_empty(row.get("score"))
        halftime = _mapping_or_empty(score.get("halftime"))
        fulltime = _mapping_or_empty(score.get("fulltime"))
        venue = _mapping_or_empty(fixture.get("venue"))
        provider_match_id = _required_int(fixture, "id")
        return {
            **_provenance(envelope, f"match:{provider_match_id}"),
            "provider_match_id": provider_match_id,
            "provider_competition_id": _required_int(league, "id"),
            "season": _required_int(league, "season"),
            "kickoff_at": _required_datetime(fixture, "date"),
            "timezone": _required_text(fixture, "timezone"),
            "status_short": _required_text(status, "short"),
            "status_long": _required_text(status, "long"),
            "elapsed": _optional_int(status, "elapsed"),
            "round": _optional_text(league, "round"),
            "venue_name": _optional_text(venue, "name"),
            "venue_city": _optional_text(venue, "city"),
            "home_team_provider_id": _required_int(home, "id"),
            "home_team_name": _required_text(home, "name"),
            "away_team_provider_id": _required_int(away, "id"),
            "away_team_name": _required_text(away, "name"),
            "goals_home": _optional_int(goals, "home"),
            "goals_away": _optional_int(goals, "away"),
            "score_halftime_home": _optional_int(halftime, "home"),
            "score_halftime_away": _optional_int(halftime, "away"),
            "score_fulltime_home": _optional_int(fulltime, "home"),
            "score_fulltime_away": _optional_int(fulltime, "away"),
        }

    return _normalize_rows("matches", envelope, normalize)


def normalize_standings(envelope: ApiFootballEnvelope) -> NormalizationResult:
    rows: list[dict[str, Any]] = []
    rejected = 0
    for item in envelope.data.response:
        try:
            league = _mapping(_mapping(item).get("league"))
            competition_id = _required_int(league, "id")
            season = _required_int(league, "season")
            groups = league.get("standings")
            if not isinstance(groups, list):
                raise SportsNormalizationError("standings groups are missing")
            for group in groups:
                if not isinstance(group, list):
                    continue
                for standing_item in group:
                    standing = _mapping(standing_item)
                    team = _mapping(standing.get("team"))
                    provider_team_id = _required_int(team, "id")
                    group_name = _optional_text(standing, "group")
                    all_stats = _mapping_or_empty(standing.get("all"))
                    goals = _mapping_or_empty(all_stats.get("goals"))
                    event_id = (
                        f"standing:{competition_id}:{season}:"
                        f"{group_name or 'default'}:{provider_team_id}"
                    )
                    rows.append(
                        {
                            **_provenance(envelope, event_id),
                            "provider_competition_id": competition_id,
                            "season": season,
                            "provider_team_id": provider_team_id,
                            "team_name": _required_text(team, "name"),
                            "group_name": group_name,
                            "rank": _required_int(standing, "rank"),
                            "points": _optional_int(standing, "points"),
                            "goals_diff": _optional_int(standing, "goalsDiff"),
                            "form": _optional_text(standing, "form"),
                            "description": _optional_text(standing, "description"),
                            "played": _optional_int(all_stats, "played"),
                            "wins": _optional_int(all_stats, "win"),
                            "draws": _optional_int(all_stats, "draw"),
                            "losses": _optional_int(all_stats, "lose"),
                            "goals_for": _optional_int(goals, "for"),
                            "goals_against": _optional_int(goals, "against"),
                        }
                    )
        except SportsNormalizationError:
            rejected += 1
    return NormalizationResult(
        resource="standings",
        rows=tuple(rows),
        rejected_count=rejected,
        error_codes=("invalid_standings_row",) if rejected else (),
    )


def normalize_match_statistics(
    envelope: ApiFootballEnvelope,
    provider_match_id: int,
) -> NormalizationResult:
    rows: list[dict[str, Any]] = []
    rejected = 0
    for item in envelope.data.response:
        try:
            row = _mapping(item)
            team = _mapping(row.get("team"))
            team_id = _required_int(team, "id")
            statistics = row.get("statistics")
            if not isinstance(statistics, list):
                raise SportsNormalizationError("statistics list is missing")
            for statistic_item in statistics:
                statistic = _mapping(statistic_item)
                statistic_type = _required_text(statistic, "type")
                event_id = (
                    f"match-statistic:{provider_match_id}:{team_id}:"
                    f"{_stable_key(statistic_type)}"
                )
                rows.append(
                    {
                        **_provenance(envelope, event_id),
                        "provider_match_id": provider_match_id,
                        "provider_team_id": team_id,
                        "statistic_type": statistic_type,
                        "statistic_value": _safe_scalar(statistic.get("value")),
                    }
                )
        except SportsNormalizationError:
            rejected += 1
    return NormalizationResult(
        resource="match_statistics",
        rows=tuple(rows),
        rejected_count=rejected,
        error_codes=("invalid_match_statistics_row",) if rejected else (),
    )


def normalize_match_events(
    envelope: ApiFootballEnvelope,
    provider_match_id: int,
) -> NormalizationResult:
    def normalize(item: Any) -> dict[str, Any]:
        row = _mapping(item)
        time = _mapping(row.get("time"))
        team = _mapping_or_empty(row.get("team"))
        player = _mapping_or_empty(row.get("player"))
        assist = _mapping_or_empty(row.get("assist"))
        event_key = _stable_key(
            {
                "match": provider_match_id,
                "elapsed": time.get("elapsed"),
                "extra": time.get("extra"),
                "team": team.get("id"),
                "player": player.get("id"),
                "type": row.get("type"),
                "detail": row.get("detail"),
                "comments": row.get("comments"),
            }
        )
        return {
            **_provenance(
                envelope,
                f"match-event:{provider_match_id}:{event_key}",
            ),
            "provider_match_id": provider_match_id,
            "event_key": event_key,
            "elapsed": _optional_int(time, "elapsed"),
            "extra": _optional_int(time, "extra"),
            "provider_team_id": _optional_int(team, "id"),
            "team_name": _optional_text(team, "name"),
            "provider_player_id": _optional_int(player, "id"),
            "player_name": _optional_text(player, "name"),
            "provider_assist_id": _optional_int(assist, "id"),
            "assist_name": _optional_text(assist, "name"),
            "event_type": _required_text(row, "type"),
            "detail": _optional_text(row, "detail"),
            "comments": _optional_text(row, "comments"),
        }

    return _normalize_rows("match_events", envelope, normalize)


def normalize_lineups(
    envelope: ApiFootballEnvelope,
    provider_match_id: int,
) -> NormalizationResult:
    rows: list[dict[str, Any]] = []
    rejected = 0
    for item in envelope.data.response:
        try:
            row = _mapping(item)
            team = _mapping(row.get("team"))
            coach = _mapping_or_empty(row.get("coach"))
            team_id = _required_int(team, "id")
            for field_name, role in (("startXI", "start_xi"), ("substitutes", "substitute")):
                players = row.get(field_name)
                if players is None:
                    continue
                if not isinstance(players, list):
                    raise SportsNormalizationError("lineup player list is invalid")
                for player_item in players:
                    player = _mapping(_mapping(player_item).get("player"))
                    player_id = _optional_int(player, "id")
                    identity = player_id or _stable_key(_optional_text(player, "name") or "unknown")
                    event_id = (
                        f"lineup:{provider_match_id}:{team_id}:{role}:{identity}"
                    )
                    rows.append(
                        {
                            **_provenance(envelope, event_id),
                            "provider_match_id": provider_match_id,
                            "provider_team_id": team_id,
                            "team_name": _required_text(team, "name"),
                            "formation": _optional_text(row, "formation"),
                            "provider_coach_id": _optional_int(coach, "id"),
                            "coach_name": _optional_text(coach, "name"),
                            "provider_player_id": player_id,
                            "player_name": _optional_text(player, "name"),
                            "number": _optional_int(player, "number"),
                            "position": _optional_text(player, "pos"),
                            "grid": _optional_text(player, "grid"),
                            "role": role,
                        }
                    )
        except SportsNormalizationError:
            rejected += 1
    return NormalizationResult(
        resource="lineups",
        rows=tuple(rows),
        rejected_count=rejected,
        error_codes=("invalid_lineup_row",) if rejected else (),
    )


def normalize_injuries(envelope: ApiFootballEnvelope) -> NormalizationResult:
    def normalize(item: Any) -> dict[str, Any]:
        row = _mapping(item)
        fixture = _mapping_or_empty(row.get("fixture"))
        league = _mapping_or_empty(row.get("league"))
        team = _mapping(row.get("team"))
        player = _mapping(row.get("player"))
        match_id = _optional_int(fixture, "id")
        team_id = _required_int(team, "id")
        player_id = _required_int(player, "id")
        event_id = (
            f"injury:{match_id or 'unknown'}:{team_id}:{player_id}:"
            f"{_stable_key([player.get('type'), player.get('reason')])}"
        )
        return {
            **_provenance(envelope, event_id),
            "provider_match_id": match_id,
            "provider_competition_id": _optional_int(league, "id"),
            "season": _optional_int(league, "season"),
            "provider_team_id": team_id,
            "team_name": _required_text(team, "name"),
            "provider_player_id": player_id,
            "player_name": _required_text(player, "name"),
            "injury_type": _optional_text(player, "type"),
            "reason": _optional_text(player, "reason"),
        }

    return _normalize_rows("injuries", envelope, normalize)


def _normalize_rows(
    resource: str,
    envelope: ApiFootballEnvelope,
    normalizer: Callable[[Any], dict[str, Any]],
) -> NormalizationResult:
    rows: list[dict[str, Any]] = []
    rejected = 0
    for item in envelope.data.response:
        try:
            rows.append(normalizer(item))
        except SportsNormalizationError:
            rejected += 1
    return NormalizationResult(
        resource=resource,
        rows=tuple(rows),
        rejected_count=rejected,
        error_codes=(f"invalid_{resource}_row",) if rejected else (),
    )


def _provenance(
    envelope: ApiFootballEnvelope,
    provider_event_id: str,
) -> dict[str, Any]:
    if not envelope.observed_at <= envelope.available_at <= envelope.fetched_at:
        raise SportsNormalizationError("provider temporal order is invalid")
    return {
        "provider": API_FOOTBALL_PROVIDER,
        "provider_event_id": provider_event_id,
        "observed_at": envelope.observed_at,
        "available_at": envelope.available_at,
        "fetched_at": envelope.fetched_at,
        "source_version": envelope.source_version,
        "quality_flags": list(COMMON_QUALITY_FLAGS),
        "raw_hash": envelope.raw_hash,
        "freshness_status": "fresh",
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SportsNormalizationError("provider row must be an object")
    return value


def _mapping_or_empty(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _required_int(row: Mapping[str, Any], key: str) -> int:
    value = _optional_int(row, key)
    if value is None or value <= 0:
        raise SportsNormalizationError(f"{key} must be a positive integer")
    return value


def _optional_int(row: Mapping[str, Any], key: str) -> int | None:
    value = row.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = _optional_text(row, key)
    if value is None:
        raise SportsNormalizationError(f"{key} must be a non-empty string")
    return value


def _optional_text(row: Mapping[str, Any], key: str) -> str | None:
    value = row.get(key)
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value[:500] if value else None


def _required_datetime(row: Mapping[str, Any], key: str) -> datetime:
    value = row.get(key)
    if not isinstance(value, str):
        raise SportsNormalizationError(f"{key} must be an ISO datetime")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SportsNormalizationError(f"{key} must be an ISO datetime") from exc
    if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
        raise SportsNormalizationError(f"{key} must be timezone-aware")
    return parsed


def _optional_date(row: Mapping[str, Any], key: str) -> date | None:
    value = row.get(key)
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _safe_scalar(value: Any) -> str | int | float | bool | None:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    return None


def _safe_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {
        str(key)[:120]: _safe_json(value_item)
        for key, value_item in value.items()
    }


def _safe_json(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        return _safe_mapping(value)
    if isinstance(value, list):
        return [_safe_json(item) for item in value[:200]]
    return None


def _latest_coverage(seasons: list[Any]) -> dict[str, Any]:
    usable = [_mapping(item) for item in seasons if isinstance(item, Mapping)]
    current = next((item for item in usable if item.get("current") is True), None)
    selected = current or (usable[-1] if usable else {})
    return _safe_mapping(selected.get("coverage"))


def _stable_key(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:24]


__all__ = [
    "NormalizationResult",
    "SportsNormalizationError",
    "normalize_fixtures",
    "normalize_injuries",
    "normalize_leagues",
    "normalize_lineups",
    "normalize_match_events",
    "normalize_match_statistics",
    "normalize_standings",
    "normalize_teams",
]
