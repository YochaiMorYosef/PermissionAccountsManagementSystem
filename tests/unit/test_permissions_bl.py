import pytest
from unittest.mock import MagicMock, patch
from src.bl.create_permission import create_permission
from src.bl.get_permission import get_permission
from src.bl.update_permission import update_permission
from src.bl.delete_permission import delete_permission
from src.bl.query_permissions import query_permissions
from src.models.exceptions import PermissionNotFoundError
from src.models.permission import Permission
from src.models.permission_status import PermissionStatus
from src.utils.validation import ValidationError


def _make_perm(permission_id="perm-1", status=PermissionStatus.ACTIVE):
    return Permission(
        tenant_id="tenant-1",
        permission_id=permission_id,
        user="alice",
        account_id="acc-1",
        permission="read",
        status=status,
        schedule=None,
    )


def test_create_permission_calls_repo_put():
    repo = MagicMock()
    with patch("src.bl.create_permission.send_message"):
        data = {"user": "alice", "account_id": "acc-1", "permission": "read"}
        result = create_permission("tenant-1", data, repo, "http://queue")
    repo.put.assert_called_once()
    assert result.tenant_id == "tenant-1"
    assert result.user == "alice"
    assert result.status == PermissionStatus.CREATING


def test_create_permission_sends_sqs_message():
    repo = MagicMock()
    with patch("src.bl.create_permission.send_message") as mock_send:
        data = {"user": "alice", "account_id": "acc-1", "permission": "read"}
        result = create_permission("tenant-1", data, repo, "http://queue")
    mock_send.assert_called_once()
    call_args = mock_send.call_args
    assert call_args[0][0] == "http://queue"
    assert call_args[0][1]["action"] == "create"
    assert call_args[0][1]["permission_id"] == result.permission_id


def test_create_permission_validation_error():
    repo = MagicMock()
    with patch("src.bl.create_permission.send_message"):
        with pytest.raises(ValidationError):
            create_permission("tenant-1", {"user": "alice"}, repo, "http://queue")
    repo.put.assert_not_called()


def test_get_permission_found():
    repo = MagicMock()
    repo.get.return_value = _make_perm()
    result = get_permission("tenant-1", "perm-1", repo)
    assert result.permission_id == "perm-1"


def test_get_permission_not_found():
    repo = MagicMock()
    repo.get.return_value = None
    with pytest.raises(PermissionNotFoundError):
        get_permission("tenant-1", "perm-1", repo)


def test_update_permission_not_found():
    repo = MagicMock()
    repo.get.return_value = None
    with pytest.raises(PermissionNotFoundError):
        update_permission("tenant-1", "perm-1", {"user": "bob"}, repo)


def test_update_permission_calls_repo_update():
    perm = _make_perm()
    repo = MagicMock()
    repo.get.return_value = perm
    update_permission("tenant-1", "perm-1", {"user": "bob"}, repo)
    repo.update.assert_called_once()


def test_delete_permission_not_found():
    repo = MagicMock()
    repo.get.return_value = None
    with pytest.raises(PermissionNotFoundError):
        delete_permission("tenant-1", "perm-1", repo, "http://queue")


def test_delete_permission_updates_status_to_deleting():
    repo = MagicMock()
    repo.get.return_value = _make_perm()
    with patch("src.bl.delete_permission.send_message"):
        delete_permission("tenant-1", "perm-1", repo, "http://queue")
    repo.update.assert_called_once_with("tenant-1", "perm-1", {"status": PermissionStatus.DELETING})
    repo.delete.assert_not_called()


def test_delete_permission_sends_sqs_message():
    repo = MagicMock()
    repo.get.return_value = _make_perm()
    with patch("src.bl.delete_permission.send_message") as mock_send:
        delete_permission("tenant-1", "perm-1", repo, "http://queue")
    mock_send.assert_called_once()
    call_args = mock_send.call_args
    assert call_args[0][0] == "http://queue"
    assert call_args[0][1]["action"] == "delete"
    assert call_args[0][1]["permission_id"] == "perm-1"


def test_query_permissions_passes_filters():
    repo = MagicMock()
    repo.query.return_value = []
    result = query_permissions("tenant-1", {"user": "alice"}, repo)
    repo.query.assert_called_once_with("tenant-1", {"user": "alice"})
    assert result == []
