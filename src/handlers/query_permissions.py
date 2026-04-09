from src.bl.query_permissions import query_permissions
from src.repositories.permissions_repo import PermissionsRepo
from src.utils.jwt_parser import parse_jwt_claims, extract_tenant_id, JWTParseError
from src.utils import response as res
from src.utils.logger import get_logger

logger = get_logger(__name__)

ALLOWED_FILTER_PARAMS = {"user", "account_id", "permission"}


def handler(event, context):
    try:
        auth_header = (event.get("headers") or {}).get("Authorization") or \
                      (event.get("headers") or {}).get("authorization")
        claims = parse_jwt_claims(auth_header)
        tenant_id = extract_tenant_id(claims)
    except JWTParseError as e:
        return res.unauthorized(str(e))

    query_params = event.get("queryStringParameters") or {}
    filters = {k: v for k, v in query_params.items() if k in ALLOWED_FILTER_PARAMS and v}

    try:
        repo = PermissionsRepo()
        permissions = query_permissions(tenant_id, filters or None, repo)
        return res.success([p.to_dict() for p in permissions])
    except Exception:
        logger.exception("Unexpected error in query_permissions")
        return res.internal_error()
