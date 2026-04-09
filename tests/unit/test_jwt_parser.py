import pytest
import jwt as pyjwt
from src.utils.jwt_parser import parse_jwt_claims, extract_tenant_id, extract_user, JWTParseError


def _make_token(payload: dict) -> str:
    return pyjwt.encode(payload, "secret", algorithm="HS256")


def test_parse_valid_token():
    token = _make_token({"tenant_id": "t1", "sub": "user1"})
    claims = parse_jwt_claims(f"Bearer {token}")
    assert claims["tenant_id"] == "t1"
    assert claims["sub"] == "user1"


def test_parse_missing_header():
    with pytest.raises(JWTParseError):
        parse_jwt_claims(None)


def test_parse_empty_header():
    with pytest.raises(JWTParseError):
        parse_jwt_claims("")


def test_parse_malformed_header():
    with pytest.raises(JWTParseError):
        parse_jwt_claims("NotBearer token")


def test_parse_invalid_token():
    with pytest.raises(JWTParseError):
        parse_jwt_claims("Bearer not.a.jwt")


def test_extract_tenant_id_present():
    claims = {"tenant_id": "tenant-abc"}
    assert extract_tenant_id(claims) == "tenant-abc"


def test_extract_tenant_id_missing():
    with pytest.raises(JWTParseError):
        extract_tenant_id({})


def test_extract_user_present():
    claims = {"sub": "alice"}
    assert extract_user(claims) == "alice"


def test_extract_user_missing():
    with pytest.raises(JWTParseError):
        extract_user({})
