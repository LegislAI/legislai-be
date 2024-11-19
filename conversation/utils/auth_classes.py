from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Optional
from typing import Union

import boto3
from authentication.config.settings import settings
from authentication.services.dynamo_services import token_blacklist
from authentication.utils.exceptions import TokenRevokedException
from authentication.utils.logging_config import logger
from botocore.exceptions import ClientError
from conversation.config.settings import settings
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from jose import jwt
from jwt.exceptions import ExpiredSignatureError
from jwt.exceptions import InvalidTokenError


boto3_client = boto3.client(
    "dynamodb",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region,
)


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
            user = response["Items"][0]
            return user["refresh_token"]["S"]

    except ClientError as e:
        logger.error(f"Error fetching refresh token: {e.response['Error']['Message']}")
        raise e


def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    """
    Create an access token for a user identifier.
    """
    if expires_delta is not None:
        expires_delta = datetime.now(timezone.utc) + expires_delta

    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, settings.algorithm)

    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    """
    Create a refresh token for a user identifier.
    """
    if expires_delta is not None:
        expires_delta = datetime.now(timezone.utc) + expires_delta

    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(
            minutes=settings.refresh_token_expire_minutes
        )

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.refresh_secret_key, settings.algorithm)

    return encoded_jwt


def decodeJWT(jwtoken: str):
    """
    Decode a JWT token and return the payload and verify if the token is valid.
    """
    try:
        logger.info("Attempting to decode JWT")
        payload = jwt.decode(
            jwtoken, settings.secret_key, algorithms=[settings.algorithm]
        )
        logger.info("JWT decoded successfully")
        return payload

    except ExpiredSignatureError:
        logger.error("Expired token")
        return None

    except InvalidTokenError:
        logger.error("Invalid token")
        return None

    except Exception as e:
        logger.error(f"Unexpected error decoding token: {str(e)}")
        return None


class JWTBearer(HTTPBearer):
    """
    This class is a custom authentication class that inherits from HTTPBearer, a class provided by FastAPI for handling bearer token authentication.
    """

    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)

        if not credentials:
            logger.error("No credentials provided")
            raise HTTPException(
                status_code=403, detail="Invalid authentication credentials."
            )

        if credentials.scheme != "Bearer":
            logger.error(f"Invalid auth scheme: {credentials.scheme}")
            raise HTTPException(
                status_code=403, detail="Invalid authentication scheme."
            )

        token = credentials.credentials
        payload = decodeJWT(token)

        if not payload:
            logger.error("Invalid or expired token")
            raise HTTPException(status_code=403, detail="Invalid or expired token.")

        user_id = payload["sub"]

        try:
            if token_blacklist.is_blacklisted(user_id, token):
                token_blacklist.add_user_active_refresh_token_to_blacklist(user_id)
                raise TokenRevokedException("Token has been revoked")
        except TokenRevokedException as e:
            logger.error(f"Token has been revoked: {str(e)}")
            raise HTTPException(status_code=403, detail="Token has been revoked.")
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error.")

        return credentials


def is_authenticated(token: str) -> bool:
    """
    Check if the token is valid and not expired.
    """
    try:
        payload = decodeJWT(token)
        if not payload:
            return False
        return True
    except Exception:
        return False


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(JWTBearer())):
    token = credentials.credentials
    if not is_authenticated(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )
