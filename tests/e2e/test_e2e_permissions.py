import json
import os
import time
import jwt as pyjwt
import pytest
import requests

BASE_URL = os.environ.get(
    "E2E_BASE_URL",
    "https://fghthefamc.execute-api.us-east-1.amazonaws.com/dev",
)
JWT_SECRET = os.environ.get("E2E_JWT_SECRET", "secret")
TENANT_ID = "e2e-tenant"
USER = "e2e-alice"
ACCOUNT_ID = "e2e-acc-1"

MAX_WAIT_SECONDS = 60
POLL_INTERVAL = 5


def _token(tenant_id=TENANT_ID, sub=USER):
    return pyjwt.encode({"tenant_id": tenant_id, "sub": sub}, JWT_SECRET, algorithm="HS256")


def _headers(tenant_id=TENANT_ID, sub=USER):
    return {
        "Authorization": f"Bearer {_token(tenant_id, sub)}",
        "Content-Type": "application/json",
    }


def _url(path):
    return f"{BASE_URL}{path}"


def _poll_until(url, headers, condition, description):
    elapsed = 0
    while elapsed < MAX_WAIT_SECONDS:
        resp = requests.get(url, headers=headers)
        if condition(resp):
            return resp
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
    pytest.fail(f"Timed out waiting for: {description} (after {MAX_WAIT_SECONDS}s)")


# ── helpers to track resources for cleanup ──

_created_permission_ids: list[str] = []


@pytest.fixture(autouse=True)
def _cleanup():
    _created_permission_ids.clear()
    yield
    hdrs = _headers()
    for pid in _created_permission_ids:
        try:
            requests.delete(_url(f"/permissions/{pid}"), headers=hdrs)
        except Exception:
            pass


# ── tests ──


def test_unauthorized_without_token():
    resp = requests.post(
        _url("/permissions"),
        headers={"Content-Type": "application/json"},
        json={"user": USER, "account_id": ACCOUNT_ID, "permission": "read"},
    )
    assert resp.status_code == 401


def test_unauthorized_with_bad_token():
    resp = requests.get(
        _url("/permissions"),
        headers={"Authorization": "Bearer garbage.token.here"},
    )
    assert resp.status_code == 401


def test_create_returns_201_with_creating_status():
    resp = requests.post(
        _url("/permissions"),
        headers=_headers(),
        json={"user": USER, "account_id": ACCOUNT_ID, "permission": "read"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["tenant_id"] == TENANT_ID
    assert data["user"] == USER
    assert data["account_id"] == ACCOUNT_ID
    assert data["permission"] == "read"
    assert data["status"] == "Creating"
    assert data["permission_id"]
    _created_permission_ids.append(data["permission_id"])


def test_create_missing_fields_returns_400():
    resp = requests.post(
        _url("/permissions"),
        headers=_headers(),
        json={"user": USER},
    )
    assert resp.status_code == 400
    assert "error" in resp.json()


def test_get_nonexistent_returns_404():
    resp = requests.get(
        _url("/permissions/nonexistent-id"),
        headers=_headers(),
    )
    assert resp.status_code == 404


def test_full_create_lifecycle():
    create_resp = requests.post(
        _url("/permissions"),
        headers=_headers(),
        json={"user": USER, "account_id": ACCOUNT_ID, "permission": "lifecycle-test"},
    )
    assert create_resp.status_code == 201
    perm = create_resp.json()["data"]
    pid = perm["permission_id"]
    _created_permission_ids.append(pid)
    assert perm["status"] == "Creating"

    get_resp = requests.get(_url(f"/permissions/{pid}"), headers=_headers())
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["status"] == "Creating"

    final_resp = _poll_until(
        _url(f"/permissions/{pid}"),
        _headers(),
        lambda r: r.status_code == 200 and r.json()["data"]["status"] in ("Active", "FailedCreating"),
        f"permission {pid} to reach Active or FailedCreating",
    )
    final_status = final_resp.json()["data"]["status"]
    assert final_status in ("Active", "FailedCreating")


def test_update_permission():
    create_resp = requests.post(
        _url("/permissions"),
        headers=_headers(),
        json={"user": USER, "account_id": ACCOUNT_ID, "permission": "update-test"},
    )
    pid = create_resp.json()["data"]["permission_id"]
    _created_permission_ids.append(pid)

    update_resp = requests.patch(
        _url(f"/permissions/{pid}"),
        headers=_headers(),
        json={"permission": "updated-value"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["permission"] == "updated-value"


def test_update_nonexistent_returns_404():
    resp = requests.patch(
        _url("/permissions/nonexistent-id"),
        headers=_headers(),
        json={"permission": "new-value"},
    )
    assert resp.status_code == 404


def test_delete_returns_204_and_transitions_to_deleting():
    create_resp = requests.post(
        _url("/permissions"),
        headers=_headers(),
        json={"user": USER, "account_id": ACCOUNT_ID, "permission": "delete-test"},
    )
    pid = create_resp.json()["data"]["permission_id"]

    _poll_until(
        _url(f"/permissions/{pid}"),
        _headers(),
        lambda r: r.status_code == 200 and r.json()["data"]["status"] in ("Active", "FailedCreating"),
        f"permission {pid} to finish creating before delete test",
    )

    del_resp = requests.delete(_url(f"/permissions/{pid}"), headers=_headers())
    assert del_resp.status_code == 204
    assert del_resp.text == ""

    get_resp = requests.get(_url(f"/permissions/{pid}"), headers=_headers())
    assert get_resp.status_code == 200
    data = get_resp.json()["data"]
    assert data["status"] in ("Deleting", "FailedDeleting")


def test_delete_nonexistent_returns_404():
    resp = requests.delete(
        _url("/permissions/nonexistent-id"),
        headers=_headers(),
    )
    assert resp.status_code == 404


def test_full_delete_lifecycle():
    create_resp = requests.post(
        _url("/permissions"),
        headers=_headers(),
        json={"user": USER, "account_id": ACCOUNT_ID, "permission": "full-delete-test"},
    )
    pid = create_resp.json()["data"]["permission_id"]

    _poll_until(
        _url(f"/permissions/{pid}"),
        _headers(),
        lambda r: r.status_code == 200 and r.json()["data"]["status"] in ("Active", "FailedCreating"),
        f"permission {pid} to finish creating",
    )

    status_before_delete = requests.get(_url(f"/permissions/{pid}"), headers=_headers()).json()["data"]["status"]
    if status_before_delete != "Active":
        pytest.skip("Permission did not become Active (random failure from provision server); cannot test delete lifecycle")

    requests.delete(_url(f"/permissions/{pid}"), headers=_headers())

    result = _poll_until(
        _url(f"/permissions/{pid}"),
        _headers(),
        lambda r: r.status_code == 404 or (r.status_code == 200 and r.json()["data"]["status"] == "FailedDeleting"),
        f"permission {pid} to be deleted or reach FailedDeleting",
    )
    assert result.status_code in (404, 200)


def test_query_permissions():
    ids = []
    for perm_name in ("query-a", "query-b"):
        resp = requests.post(
            _url("/permissions"),
            headers=_headers(),
            json={"user": USER, "account_id": ACCOUNT_ID, "permission": perm_name},
        )
        ids.append(resp.json()["data"]["permission_id"])
        _created_permission_ids.append(ids[-1])

    query_resp = requests.get(
        _url(f"/permissions?user={USER}"),
        headers=_headers(),
    )
    assert query_resp.status_code == 200
    results = query_resp.json()["data"]
    returned_ids = {r["permission_id"] for r in results}
    for pid in ids:
        assert pid in returned_ids


def test_get_user_permissions_returns_only_active():
    create_resp = requests.post(
        _url("/permissions"),
        headers=_headers(),
        json={"user": USER, "account_id": ACCOUNT_ID, "permission": "me-test"},
    )
    pid = create_resp.json()["data"]["permission_id"]
    _created_permission_ids.append(pid)

    me_before = requests.get(
        _url(f"/permissions/me?account_id={ACCOUNT_ID}"),
        headers=_headers(),
    )
    assert me_before.status_code == 200
    before_actions = me_before.json()["data"]
    assert isinstance(before_actions, list)
    assert "me-test" not in before_actions, "Creating permission action should not appear in /me"

    _poll_until(
        _url(f"/permissions/{pid}"),
        _headers(),
        lambda r: r.status_code == 200 and r.json()["data"]["status"] in ("Active", "FailedCreating"),
        f"permission {pid} to finish creating",
    )

    final_status = requests.get(_url(f"/permissions/{pid}"), headers=_headers()).json()["data"]["status"]
    if final_status != "Active":
        pytest.skip("Permission did not become Active; cannot verify /me inclusion")

    me_after = requests.get(
        _url(f"/permissions/me?account_id={ACCOUNT_ID}"),
        headers=_headers(),
    )
    assert me_after.status_code == 200
    after_actions = me_after.json()["data"]
    assert isinstance(after_actions, list)
    assert "me-test" in after_actions, "Active permission action should appear in /me"


def test_tenant_isolation():
    create_resp = requests.post(
        _url("/permissions"),
        headers=_headers(tenant_id="e2e-tenant-A"),
        json={"user": USER, "account_id": ACCOUNT_ID, "permission": "isolated"},
    )
    pid = create_resp.json()["data"]["permission_id"]

    get_from_other = requests.get(
        _url(f"/permissions/{pid}"),
        headers=_headers(tenant_id="e2e-tenant-B"),
    )
    assert get_from_other.status_code == 404

    requests.delete(_url(f"/permissions/{pid}"), headers=_headers(tenant_id="e2e-tenant-A"))


def test_create_with_schedule():
    resp = requests.post(
        _url("/permissions"),
        headers=_headers(),
        json={
            "user": USER,
            "account_id": ACCOUNT_ID,
            "permission": "scheduled",
            "schedule": [{"weekday": 0, "start_time": "09:00", "end_time": "17:00"}],
        },
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    _created_permission_ids.append(data["permission_id"])
    assert data["schedule"] is not None
    assert len(data["schedule"]) == 1
    assert data["schedule"][0]["weekday"] == 0


def test_create_without_schedule_is_always_active():
    resp = requests.post(
        _url("/permissions"),
        headers=_headers(),
        json={"user": USER, "account_id": ACCOUNT_ID, "permission": "no-schedule"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    _created_permission_ids.append(data["permission_id"])
    assert data["schedule"] is None
