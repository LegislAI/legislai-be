import uuid
from datetime import datetime
from datetime import timezone
from typing import Dict

import boto3
from authentication.config.settings import settings
from authentication.utils.logging_config import logger
from authentication.utils.schemas import RegisterUserRequest
from botocore.exceptions import ClientError


boto3_client = boto3.client(
    "dynamodb",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region,
)


def get_user(boto3_client, email: str) -> Dict:
    """
    Fetch a user by email from the DynamoDB table.
    """
    try:
        response = boto3_client.query(
            TableName="users",
            IndexName="EmailIndex",
            KeyConditionExpression="email = :email",
            ExpressionAttributeValues={":email": {"S": email}},
            ProjectionExpression="userid, email, username, password",
        )

        if response["Items"]:
            user = response["Items"][0]
            return {
                "userid": user["userid"]["S"],
                "email": user["email"]["S"],
                "username": user["username"]["S"],
                "password": user["password"]["S"],
            }

    except ClientError as e:
        logger.error(f"Error fetching user: {e.response['Error']['Message']}")
        return {}


def create_user(db, user_data: RegisterUserRequest) -> Dict:
    """
    Create a new user in the DynamoDB table.
    """
    email, username, password = user_data.email, user_data.username, user_data.password
    user_id = str(uuid.uuid4())

    try:
        db.put_item(
            TableName="users",
            Item={
                "userid": {"S": user_id},
                "email": {"S": email},
                "username": {"S": username},
                "password": {"S": password},
                "usercreated": {"S": str(datetime.now(timezone.utc))},
                "lastlogin": {"S": str(datetime.now(timezone.utc))},
            },
        )
        logger.info(f"User with email {email} created!")
        return {
            "userid": user_id,
            "email": email,
            "username": username,
            "password": password,
        }

    except ClientError as e:
        logger.error(f"Error creating user: {e.response['Error']['Message']}")
        return {}


def update_user_fields(db, userid: str, email: str, fields: Dict[str, str]) -> bool:
    """
    Update specified fields for the user in the DynamoDB table.

    :param db: DynamoDB client
    :param userid: User's unique ID (partition key)
    :param email: User's email (sort key)
    :param fields: A dictionary of fields to update, e.g., {"lastlogin": "new_value"}
    :return: True if the update was successful, False otherwise
    """
    update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in fields.keys())
    expression_attribute_values = {f":{k}": {"S": v} for k, v in fields.items()}

    try:
        db.update_item(
            TableName="users",
            Key={
                "userid": {"S": userid},  # Partition key
                "email": {"S": email},  # Sort key
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
        )
        logger.info("User updated!")
        return True

    except ClientError as e:
        logger.error(f"Error updating user fields: {e.response['Error']['Message']}")
        return False
