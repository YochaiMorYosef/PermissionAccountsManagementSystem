import pytest
from src.utils.validation import validate_create, validate_update, ValidationError


def test_validate_create_success():
    validate_create({"user": "alice", "account_id": "acc-1", "permission": "read"})


def test_validate_create_success_with_schedule():
    validate_create({
        "user": "alice",
        "account_id": "acc-1",
        "permission": "read",
        "schedule": [{"weekday": 0, "start_time": "09:00", "end_time": "17:00"}],
    })


def test_validate_create_missing_field():
    with pytest.raises(ValidationError, match="Missing required fields"):
        validate_create({"user": "alice", "account_id": "acc-1"})


def test_validate_create_empty_user():
    with pytest.raises(ValidationError):
        validate_create({"user": "  ", "account_id": "acc-1", "permission": "read"})


def test_validate_create_empty_schedule_list():
    with pytest.raises(ValidationError, match="non-empty"):
        validate_create({
            "user": "alice", "account_id": "acc-1", "permission": "read",
            "schedule": [],
        })


def test_validate_create_schedule_invalid_weekday():
    with pytest.raises(ValidationError, match="weekday"):
        validate_create({
            "user": "alice", "account_id": "acc-1", "permission": "read",
            "schedule": [{"weekday": 7, "start_time": "09:00", "end_time": "17:00"}],
        })


def test_validate_create_schedule_invalid_time_format():
    with pytest.raises(ValidationError, match="HH:MM"):
        validate_create({
            "user": "alice", "account_id": "acc-1", "permission": "read",
            "schedule": [{"weekday": 0, "start_time": "9:00", "end_time": "17:00"}],
        })


def test_validate_update_success():
    fields = validate_update({"user": "bob"})
    assert "user" in fields


def test_validate_update_empty_body():
    with pytest.raises(ValidationError, match="at least one"):
        validate_update({})


def test_validate_update_unknown_fields_only():
    with pytest.raises(ValidationError, match="at least one"):
        validate_update({"unknown_field": "value"})


def test_validate_update_schedule_none_allowed():
    fields = validate_update({"schedule": None})
    assert "schedule" in fields


def test_validate_update_invalid_schedule():
    with pytest.raises(ValidationError):
        validate_update({"schedule": [{"weekday": 0, "start_time": "bad", "end_time": "17:00"}]})
