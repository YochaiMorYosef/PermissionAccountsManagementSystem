import json
from src.bl.process_permission import process_permission
from src.repositories.permissions_repo import PermissionsRepo
from src.utils.logger import get_logger

logger = get_logger(__name__)


def handler(event, context):
    for record in event["Records"]:
        message = json.loads(record["body"])
        repo = PermissionsRepo()
        try:
            process_permission(message, repo)
        except Exception:
            logger.exception("Failed to process permission message", extra={"sqs_message": message})
            raise
