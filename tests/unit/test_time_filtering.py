import pytest
from datetime import datetime, timezone
from src.bl.time_filtering import is_permission_active as _is_permission_active
from src.models.permission import Permission, ScheduleEntry
from src.models.permission_status import PermissionStatus


def _make_permission(schedule):
    return Permission(
        tenant_id="t1",
        permission_id="p1",
        user="alice",
        account_id="acc-1",
        permission="read",
        status=PermissionStatus.ACTIVE,
        schedule=schedule,
    )


def _utc(year, month, day, hour, minute, weekday_override=None):
    dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
    return dt


MONDAY_10AM = datetime(2026, 3, 9, 10, 0, tzinfo=timezone.utc)
MONDAY_20PM = datetime(2026, 3, 9, 20, 0, tzinfo=timezone.utc)
TUESDAY_10AM = datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)


def test_always_active_when_no_schedule():
    p = _make_permission(None)
    assert _is_permission_active(p, MONDAY_10AM) is True


def test_active_in_window():
    schedule = [ScheduleEntry(weekday=0, start_time="09:00", end_time="17:00")]
    p = _make_permission(schedule)
    assert _is_permission_active(p, MONDAY_10AM) is True


def test_inactive_outside_window():
    schedule = [ScheduleEntry(weekday=0, start_time="09:00", end_time="17:00")]
    p = _make_permission(schedule)
    assert _is_permission_active(p, MONDAY_20PM) is False


def test_inactive_wrong_weekday():
    schedule = [ScheduleEntry(weekday=0, start_time="09:00", end_time="17:00")]
    p = _make_permission(schedule)
    assert _is_permission_active(p, TUESDAY_10AM) is False


def test_overnight_window_active_before_midnight():
    schedule = [ScheduleEntry(weekday=0, start_time="22:00", end_time="06:00")]
    p = _make_permission(schedule)
    late_monday = datetime(2026, 3, 9, 23, 0, tzinfo=timezone.utc)
    assert _is_permission_active(p, late_monday) is True


def test_overnight_window_active_after_midnight():
    schedule = [ScheduleEntry(weekday=1, start_time="22:00", end_time="06:00")]
    p = _make_permission(schedule)
    early_tuesday = datetime(2026, 3, 10, 2, 0, tzinfo=timezone.utc)
    assert _is_permission_active(p, early_tuesday) is True


def test_overnight_window_inactive_in_gap():
    schedule = [ScheduleEntry(weekday=0, start_time="22:00", end_time="06:00")]
    p = _make_permission(schedule)
    assert _is_permission_active(p, MONDAY_10AM) is False


def test_active_at_exact_start_time():
    schedule = [ScheduleEntry(weekday=0, start_time="10:00", end_time="17:00")]
    p = _make_permission(schedule)
    assert _is_permission_active(p, MONDAY_10AM) is True


def test_active_at_exact_end_time():
    schedule = [ScheduleEntry(weekday=0, start_time="09:00", end_time="20:00")]
    p = _make_permission(schedule)
    assert _is_permission_active(p, MONDAY_20PM) is True


def test_multiple_schedule_entries_one_matches():
    schedule = [
        ScheduleEntry(weekday=2, start_time="09:00", end_time="17:00"),
        ScheduleEntry(weekday=0, start_time="09:00", end_time="17:00"),
    ]
    p = _make_permission(schedule)
    assert _is_permission_active(p, MONDAY_10AM) is True
