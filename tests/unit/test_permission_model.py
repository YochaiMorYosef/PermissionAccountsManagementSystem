import pytest
from src.models.permission import Permission, ScheduleEntry
from src.models.permission_status import PermissionStatus


def test_schedule_entry_roundtrip():
    entry = ScheduleEntry(weekday=0, start_time="09:00", end_time="17:00")
    assert ScheduleEntry.from_dict(entry.to_dict()) == entry


def test_permission_create_generates_uuid():
    data = {"user": "alice", "account_id": "acc-1", "permission": "read"}
    p = Permission.create("tenant-1", data)
    assert p.permission_id
    assert p.tenant_id == "tenant-1"
    assert p.schedule is None
    assert p.status == PermissionStatus.CREATING


def test_permission_create_with_schedule():
    data = {
        "user": "alice",
        "account_id": "acc-1",
        "permission": "read",
        "schedule": [{"weekday": 1, "start_time": "08:00", "end_time": "18:00"}],
    }
    p = Permission.create("tenant-1", data)
    assert len(p.schedule) == 1
    assert p.schedule[0].weekday == 1


def test_permission_to_dict_without_schedule():
    data = {"user": "alice", "account_id": "acc-1", "permission": "read"}
    p = Permission.create("tenant-1", data)
    d = p.to_dict()
    assert d["schedule"] is None
    assert d["user"] == "alice"
    assert d["status"] == "Creating"


def test_permission_to_dynamo_item_omits_schedule_key_when_none():
    data = {"user": "alice", "account_id": "acc-1", "permission": "read"}
    p = Permission.create("tenant-1", data)
    item = p.to_dynamo_item()
    assert "schedule" not in item
    assert item["status"] == "Creating"


def test_permission_from_dynamo_item_without_schedule():
    item = {
        "tenant_id": "tenant-1",
        "permission_id": "perm-1",
        "user": "alice",
        "account_id": "acc-1",
        "permission": "read",
        "status": "Active",
    }
    p = Permission.from_dynamo_item(item)
    assert p.schedule is None
    assert p.status == PermissionStatus.ACTIVE


def test_permission_from_dynamo_item_defaults_status_to_active_when_missing():
    item = {
        "tenant_id": "tenant-1",
        "permission_id": "perm-1",
        "user": "alice",
        "account_id": "acc-1",
        "permission": "read",
    }
    p = Permission.from_dynamo_item(item)
    assert p.status == PermissionStatus.ACTIVE


def test_permission_from_dynamo_item_with_schedule():
    item = {
        "tenant_id": "tenant-1",
        "permission_id": "perm-1",
        "user": "alice",
        "account_id": "acc-1",
        "permission": "read",
        "status": "Active",
        "schedule": [{"weekday": 3, "start_time": "10:00", "end_time": "20:00"}],
    }
    p = Permission.from_dynamo_item(item)
    assert p.schedule[0].weekday == 3


def test_permission_status_is_str():
    assert isinstance(PermissionStatus.ACTIVE, str)
    assert PermissionStatus.ACTIVE == "Active"
