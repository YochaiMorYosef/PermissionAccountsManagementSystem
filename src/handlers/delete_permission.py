import os
from src.bl.delete_permission import delete_permission
from src.models.exceptions import PermissionNotFoundError
from src.repositories.permissions_repo import PermissionsRepo
from src.utils.auth import require_admin, AuthorizationError
from src.utils.jwt_parser import JWTParseError
from src.utils import response as res
from src.utils.logger import get_logger

logger = get_logger(__name__)


def handler(event, context):
    try:
        _, tenant_id = require_admin(event)
    except JWTParseError as e:
        return res.unauthorized(str(e))
    except AuthorizationError as e:
        return res.forbidden(str(e))

    permission_id = (event.get("pathParameters") or {}).get("permission_id")
    if not permission_id:
        return res.bad_request("Missing permission_id path parameter")

    try:
        repo = PermissionsRepo()
        delete_permission(tenant_id, permission_id, repo, os.environ["QUEUE_URL"])
        logger.info("Permission deleting", extra={"tenant_id": tenant_id})
        return res.no_content()
    except PermissionNotFoundError as e:
        return res.not_found(str(e))
    except Exception:
        logger.exception("Unexpected error in delete_permission")
        return res.internal_error()
