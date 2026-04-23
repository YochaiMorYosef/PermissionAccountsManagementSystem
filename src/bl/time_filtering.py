from datetime import datetime, time
from src.models.permission import Permission


def is_permission_active(permission: Permission, now: datetime) -> bool:
    # print(f"Checking if permission {permission} is active at {now}")
    if permission.schedule is None:
        return True
    current_weekday = now.weekday()
    current_time = now.time().replace(second=0, microsecond=0)
    for entry in permission.schedule:
        # print(f"  Checking schedule entry: {entry}")
        start_h, start_m = map(int, entry.start_time.split(":"))
        end_h, end_m = map(int, entry.end_time.split(":"))
        start = time(start_h, start_m)
        end = time(end_h, end_m)


        if start <= end:
            if entry.weekday != current_weekday:
                # print("    Same-day window: weekday does not match, skipping")
                continue

            # print("    Same-day window: weekday matches, checking time")
            if start <= current_time <= end:
                # print("    Time matches -> active")
                return True
        
        else:
            next_weekday = (entry.weekday + 1) % 7
            if current_weekday == entry.weekday:
                # print("    Overnight window: current weekday is start weekday, checking if time is after start")
                if current_time >= start:
                    # print("    Time is after start -> active")
                    return True
            elif current_weekday == next_weekday:
                # print("    Overnight window: current weekday is end weekday, checking if time is before end")
                if current_time <= end:
                    # print("    Time is before end -> active")
                    return True
            # else:
                # print("    Overnight window: current weekday does not match either start or end weekday, skipping")
            
    return False
