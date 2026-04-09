import os
from src.bl.delete_permission import delete_permission
from src.models.exceptions import PermissionNotFoundError
from src.repositories.permissions_repo import PermissionsRepo
from src.utils.jwt_parser import parse_jwt_claims, extract_tenant_id, JWTParseError
from src.utils import response as res
from src.utils.logger import get_logger

logger = get_logger(__name__)


def handler(event, context):
    try:
        auth_header = (event.get("headers") or {}).get("Authorization") or \
                      (event.get("headers") or {}).get("authorization")
        claims = parse_jwt_claims(auth_header)
        tenant_id = extract_tenant_id(claims)
    except JWTParseError as e:
        return res.unauthorized(str(e))

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
