import json
import os
from src.bl.create_permission import create_permission
from src.repositories.permissions_repo import PermissionsRepo
from src.utils.jwt_parser import parse_jwt_claims, extract_tenant_id, JWTParseError
from src.utils.validation import ValidationError
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
