import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from src.models.permission import Permission


class PermissionsRepo:
    def __init__(self):
        self._table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])

    def put(self, permission: Permission):
        self._table.put_item(Item=permission.to_dynamo_item())

    def get(self, tenant_id: str, permission_id: str) -> Permission | None:
        response = self._table.get_item(
            Key={"tenant_id": tenant_id, "permission_id": permission_id}
        )
        item = response.get("Item")
        if item is None:
            return None
        return Permission.from_dynamo_item(item)

    def update(self, tenant_id: str, permission_id: str, fields: dict):
        update_parts = []
        names = {}
        values = {}
        for i, (key, value) in enumerate(fields.items()):
            placeholder_name = f"#f{i}"
            placeholder_value = f":v{i}"
            update_parts.append(f"{placeholder_name} = {placeholder_value}")
            names[placeholder_name] = key
            if value is None:
                values[placeholder_value] = None
            else:
                values[placeholder_value] = value
        update_expression = "SET " + ", ".join(update_parts)
        self._table.update_item(
            Key={"tenant_id": tenant_id, "permission_id": permission_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
        )

    def delete(self, tenant_id: str, permission_id: str):
        self._table.delete_item(
            Key={"tenant_id": tenant_id, "permission_id": permission_id}
        )

    def query(
        self,
        tenant_id: str,
        filters: dict | None = None,
        limit: int | None = None,
        exclusive_start_key: dict | None = None,
    ) -> tuple[list[Permission], dict | None]:
        key_condition = Key("tenant_id").eq(tenant_id)
        kwargs = {"KeyConditionExpression": key_condition}
        if filters:
            filter_expressions = [Attr(k).eq(v) for k, v in filters.items()]
            combined = filter_expressions[0]
            for expr in filter_expressions[1:]:
                combined = combined & expr
            kwargs["FilterExpression"] = combined
        if limit is not None:
            # Single-page call — return items and the cursor for the next page
            if exclusive_start_key:
                kwargs["ExclusiveStartKey"] = exclusive_start_key
            kwargs["Limit"] = limit
            response = self._table.query(**kwargs)
            items = [Permission.from_dynamo_item(i) for i in response.get("Items", [])]
            return items, response.get("LastEvaluatedKey")
        # No limit — exhaust all
        response = self._table.query(**kwargs)
        return [Permission.from_dynamo_item(item) for item in response.get("Items", [])], None
