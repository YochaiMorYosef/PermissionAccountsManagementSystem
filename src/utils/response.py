import json

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,PATCH,DELETE,OPTIONS",
}

BASE_HEADERS = {
    **CORS_HEADERS,
    "Content-Type": "application/json",
}


def success(data, status_code: int = 200) -> dict:
    return {
        "statusCode": status_code,
        "headers": BASE_HEADERS,
        "body": json.dumps({"data": data}),
    }


def no_content() -> dict:
    return {
        "statusCode": 204,
        "headers": BASE_HEADERS,
        "body": "",
    }


def error(message: str, status_code: int) -> dict:
    return {
        "statusCode": status_code,
        "headers": BASE_HEADERS,
        "body": json.dumps({"error": {"message": message}}),
    }


def bad_request(message: str) -> dict:
    return error(message, 400)


def unauthorized(message: str = "Unauthorized") -> dict:
    return error(message, 401)


def forbidden(message: str = "Forbidden") -> dict:
    return error(message, 403)


def not_found(message: str = "Not found") -> dict:
    return error(message, 404)


def internal_error(message: str = "Internal server error") -> dict:
    return error(message, 500)
