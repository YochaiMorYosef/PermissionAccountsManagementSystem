from src.models.permission import Permission
from src.repositories.permissions_repo import PermissionsRepo
from src.models.exceptions import PermissionNotFoundError
from src.utils.validation import validate_update


def update_permission(tenant_id: str, permission_id: str, data: dict, repo: PermissionsRepo) -> Permission:
    valid_fields = validate_update(data)
    existing = repo.get(tenant_id, permission_id)
    if existing is None:
        raise PermissionNotFoundError(f"Permission {permission_id} not found")
    dynamo_fields = {}
    for key, value in valid_fields.items():
        if key == "schedule" and value is not None:
            dynamo_fields[key] = [e if isinstance(e, dict) else e for e in value]
        else:
            dynamo_fields[key] = value
    repo.update(tenant_id, permission_id, dynamo_fields)
    return repo.get(tenant_id, permission_id)
