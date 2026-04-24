from src.models.permission import Permission
from src.repositories.permissions_repo import PermissionsRepo


def query_permissions(
    tenant_id: str,
    filters: dict | None,
    repo: PermissionsRepo,
    limit: int | None = None,
    exclusive_start_key: dict | None = None,
) -> tuple[list[Permission], dict | None]:
    if limit is None and exclusive_start_key is None:
        return repo.query(tenant_id, filters or None)

    return repo.query(
        tenant_id,
        filters or None,
        limit=limit,
        exclusive_start_key=exclusive_start_key,
    )