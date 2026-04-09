from src.models.permission import Permission
from src.repositories.permissions_repo import PermissionsRepo
from src.utils.validation import validate_create
from src.utils.sqs import send_message


def create_permission(tenant_id: str, data: dict, repo: PermissionsRepo, queue_url: str) -> Permission:
    validate_create(data)
    permission = Permission.create(tenant_id, data)
    repo.put(permission)
    send_message(queue_url, {
        "action": "create",
        "tenant_id": tenant_id,
        "permission_id": permission.permission_id,
        "permission_data": permission.to_dict(),
    })
    return permission
