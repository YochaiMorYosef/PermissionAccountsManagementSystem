import json
from src.bl.update_permission import update_permission
from src.models.exceptions import PermissionNotFoundError
from src.repositories.permissions_repo import PermissionsRepo
from src.utils.auth import require_admin, AuthorizationError
from src.utils.jwt_parser import JWTParseError
from src.utils.validation import ValidationError
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
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return res.bad_request("Invalid JSON body")

    try:
        repo = PermissionsRepo()
        permission = update_permission(tenant_id, permission_id, body, repo)
        logger.info("Permission updated", extra={"tenant_id": tenant_id})
        return res.success(permission.to_dict())
    except ValidationError as e:
        return res.bad_request(str(e))
    except PermissionNotFoundError as e:
        return res.not_found(str(e))
    except Exception:
        logger.exception("Unexpected error in update_permission")
        return res.internal_error()
