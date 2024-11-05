import uuid
from datetime import datetime
from datetime import timezone
from typing import Dict

import boto3
from users.config.settings import settings
from users.utils.exceptions import UserNotFoundException
from users.utils.logging_config import logger
from users.utils.password import SecurityUtils
from users.utils.users import decodeJWT
from users.utils.schemas import UsersResponse
from users.utils.schemas import UsersPlanResponse
from users.utils.schemas import UsersRequestPayload
from botocore.exceptions import ClientError

security = SecurityUtils()
boto3_client = boto3.client(
    "dynamodb",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region,
)


def get_user_by_email(email: str) -> UsersResponse:
    """
    Fetch a user by email from the DynamoDB table.
    """
    try:
        response = boto3_client.query(
            TableName="users",
            IndexName="EmailIndex",
            KeyConditionExpression="email = :email",
            ExpressionAttributeValues={":email": {"S": email}},
            ProjectionExpression="user_id, email, username, password, plan_name",
        )

        if not response["Items"]:
            logger.error(f"User with email {email} not found")
            raise UserNotFoundException(f"User with email {email} not found")

        user = response["Items"][0]
        return UsersResponse(
            user_id=user["user_id"]["S"],
            email=user["email"]["S"],
            username=user["username"]["S"],
            plan=user["plan_name"]["S"],
        )

    except ClientError as e:
        logger.error(f"Error fetching user: {e.response['Error']['Message']}")
        raise e


def get_user_by_id(user_id) -> UsersResponse:
    """
    Fetch a user by id from the DynamoDB table.
    """
    try:
        response = boto3_client.query(
            TableName="users",
            IndexName="EmailIndex",
            KeyConditionExpression="user_id = :user_id",
            ExpressionAttributeValues={":user_id": {"S": user_id}},
            ProjectionExpression="user_id, email, username, password",
        )

        if response["Items"]:
            user = response["Items"][0]
            return UsersResponse(
                user_id=user["user_id"]["S"],
                email=user["email"]["S"],
                username=user["username"]["S"],
                plan=user["plan"]["S"],
            )
        else:
            logger.error(f"User with ID {user_id} not found")
            raise UserNotFoundException(f"User with ID {user_id} not found")

    except ClientError as e:
        logger.error(f"Error fetching user: {e.response['Error']['Message']}")
        raise e


def update_user_fields(user_id: str, email: str, fields: Dict[str, str]) -> bool:
    """
    Update specified fields for the user in the DynamoDB table.

    :param user_id: User's ID
    :param email: User's email
    :param fields: A dictionary of fields to update, e.g., {"lastlogin": "new_value"}
    :return: True if the update was successful, False otherwise
    """
    update_expr = "SET " + ", ".join(f"#{key} = :{key}" for key in fields.keys())
    expr_attr_values = {f":{key}": {"S": value} for key, value in fields.items()}
    expr_attr_names = {f"#{key}": key for key in fields.keys()}

    try:
        boto3_client.update_item(
            TableName="users",
            Key={
                "user_id": {"S": user_id},
                "email": {"S": email},
            },
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_attr_values,
            ExpressionAttributeNames=expr_attr_names,
        )
        logger.info("User updated successfully!")
        return True

    except ClientError as e:
        logger.error(f"Error updating user fields: {e.response['Error']['Message']}")
        raise e


def update_user_plan(
    user_id: str, user_email: str, desired_plan: str
) -> UsersPlanResponse:
    """
    Update the user's plan in the DynamoDB table.
    """

    update_user_fields(user_id, user_email, {"plan": desired_plan})
    return UsersPlanResponse(user_id=user_id, plan=desired_plan)


def update_user_info(payload: UsersRequestPayload, email: str) -> UsersResponse:

    username = payload.username
    password = payload.password

    user_id = get_user_by_email(email).user_id
    if not username and not password:
        raise ValueError("At least one field must be provided to update user info")

    fields = {}
    if username:
        fields["username"] = username
    if password:
        fields["password"] = security.hash_password(password)

    update_user_fields(user_id, email, fields)
    return UsersResponse(user_id=user_id, username=username)
