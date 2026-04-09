import json
import os
import pytest
import boto3
import jwt as pyjwt
from moto import mock_aws


TABLE_NAME = "permissions-test"
QUEUE_NAME = "permissions-test-queue"

os.environ["TABLE_NAME"] = TABLE_NAME
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["PROVISIONING_URL"] = "http://example.com/provision"


def _make_token(tenant_id="tenant-1", sub="alice"):
    return pyjwt.encode({"tenant_id": tenant_id, "sub": sub}, "secret", algorithm="HS256")


def _auth_header(tenant_id="tenant-1", sub="alice"):
    return {"Authorization": f"Bearer {_make_token(tenant_id, sub)}"}


def _create_table():
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    dynamodb.create_table(
        TableName=TABLE_NAME,
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[
            {"AttributeName": "tenant_id", "AttributeType": "S"},
            {"AttributeName": "permission_id", "AttributeType": "S"},
        ],
        KeySchema=[
            {"AttributeName": "tenant_id", "KeyType": "HASH"},
            {"AttributeName": "permission_id", "KeyType": "RANGE"},
        ],
    )


def _create_queue():
    sqs = boto3.client("sqs", region_name="us-east-1")
    response = sqs.create_queue(QueueName=QUEUE_NAME)
    os.environ["QUEUE_URL"] = response["QueueUrl"]


def _set_permission_status_active(permission_id: str, tenant_id: str = "tenant-1"):
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table(TABLE_NAME)
    table.update_item(
        Key={"tenant_id": tenant_id, "permission_id": permission_id},
        UpdateExpression="SET #s = :v",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":v": "Active"},
    )


@mock_aws
def test_create_and_get_permission():
    _create_table()
    _create_queue()
    from src.handlers import create_permission as create_handler
    from src.handlers import get_permission as get_handler

    event = {
        "headers": _auth_header(),
        "body": json.dumps({"user": "alice", "account_id": "acc-1", "permission": "read"}),
        "pathParameters": None,
        "queryStringParameters": None,
    }
    create_response = create_handler.handler(event, {})
    assert create_response["statusCode"] == 201
    created = json.loads(create_response["body"])["data"]
    permission_id = created["permission_id"]
    assert created["status"] == "Creating"

    get_event = {
        "headers": _auth_header(),
        "pathParameters": {"permission_id": permission_id},
        "queryStringParameters": None,
    }
    get_response = get_handler.handler(get_event, {})
    assert get_response["statusCode"] == 200
    fetched = json.loads(get_response["body"])["data"]
    assert fetched["permission_id"] == permission_id
    assert fetched["user"] == "alice"
    assert fetched["status"] == "Creating"


@mock_aws
def test_create_missing_fields_returns_400():
    _create_table()
    _create_queue()
    from src.handlers import create_permission as create_handler

    event = {
        "headers": _auth_header(),
        "body": json.dumps({"user": "alice"}),
        "pathParameters": None,
        "queryStringParameters": None,
    }
    response = create_handler.handler(event, {})
    assert response["statusCode"] == 400


@mock_aws
def test_get_nonexistent_permission_returns_404():
    _create_table()
    _create_queue()
    from src.handlers import get_permission as get_handler

    event = {
        "headers": _auth_header(),
        "pathParameters": {"permission_id": "does-not-exist"},
        "queryStringParameters": None,
    }
    response = get_handler.handler(event, {})
    assert response["statusCode"] == 404


@mock_aws
def test_update_permission():
    _create_table()
    _create_queue()
    from src.handlers import create_permission as create_handler
    from src.handlers import update_permission as update_handler

    create_event = {
        "headers": _auth_header(),
        "body": json.dumps({"user": "alice", "account_id": "acc-1", "permission": "read"}),
        "pathParameters": None,
        "queryStringParameters": None,
    }
    created = json.loads(create_handler.handler(create_event, {})["body"])["data"]
    permission_id = created["permission_id"]

    update_event = {
        "headers": _auth_header(),
        "body": json.dumps({"permission": "write"}),
        "pathParameters": {"permission_id": permission_id},
        "queryStringParameters": None,
    }
    response = update_handler.handler(update_event, {})
    assert response["statusCode"] == 200
    updated = json.loads(response["body"])["data"]
    assert updated["permission"] == "write"


@mock_aws
def test_delete_permission_returns_204_and_sets_deleting_status():
    _create_table()
    _create_queue()
    from src.handlers import create_permission as create_handler
    from src.handlers import delete_permission as delete_handler
    from src.handlers import get_permission as get_handler

    create_event = {
        "headers": _auth_header(),
        "body": json.dumps({"user": "alice", "account_id": "acc-1", "permission": "read"}),
        "pathParameters": None,
        "queryStringParameters": None,
    }
    created = json.loads(create_handler.handler(create_event, {})["body"])["data"]
    permission_id = created["permission_id"]

    delete_event = {
        "headers": _auth_header(),
        "pathParameters": {"permission_id": permission_id},
        "queryStringParameters": None,
    }
    delete_response = delete_handler.handler(delete_event, {})
    assert delete_response["statusCode"] == 204
    assert delete_response["body"] == ""

    get_event = {
        "headers": _auth_header(),
        "pathParameters": {"permission_id": permission_id},
        "queryStringParameters": None,
    }
    get_response = get_handler.handler(get_event, {})
    assert get_response["statusCode"] == 200
    fetched = json.loads(get_response["body"])["data"]
    assert fetched["status"] == "Deleting"


@mock_aws
def test_delete_nonexistent_permission_returns_404():
    _create_table()
    _create_queue()
    from src.handlers import delete_permission as delete_handler

    event = {
        "headers": _auth_header(),
        "pathParameters": {"permission_id": "does-not-exist"},
        "queryStringParameters": None,
    }
    response = delete_handler.handler(event, {})
    assert response["statusCode"] == 404


@mock_aws
def test_query_permissions_with_filter():
    _create_table()
    _create_queue()
    from src.handlers import create_permission as create_handler
    from src.handlers import query_permissions as query_handler

    for user in ("alice", "alice", "bob"):
        create_handler.handler({
            "headers": _auth_header(),
            "body": json.dumps({"user": user, "account_id": "acc-1", "permission": "read"}),
            "pathParameters": None,
            "queryStringParameters": None,
        }, {})

    query_event = {
        "headers": _auth_header(),
        "pathParameters": None,
        "queryStringParameters": {"user": "alice"},
    }
    response = query_handler.handler(query_event, {})
    assert response["statusCode"] == 200
    results = json.loads(response["body"])["data"]
    assert len(results) == 2
    assert all(r["user"] == "alice" for r in results)


@mock_aws
def test_unauthorized_when_no_auth_header():
    _create_table()
    _create_queue()
    from src.handlers import create_permission as create_handler

    event = {
        "headers": {},
        "body": json.dumps({"user": "alice", "account_id": "acc-1", "permission": "read"}),
        "pathParameters": None,
        "queryStringParameters": None,
    }
    response = create_handler.handler(event, {})
    assert response["statusCode"] == 401


@mock_aws
def test_get_user_permissions_returns_active_only():
    _create_table()
    _create_queue()
    from src.handlers import create_permission as create_handler
    from src.handlers import get_user_permissions as gup_handler
    from datetime import datetime, timezone
    from unittest.mock import patch

    create_response = create_handler.handler({
        "headers": _auth_header(),
        "body": json.dumps({"user": "alice", "account_id": "acc-1", "permission": "always-on"}),
        "pathParameters": None,
        "queryStringParameters": None,
    }, {})
    always_on_id = json.loads(create_response["body"])["data"]["permission_id"]

    create_handler.handler({
        "headers": _auth_header(),
        "body": json.dumps({
            "user": "alice",
            "account_id": "acc-1",
            "permission": "night-only",
            "schedule": [{"weekday": 0, "start_time": "22:00", "end_time": "23:59"}],
        }),
        "pathParameters": None,
        "queryStringParameters": None,
    }, {})

    _set_permission_status_active(always_on_id)

    monday_noon = datetime(2026, 3, 9, 12, 0, tzinfo=timezone.utc)
    with patch("src.bl.get_user_permissions.datetime") as mock_dt:
        mock_dt.now.return_value = monday_noon
        response = gup_handler.handler({
            "headers": _auth_header(),
            "pathParameters": None,
            "queryStringParameters": {"account_id": "acc-1"},
        }, {})

    assert response["statusCode"] == 200
    results = json.loads(response["body"])["data"]
    assert "always-on" in results
    assert "night-only" not in results
