from src.models.permission_status import PermissionStatus
from src.repositories.permissions_repo import PermissionsRepo
from src.models.exceptions import PermissionNotFoundError
from src.utils.sqs import send_message


def delete_permission(tenant_id: str, permission_id: str, repo: PermissionsRepo, queue_url: str):
    existing = repo.get(tenant_id, permission_id)
    if existing is None:
        raise PermissionNotFoundError(f"Permission {permission_id} not found")
    repo.update(tenant_id, permission_id, {"status": PermissionStatus.DELETING})
    send_message(queue_url, {
        "action": "delete",
        "tenant_id": tenant_id,
        "permission_id": permission_id,
        "permission_data": existing.to_dict(),
    })
