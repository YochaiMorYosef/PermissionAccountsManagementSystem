from datetime import datetime, time
from src.models.permission import Permission


def is_permission_active(permission: Permission, now: datetime) -> bool:
    if permission.schedule is None:
        return True
    current_weekday = now.weekday()
    current_time = now.time().replace(second=0, microsecond=0)
    for entry in permission.schedule:
        if entry.weekday != current_weekday:
            continue
        start_h, start_m = map(int, entry.start_time.split(":"))
        end_h, end_m = map(int, entry.end_time.split(":"))
        start = time(start_h, start_m)
        end = time(end_h, end_m)
        if start <= end:
            if start <= current_time <= end:
                return True
        else:
            if current_time >= start or current_time <= end:
                return True
    return False
