import json
import os
from src.bl.create_permission import create_permission
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

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return res.bad_request("Invalid JSON body")

    try:
        repo = PermissionsRepo()
        permission = create_permission(tenant_id, body, repo, os.environ["QUEUE_URL"])
        logger.info("Permission created", extra={"tenant_id": tenant_id})
        return res.success(permission.to_dict(), status_code=201)
    except ValidationError as e:
        return res.bad_request(str(e))
    except Exception:
        logger.exception("Unexpected error in create_permission")
        return res.internal_error()
