import re
from src.models.api_models import CREATE_REQUIRED_FIELDS, UPDATABLE_FIELDS, SCHEDULE_ENTRY_REQUIRED_FIELDS

TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")


class ValidationError(Exception):
    pass


def _validate_time(value: str, field_name: str):
    if not isinstance(value, str) or not TIME_PATTERN.match(value):
        raise ValidationError(f"{field_name} must be in HH:MM format")
    hour, minute = value.split(":")
    if not (0 <= int(hour) <= 23 and 0 <= int(minute) <= 59):
        raise ValidationError(f"{field_name} is not a valid time")


def validate_schedule(schedule):
    if not isinstance(schedule, list) or len(schedule) == 0:
        raise ValidationError("schedule must be a non-empty list")
    for i, entry in enumerate(schedule):
        if not isinstance(entry, dict):
            raise ValidationError(f"schedule[{i}] must be an object")
        missing = SCHEDULE_ENTRY_REQUIRED_FIELDS - entry.keys()
        if missing:
            raise ValidationError(f"schedule[{i}] missing fields: {', '.join(missing)}")
        if not isinstance(entry["weekday"], int) or not (0 <= entry["weekday"] <= 6):
            raise ValidationError(f"schedule[{i}].weekday must be an integer between 0 and 6")
        _validate_time(entry["start_time"], f"schedule[{i}].start_time")
        _validate_time(entry["end_time"], f"schedule[{i}].end_time")


def validate_create(data: dict):
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")
    missing = CREATE_REQUIRED_FIELDS - data.keys()
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")
    for field in ("user", "account_id", "permission"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValidationError(f"{field} must be a non-empty string")
    if data.get("schedule") is not None:
        validate_schedule(data["schedule"])


def validate_update(data: dict):
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")
    valid_fields = {k: v for k, v in data.items() if k in UPDATABLE_FIELDS}
    if not valid_fields:
        raise ValidationError(f"Update body must contain at least one of: {', '.join(UPDATABLE_FIELDS)}")
    for field in ("user", "account_id", "permission"):
        if field in data:
            if not isinstance(data[field], str) or not data[field].strip():
                raise ValidationError(f"{field} must be a non-empty string")
    if "schedule" in data and data["schedule"] is not None:
        validate_schedule(data["schedule"])
    return valid_fields
