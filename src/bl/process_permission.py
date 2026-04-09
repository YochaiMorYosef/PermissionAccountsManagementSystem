import os
import requests
from src.models.permission_status import PermissionStatus
from src.repositories.permissions_repo import PermissionsRepo

PROVISIONING_URL = os.environ.get("PROVISIONING_URL", "")
DEMO_AUTH_TOKEN = os.environ.get("DEMO_AUTH_TOKEN", "")


def process_permission(message: dict, repo: PermissionsRepo):
    action = message["action"]
    tenant_id = message["tenant_id"]
    permission_id = message["permission_id"]
    permission_data = message["permission_data"]

    headers = {"X-Demo-Auth": DEMO_AUTH_TOKEN}
    response = requests.post(PROVISIONING_URL, json=permission_data, headers=headers, timeout=30)

    if action == "create":
        status = PermissionStatus.ACTIVE if response.ok else PermissionStatus.FAILED_CREATING
        repo.update(tenant_id, permission_id, {"status": status})
    elif action == "delete":
        if response.ok:
            repo.delete(tenant_id, permission_id)
        else:
            repo.update(tenant_id, permission_id, {"status": PermissionStatus.FAILED_DELETING})
