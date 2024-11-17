from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Optional
from typing import Union

from config.settings import settings
from fastapi import HTTPException
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from jose import jwt
from jwt.exceptions import ExpiredSignatureError
from jwt.exceptions import InvalidTokenError
from services.dynamo_services import token_blacklist
from utils.exceptions import TokenRevokedException
from utils.logging_config import logger


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
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, settings.algorithm)

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

        print(
            "token time left:", payload["exp"] - datetime.now(timezone.utc).timestamp()
        )
        email = payload["sub"]

        try:
            if token_blacklist.is_blacklisted(email, token):
                token_blacklist.add_user_active_refresh_token_to_blacklist(email)
                raise TokenRevokedException("Token has been revoked")
        except TokenRevokedException as e:
            logger.error(f"Token has been revoked: {str(e)}")
            raise HTTPException(status_code=403, detail="Token has been revoked.")
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error.")

        return credentials
