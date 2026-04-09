import jwt


class JWTParseError(Exception):
    pass


def parse_jwt_claims(authorization_header: str) -> dict:
    if not authorization_header:
        raise JWTParseError("Missing Authorization header")
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise JWTParseError("Invalid Authorization header format")
    token = parts[1]
    try:
        claims = jwt.decode(token, options={"verify_signature": False})
    except jwt.DecodeError as e:
        raise JWTParseError(f"Failed to decode JWT: {e}")
    return claims


def extract_tenant_id(claims: dict) -> str:
    tenant_id = claims.get("tenant_id")
    if not tenant_id:
        raise JWTParseError("Missing tenant_id claim in JWT")
    return tenant_id


def extract_user(claims: dict) -> str:
    user = claims.get("sub")
    if not user:
        raise JWTParseError("Missing sub claim in JWT")
    return user
