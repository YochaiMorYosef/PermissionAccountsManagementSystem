import pytest
from unittest.mock import MagicMock, patch
from src.bl.process_permission import process_permission
from src.models.permission_status import PermissionStatus


def _make_message(action="create", permission_id="perm-1"):
    return {
        "action": action,
        "tenant_id": "tenant-1",
        "permission_id": permission_id,
        "permission_data": {
            "tenant_id": "tenant-1",
            "permission_id": permission_id,
            "user": "alice",
            "account_id": "acc-1",
            "permission": "read",
            "status": "Creating",
            "schedule": None,
        },
    }


def _mock_response(ok=True, status_code=200):
    resp = MagicMock()
    resp.ok = ok
    resp.status_code = status_code
    return resp


def test_create_action_http_success_sets_active():
    repo = MagicMock()
    with patch("src.bl.process_permission.requests.post", return_value=_mock_response(ok=True)):
        process_permission(_make_message(action="create"), repo)
    repo.update.assert_called_once_with("tenant-1", "perm-1", {"status": PermissionStatus.ACTIVE})
    repo.delete.assert_not_called()


def test_create_action_http_failure_sets_failed_creating():
    repo = MagicMock()
    with patch("src.bl.process_permission.requests.post", return_value=_mock_response(ok=False, status_code=500)):
        process_permission(_make_message(action="create"), repo)
    repo.update.assert_called_once_with("tenant-1", "perm-1", {"status": PermissionStatus.FAILED_CREATING})
    repo.delete.assert_not_called()


def test_delete_action_http_success_deletes_record():
    repo = MagicMock()
    with patch("src.bl.process_permission.requests.post", return_value=_mock_response(ok=True)):
        process_permission(_make_message(action="delete"), repo)
    repo.delete.assert_called_once_with("tenant-1", "perm-1")
    repo.update.assert_not_called()


def test_delete_action_http_failure_sets_failed_deleting():
    repo = MagicMock()
    with patch("src.bl.process_permission.requests.post", return_value=_mock_response(ok=False, status_code=503)):
        process_permission(_make_message(action="delete"), repo)
    repo.update.assert_called_once_with("tenant-1", "perm-1", {"status": PermissionStatus.FAILED_DELETING})
    repo.delete.assert_not_called()


def test_http_post_called_with_permission_data():
    repo = MagicMock()
    msg = _make_message(action="create")
    with patch("src.bl.process_permission.requests.post", return_value=_mock_response()) as mock_post:
        process_permission(msg, repo)
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["json"] == msg["permission_data"]
