from enum import Enum


class PermissionStatus(str, Enum):
    CREATING = "Creating"
    ACTIVE = "Active"
    FAILED_CREATING = "FailedCreating"
    DELETING = "Deleting"
    FAILED_DELETING = "FailedDeleting"
