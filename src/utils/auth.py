from src.utils.jwt_parser import parse_jwt_claims, extract_tenant_id, extract_user, JWTParseError

class AuthorizationError(Exception):
    pass

def get_claims_from_event(event):
    auth_header = (event.get("headers") or {}).get("Authorization") or \
                  (event.get("headers") or {}).get("authorization")
    return parse_jwt_claims(auth_header)

def require_admin(event):
    claims = get_claims_from_event(event)
    tenant_id = extract_tenant_id(claims)
    role = claims.get("role")
    if role is not None and role != "admin":
        raise AuthorizationError("Admin role required")
    return claims, tenant_id

def require_authenticated_user(event):
    claims = get_claims_from_event(event)
    tenant_id = extract_tenant_id(claims)
    user = extract_user(claims)
    return claims, tenant_id, user