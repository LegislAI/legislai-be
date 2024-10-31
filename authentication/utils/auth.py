from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Optional
from typing import Union
from authentication.utils.logging_config import logger
from authentication.config.settings import settings
from authentication.services.dynamo_services import get_user_by_id, boto3_client
from fastapi import HTTPException
from fastapi import Request, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from jose import jwt
from jwt import InvalidTokenError


# generate JWTs (access and refresh tokens) for a user identifier
def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
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
    if expires_delta is not None:
        expires_delta = datetime.now(timezone.utc) + expires_delta
    else:
        expires_delta = datetime.now(timezone.utc) + timedelta(
            minutes=settings.refresh_token_expire_minutes
        )

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.refresh_secret_key, settings.algorithm)
    return encoded_jwt


# This function decodes a JWT to extract the payload.
def decodeJWT(jwtoken: str):
    try:
        logger.info("Attempting to decode JWT")
        payload = jwt.decode(
            jwtoken, settings.secret_key, algorithms=[settings.algorithm]
        )
        logger.info("JWT decoded successfully")
        return payload
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {str(e)}")
        return None


class JWTBearer(HTTPBearer):
    """This class is a custom authentication class that inherits
    from HTTPBearer, a class provided by FastAPI for handling bearer
    token authentication."""

    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                logger.error(f"Invalid auth scheme: {credentials.scheme}")
                raise HTTPException(
                    status_code=403, detail="Invalid authentication scheme."
                )
            token = credentials.credentials
            if not self.verify_jwt(token):
                raise HTTPException(
                    status_code=403, detail="Invalid token or expired token."
                )
            return token
        else:
            logger.error(f"no credentials")
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        try:
            decodeJWT(jwtoken)
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.JWTError:
            return False
