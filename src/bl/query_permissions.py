from src.models.permission import Permission
from src.repositories.permissions_repo import PermissionsRepo


def query_permissions(tenant_id: str, filters: dict | None, repo: PermissionsRepo) -> list[Permission]:
    return repo.query(tenant_id, filters or None)
