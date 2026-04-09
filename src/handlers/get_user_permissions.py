from src.bl.get_user_permissions import get_user_permissions
from src.repositories.permissions_repo import PermissionsRepo
from src.utils.jwt_parser import parse_jwt_claims, extract_tenant_id, extract_user, JWTParseError
from src.utils import response as res
from src.utils.logger import get_logger

logger = get_logger(__name__)


def handler(event, context):
    try:
        auth_header = (event.get("headers") or {}).get("Authorization") or \
                      (event.get("headers") or {}).get("authorization")
        claims = parse_jwt_claims(auth_header)
        tenant_id = extract_tenant_id(claims)
        user = extract_user(claims)
    except JWTParseError as e:
        return res.unauthorized(str(e))

    query_params = event.get("queryStringParameters") or {}
    account_id = query_params.get("account_id")
    if not account_id:
        return res.bad_request("Missing required query parameter: account_id")

    try:
        repo = PermissionsRepo()
        permissions = get_user_permissions(tenant_id, user, account_id, repo)
        return res.success(sorted(set(p.permission for p in permissions)))
    except Exception:
        logger.exception("Unexpected error in get_user_permissions")
        return res.internal_error()
