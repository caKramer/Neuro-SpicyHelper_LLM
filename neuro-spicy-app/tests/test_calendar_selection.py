import os
import sys
from datetime import date, time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import calendar_component as cc  # noqa: E402


@pytest.fixture(autouse=True)
def central_tz(monkeypatch):
    # FullCalendar sends UTC ISO strings; the app must interpret them in local time.
    monkeypatch.setenv("TZ", "America/Chicago")
    import time as _t
    _t.tzset()
    yield
    monkeypatch.delenv("TZ")
    _t.tzset()


def test_morning_slot_uses_clicked_time():
    d, start, end = cc.parse_selection("2026-11-10T12:30:00.000Z", "2026-11-10T13:00:00.000Z")
    assert d == date(2026, 11, 10)
    assert start == time(6, 30)
    assert end == time(7, 0)


def test_evening_slot_stays_on_local_day():
    # 8:00pm CST on Nov 10 is 02:00Z on Nov 11
    d, start, end = cc.parse_selection("2026-11-11T02:00:00.000Z", "2026-11-11T02:30:00.000Z")
    assert d == date(2026, 11, 10)
    assert start == time(20, 0)
    assert end == time(20, 30)


def test_date_click_without_range_defaults_to_one_hour():
    d, start, end = cc.parse_selection("2026-11-10T15:00:00.000Z", "2026-11-10T15:00:00.000Z")
    assert (d, start, end) == (date(2026, 11, 10), time(9, 0), time(10, 0))


def test_plain_date_string_from_month_view():
    d, start, end = cc.parse_selection("2026-11-10", "2026-11-11")
    assert d == date(2026, 11, 10)


def test_late_slot_end_does_not_wrap_past_midnight():
    # 11:30pm CST click -> default 1h end would wrap; clamp to 23:59
    d, start, end = cc.parse_selection("2026-11-11T05:30:00.000Z", "2026-11-11T05:30:00.000Z")
    assert d == date(2026, 11, 10)
    assert start == time(23, 30)
    assert end == time(23, 59)
