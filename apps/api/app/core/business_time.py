from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import Final
from zoneinfo import ZoneInfo


BUSINESS_TIMEZONE_NAME: Final = "Africa/Kinshasa"
BUSINESS_TIMEZONE: Final = ZoneInfo(BUSINESS_TIMEZONE_NAME)


def utc_now() -> datetime:
    return datetime.now(UTC)


def business_date_at(moment: datetime) -> date:
    if moment.tzinfo is None or moment.tzinfo.utcoffset(moment) is None:
        raise ValueError("moment must be timezone-aware.")
    return moment.astimezone(BUSINESS_TIMEZONE).date()


def business_today() -> date:
    return business_date_at(utc_now())


def utc_bounds_for_business_date(local_date: date) -> tuple[datetime, datetime]:
    if local_date <= date.min or local_date >= date.max:
        raise ValueError("business date cannot be converted safely.")
    starts_at = datetime.combine(
        local_date,
        time.min,
        tzinfo=BUSINESS_TIMEZONE,
    ).astimezone(UTC)
    ends_at = datetime.combine(
        local_date + timedelta(days=1),
        time.min,
        tzinfo=BUSINESS_TIMEZONE,
    ).astimezone(UTC)
    return starts_at, ends_at


def utc_bounds_for_business_dates(
    starts_on: date,
    ends_on: date,
) -> tuple[datetime, datetime]:
    if ends_on < starts_on:
        raise ValueError("business date range is invalid.")
    starts_at, _ = utc_bounds_for_business_date(starts_on)
    _, ends_at = utc_bounds_for_business_date(ends_on)
    return starts_at, ends_at


__all__ = [
    "BUSINESS_TIMEZONE",
    "BUSINESS_TIMEZONE_NAME",
    "business_date_at",
    "business_today",
    "utc_bounds_for_business_date",
    "utc_bounds_for_business_dates",
    "utc_now",
]
