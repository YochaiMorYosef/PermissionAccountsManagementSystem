from dataclasses import dataclass
from typing import Optional
import uuid

from src.models.permission_status import PermissionStatus


@dataclass
class ScheduleEntry:
    weekday: int
    start_time: str
    end_time: str

    def to_dict(self):
        return {
            "weekday": self.weekday,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScheduleEntry":
        return cls(
            weekday=int(data["weekday"]),
            start_time=data["start_time"],
            end_time=data["end_time"],
        )


@dataclass
class Permission:
    tenant_id: str
    permission_id: str
    user: str
    account_id: str
    permission: str
    status: PermissionStatus
    schedule: Optional[list[ScheduleEntry]] = None

    @classmethod
    def create(cls, tenant_id: str, data: dict) -> "Permission":
        schedule = None
        if data.get("schedule") is not None:
            schedule = [ScheduleEntry.from_dict(e) for e in data["schedule"]]
        return cls(
            tenant_id=tenant_id,
            permission_id=str(uuid.uuid4()),
            user=data["user"],
            account_id=data["account_id"],
            permission=data["permission"],
            status=PermissionStatus.CREATING,
            schedule=schedule,
        )

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "permission_id": self.permission_id,
            "user": self.user,
            "account_id": self.account_id,
            "permission": self.permission,
            "status": self.status,
            "schedule": [e.to_dict() for e in self.schedule] if self.schedule is not None else None,
        }

    def to_dynamo_item(self) -> dict:
        item = {
            "tenant_id": self.tenant_id,
            "permission_id": self.permission_id,
            "user": self.user,
            "account_id": self.account_id,
            "permission": self.permission,
            "status": self.status,
        }
        if self.schedule is not None:
            item["schedule"] = [e.to_dict() for e in self.schedule]
        return item

    @classmethod
    def from_dynamo_item(cls, item: dict) -> "Permission":
        schedule = None
        if "schedule" in item and item["schedule"] is not None:
            schedule = [ScheduleEntry.from_dict(e) for e in item["schedule"]]
        return cls(
            tenant_id=item["tenant_id"],
            permission_id=item["permission_id"],
            user=item["user"],
            account_id=item["account_id"],
            permission=item["permission"],
            status=PermissionStatus(item.get("status", PermissionStatus.ACTIVE)),
            schedule=schedule,
        )
