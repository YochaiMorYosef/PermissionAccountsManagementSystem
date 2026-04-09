import json
import boto3


def send_message(queue_url: str, message_body: dict):
    boto3.client("sqs").send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message_body),
    )
