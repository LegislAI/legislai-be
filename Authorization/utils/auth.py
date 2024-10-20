import datetime
from datetime import timedelta
from datetime import timezone
from typing import Any
from typing import Optional
from typing import Union
from .config import setting
from fastapi import HTTPException
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from jose import jwt
from jwt import InvalidTokenError


# generate JWTs (access and refresh tokens) for a user identifier
def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.datetime.now(timezone.utc) + expires_delta
    else:
        expires_delta = datetime.datetime.now(timezone.utc) + timedelta(
            minutes=setting.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, setting.secret_key, setting.algorithm)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.datetime.now(timezone.utc) + expires_delta
    else:
        expires_delta = datetime.datetime.now(timezone.utc) + timedelta(
            minutes=setting.REFRESH_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, setting.refresh_secret_key, setting.algorithm)
    return encoded_jwt


# This function decodes a JWT to extract the payload.
def decodeJWT(jwtoken: str):
    try:
        payload = jwt.decode(jwtoken, setting.secret_key, setting.algorithm)
        return payload
    except InvalidTokenError:
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
            raise HTTPException(status_code=403, detail="Invalid authorization code.")

    def verify_jwt(self, jwtoken: str) -> bool:
        try:
            decodeJWT(jwtoken)
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.JWTError:
            return False
