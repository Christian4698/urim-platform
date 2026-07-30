from datetime import UTC, date, datetime, timedelta

import pytest

from app.core.business_time import (
    BUSINESS_TIMEZONE_NAME,
    business_date_at,
    utc_bounds_for_business_date,
    utc_bounds_for_business_dates,
)


def test_kinshasa_business_date_changes_at_2300_utc() -> None:
    assert BUSINESS_TIMEZONE_NAME == "Africa/Kinshasa"
    assert business_date_at(
        datetime(2026, 7, 30, 22, 59, 59, tzinfo=UTC)
    ) == date(2026, 7, 30)
    assert business_date_at(
        datetime(2026, 7, 30, 23, 0, 0, tzinfo=UTC)
    ) == date(2026, 7, 31)


def test_kinshasa_day_bounds_are_half_open_in_utc() -> None:
    starts_at, ends_at = utc_bounds_for_business_date(date(2026, 7, 31))

    assert starts_at == datetime(2026, 7, 30, 23, 0, tzinfo=UTC)
    assert ends_at == datetime(2026, 7, 31, 23, 0, tzinfo=UTC)
    assert business_date_at(ends_at - timedelta(microseconds=1)) == date(
        2026,
        7,
        31,
    )
    assert business_date_at(ends_at) == date(2026, 8, 1)


def test_multi_day_bounds_use_two_local_midnights() -> None:
    starts_at, ends_at = utc_bounds_for_business_dates(
        date(2026, 7, 31),
        date(2026, 8, 2),
    )

    assert starts_at == datetime(2026, 7, 30, 23, 0, tzinfo=UTC)
    assert ends_at == datetime(2026, 8, 2, 23, 0, tzinfo=UTC)


def test_business_date_rejects_naive_instants() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        business_date_at(datetime(2026, 7, 31, 0, 0))


@pytest.mark.parametrize("unsafe_date", (date.min, date.max))
def test_business_date_bounds_reject_extremes_before_overflow(
    unsafe_date: date,
) -> None:
    with pytest.raises(ValueError, match="converted safely"):
        utc_bounds_for_business_date(unsafe_date)
