import datetime
from datetime import timezone
from typing import Dict

import boto3
from botocore.exceptions import ClientError
from config.settings import settings
from utils.exceptions import UserNotFoundException
from utils.logging_config import logger
from utils.password import SecurityUtils
from utils.schemas import UsersPlanResponse
from utils.schemas import UsersRequestPayload
from utils.schemas import UsersResponse

security = SecurityUtils()
boto3_client = boto3.client(
    "dynamodb",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region,
)


def get_user_by_email(email: str) -> UsersResponse:
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
            KeyConditionExpression="user_id = :user_id",
            ExpressionAttributeValues={":user_id": {"S": user_id}},
            ProjectionExpression="user_id, email, username, password, plan_name, weekly_queries",
        )

        if response["Items"]:
            user = response["Items"][0]
            return UsersResponse(
                user_id=user["user_id"]["S"],
                email=user["email"]["S"],
                username=user["username"]["S"],
                plan=user["plan_name"]["S"],
                weekly_queries=user["weekly_queries"]["S"],
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

    update_user_fields(user_id, user_email, {"plan_name": desired_plan})
    return UsersPlanResponse(user_id=user_id, plan=desired_plan)


def update_user_info(payload: UsersRequestPayload, user_id: str) -> UsersResponse:

    username = payload.username
    password = payload.password

    if not username and not password:
        raise ValueError("At least one field must be provided to update user info")

    fields = {}
    if username:
        fields["username"] = username
    if password:
        fields["password"] = security.hash_password(password)

    email = get_user_by_id(user_id).email

    update_user_fields(user_id, email, fields)
    return UsersResponse(user_id=user_id, username=username)


def revoke_token(user_id: str, token: str, type: str):
    try:
        token_blacklist.add_to_blacklist(user_id, token, type)
        logger.info(f"{type} revoked for {user_id}")

    except Exception as e:
        logger.error(f"Failed to revoke tokens: {str(e)}")
        raise e


def get_refresh_token(user_id: str) -> str:
    """
    Fetch the refresh token for the user
    """
    try:
        response = boto3_client.query(
            TableName="users",
            KeyConditionExpression="user_id = :user_id",
            ExpressionAttributeValues={":user_id": {"S": user_id}},
            ProjectionExpression="refresh_token",
        )

        if response["Items"]:
            return response["Items"][0]["refresh_token"]["S"]
        else:
            raise UserNotFoundException(f"Refresh token not found for user: {user_id}")

    except UserNotFoundException as e:
        logger.error(f"Error fetching refresh token: {str(e)}")
        raise e

    except ClientError as e:
        logger.error(f"Error fetching refresh token: {str(e)}")
        raise e


class TokenBlacklist:
    """
    Handles token blacklisting operations in DynamoDB
    """

    def __init__(self, dynamodb_client):
        self.client = dynamodb_client
        self.table_name = "token_blacklist"

    def add_to_blacklist(self, user_id: str, auth_token: str, type: str):
        """
        Add a token to the blacklist
        """
        try:
            self.client.put_item(
                TableName=self.table_name,
                Item={
                    "user_id": {"S": user_id},
                    "auth_token": {"S": auth_token},
                    "type": {"S": type},
                    "blacklisted_at": {"S": str(datetime.now(timezone.utc))},
                },
            )

        except Exception as e:
            logger.error(f"Failed to blacklist auth_token: {str(e)}")
            raise e

    def get_blacklisted_tokens(self, user_id: str):
        """
        Fetch all blacklisted tokens for a user
        """
        try:
            response = self.client.query(
                TableName=self.table_name,
                KeyConditionExpression="user_id = :user_id",
                ExpressionAttributeValues={":user_id": {"S": user_id}},
            )

            tokens = [item["auth_token"]["S"] for item in response.get("Items", [])]
            return tokens

        except Exception as e:
            logger.error(f"Failed to fetch blacklisted tokens: {str(e)}")
            raise e

    def is_blacklisted(self, user_id: str, auth_token: str) -> bool:
        """
        Check if a token has been in the blacklist
        """
        try:
            response = self.client.query(
                TableName=self.table_name,
                KeyConditionExpression="user_id = :user_id AND auth_token = :auth_token",
                ExpressionAttributeValues={
                    ":user_id": {"S": user_id},
                    ":auth_token": {"S": auth_token},
                },
            )

            return len(response.get("Items", [])) > 0

        except Exception as e:
            logger.error(f"Failed to check token blacklist: {str(e)}")
            raise e

    def add_user_active_refresh_token_to_blacklist(self, user_id: str):
        """
        Add active refresh token to the blacklist
        """
        try:
            refresh_token = get_refresh_token(user_id)
            self.add_to_blacklist(user_id, refresh_token, "refresh")

        except Exception as e:
            logger.error(f"Failed to blacklist active refresh_token: {str(e)}")
            raise e


token_blacklist = TokenBlacklist(boto3_client)


def revoke_token(user_id: str, token: str, type: str):
    """
    Revoke user's access or refresh tokens
    """
    try:
        token_blacklist.add_to_blacklist(user_id, token, type)
        logger.info(f"{type} revoked for {user_id}")

    except Exception as e:
        logger.error(f"Failed to revoke tokens: {str(e)}")
        raise e


def get_refresh_token(user_id: str) -> str:
    """
    Fetch the refresh token for the user
    """
    try:
        response = boto3_client.query(
            TableName="users",
            KeyConditionExpression="user_id = :user_id",
            ExpressionAttributeValues={":user_id": {"S": user_id}},
            ProjectionExpression="refresh_token",
        )

        if response["Items"]:
            return response["Items"][0]["refresh_token"]["S"]
        else:
            raise UserNotFoundException(f"Refresh token not found for user: {user_id}")

    except UserNotFoundException as e:
        logger.error(f"Error fetching refresh token: {str(e)}")
        raise e

    except ClientError as e:
        logger.error(f"Error fetching refresh token: {str(e)}")
        raise e
