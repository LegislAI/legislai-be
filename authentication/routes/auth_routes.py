from datetime import datetime
from datetime import timedelta
from datetime import timezone

from config.settings import settings
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from services.dynamo_services import create_user
from services.dynamo_services import get_refresh_token
from services.dynamo_services import get_user_by_email
from services.dynamo_services import revoke_token
from services.dynamo_services import update_user_fields
from services.stripe_services import StripeServices
from utils.auth import create_access_token
from utils.auth import create_refresh_token
from utils.auth import decodeJWT
from utils.auth import JWTBearer
from utils.exceptions import UserNotFoundException
from utils.logging_config import logger
from utils.password import SecurityUtils
from utils.schemas import LoginRequest
from utils.schemas import LoginResponse
from utils.schemas import LogoutResponse
from utils.schemas import RefreshTokenRequest
from utils.schemas import RefreshTokenResponse
from utils.schemas import RegisterRequest
from utils.schemas import RegisterResponse


route = APIRouter()
security = SecurityUtils()
stripe_services = StripeServices()


@route.post("/register", response_model=RegisterResponse)
def register_user(payload: RegisterRequest):
    email, username = payload.email, payload.username

    if not email:
        logger.error("email field is required")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="email field is required",
        )
    if not username:
        logger.error("username field is required")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="username field is required",
        )

    user = None

    try:
        user = get_user_by_email(email=email)
    except UserNotFoundException:
        pass
    except Exception as e:
        logger.error(f"Failed to fetch user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed registration attempt",
        )

    if user:
        logger.error(f"User with email {email} already exists")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User with email {email} already exists",
        )

    try:
        user = create_user(payload)
        stripe_user = stripe_services.create_customer(email, user["user_id"], username)
        if user and stripe_user:
            # create a subscription to the free plan
            stripe_services.create_subscription(stripe_user.id, "free", None)
            logger.info(f"User {email} created successfully")
            return RegisterResponse(message=f"User {email} created successfully")
    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed registration attempt",
        )


@route.post("/login", response_model=LoginResponse)
def login_user(payload: LoginRequest):
    """
    Login user based on email and password
    """
    email, password = payload.email, payload.password

    if not email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please provide email",
        )
    if not password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please provide password",
        )

    try:
        user = get_user_by_email(payload.email)
    except UserNotFoundException as e:
        logger.error(f"User not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    except Exception as e:
        logger.error(f"Failed to fetch user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed login attempt",
        )

    if not security.verify_password(user["password"], payload.password):
        logger.warning(f"Failed login attempt for email: {payload.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )

    access_token = create_access_token(
        user["user_id"], timedelta(minutes=settings.access_token_expire_minutes)
    )
    refresh_token = create_refresh_token(
        user["user_id"], timedelta(minutes=settings.refresh_token_expire_minutes)
    )

    fields_to_update = {
        "last_login": str(datetime.now(timezone.utc)),
        "refresh_token": refresh_token,
    }

    try:
        update_user_fields(user["user_id"], user["email"], fields_to_update)
    except Exception as e:
        logger.error(f"Failed to update user fields: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed login attempt",
        )

    logger.info(f"User logged in: {user['email']}")
    return LoginResponse(
        user_id=user["user_id"],
        access_token=access_token,
        refresh_token=refresh_token,
    )


@route.post("/logout", response_model=LogoutResponse)
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(JWTBearer()),
):
    """
    Logout user based on email and revoke tokens
    """
    access_token = credentials.credentials

    try:
        user_id = decodeJWT(access_token)["sub"]
    except Exception as e:
        logger.error(f"Failed to fetch user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout",
        )

    try:
        refresh_token = get_refresh_token(user_id)
        revoke_token(user_id, refresh_token, "refresh_token")
        revoke_token(user_id, access_token, "access_token")
    except Exception as e:
        logger.error(f"Failed to logout user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout user",
        )

    logger.info(f"User with id {user_id} logged out successfully")
    return LogoutResponse(message="Successfully logged out")


@route.post("/refresh-tokens", response_model=RefreshTokenResponse)
async def refresh_tokens(
    payload: RefreshTokenRequest,
    credentials: HTTPAuthorizationCredentials = Depends(JWTBearer()),
):
    """
    Refresh access and refresh tokens
    """
    email, access_token = payload.email, payload.access_token

    try:
        user = get_user_by_email(email)
    except UserNotFoundException as e:
        logger.error(f"User not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    except Exception as e:
        logger.error(f"Failed to fetch user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed login attempt",
        )

    refresh_token = credentials.credentials

    try:
        revoke_token(user["user_id"], refresh_token, "refresh_token")
        revoke_token(user["user_id"], access_token, "access_token")
    except Exception as e:
        logger.error(f"Failed to refresh token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh tokens",
        )

    new_access_token = create_access_token(
        user["user_id"], timedelta(minutes=settings.access_token_expire_minutes)
    )
    new_refresh_token = create_refresh_token(
        user["user_id"], timedelta(minutes=settings.refresh_token_expire_minutes)
    )

    try:
        update_user_fields(
            user["user_id"], user["email"], {"refresh_token": new_refresh_token}
        )
    except Exception as e:
        logger.error(f"Failed to update user fields: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh tokens",
        )

    return RefreshTokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )
