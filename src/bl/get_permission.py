from src.models.permission import Permission
from src.repositories.permissions_repo import PermissionsRepo
from src.models.exceptions import PermissionNotFoundError


def get_permission(tenant_id: str, permission_id: str, repo: PermissionsRepo) -> Permission:
    permission = repo.get(tenant_id, permission_id)
    if permission is None:
        raise PermissionNotFoundError(f"Permission {permission_id} not found")
    return permission
