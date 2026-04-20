import base64
import json
from src.bl.query_permissions import query_permissions
from src.repositories.permissions_repo import PermissionsRepo
from src.utils.auth import require_admin, AuthorizationError
from src.utils.jwt_parser import JWTParseError
from src.utils import response as res
from src.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_LIMIT = 50
MAX_LIMIT = 100


def _decode_cursor(cursor: str) -> dict | None:
    try:
        return json.loads(base64.urlsafe_b64decode(cursor.encode()))
    except Exception:
        return None


def _encode_cursor(last_key: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(last_key).encode()).decode()


def handler(event, context):
    try:
        _, tenant_id = require_admin(event)
    except JWTParseError as e:
        return res.unauthorized(str(e))
    except AuthorizationError as e:
        return res.forbidden(str(e))

    query_params = event.get("queryStringParameters") or {}

    try:
        limit = min(int(query_params.get("limit", DEFAULT_LIMIT)), MAX_LIMIT)
    except (ValueError, TypeError):
        limit = DEFAULT_LIMIT

    cursor_param = query_params.get("cursor")
    exclusive_start_key = _decode_cursor(cursor_param) if cursor_param else None

    try:
        repo = PermissionsRepo()
        permissions, last_key = query_permissions(
            tenant_id, None, repo, limit=limit, exclusive_start_key=exclusive_start_key
        )
        return res.success({
            "items": [p.to_dict() for p in permissions],
            "next_cursor": _encode_cursor(last_key) if last_key else None,
        })
    except Exception:
        logger.exception("Unexpected error in query_permissions")
        return res.internal_error()
