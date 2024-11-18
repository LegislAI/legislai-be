from typing import Any
from typing import Optional
from services.dynamo_services import token_blacklist
from utils.exceptions import TokenRevokedException
from fastapi import HTTPException
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from jose import jwt
from jwt.exceptions import ExpiredSignatureError
from jwt.exceptions import InvalidTokenError
from config.settings import settings
from utils.logging_config import logger


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
