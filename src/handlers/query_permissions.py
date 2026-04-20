from src.bl.query_permissions import query_permissions
from src.repositories.permissions_repo import PermissionsRepo
from src.utils.auth import require_admin, AuthorizationError
from src.utils.jwt_parser import JWTParseError
from src.utils import response as res
from src.utils.logger import get_logger

logger = get_logger(__name__)

ALLOWED_FILTER_PARAMS = {"user", "account_id", "permission"}


def handler(event, context):
    try:
        _, tenant_id = require_admin(event)
    except JWTParseError as e:
        return res.unauthorized(str(e))
    except AuthorizationError as e:
        return res.forbidden(str(e))

    query_params = event.get("queryStringParameters") or {}
    filters = {k: v for k, v in query_params.items() if k in ALLOWED_FILTER_PARAMS and v}

    try:
        repo = PermissionsRepo()
        permissions = query_permissions(tenant_id, filters or None, repo)
        return res.success([p.to_dict() for p in permissions])
    except Exception:
        logger.exception("Unexpected error in query_permissions")
        return res.internal_error()
