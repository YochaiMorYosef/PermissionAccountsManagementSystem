from datetime import datetime, timezone
from src.models.permission import Permission
from src.models.permission_status import PermissionStatus
from src.repositories.permissions_repo import PermissionsRepo
from src.bl.time_filtering import is_permission_active


def get_user_permissions(tenant_id: str, user: str, account_id: str, repo: PermissionsRepo) -> list[Permission]:
    filters = {"user": user, "account_id": account_id}
    permissions, _ = repo.query(tenant_id, filters)
    now = datetime.now(timezone.utc)
    return [
        p for p in permissions
        if p.status == PermissionStatus.ACTIVE and is_permission_active(p, now)
    ]
