from datetime import datetime
from datetime import timedelta
from datetime import timezone

from authentication.config.settings import settings
from authentication.services.dynamo_services import boto3_client
from authentication.services.dynamo_services import create_user
from authentication.services.dynamo_services import get_user
from authentication.services.dynamo_services import update_user_fields
from authentication.utils.auth import create_access_token
from authentication.utils.auth import create_refresh_token
from authentication.utils.logging_config import logger
from authentication.utils.schemas import LoginUserRequest
from authentication.utils.schemas import LoginUserResponse
from authentication.utils.schemas import RegisterUserRequest
from authentication.utils.schemas import RegisterUserResponse
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status


route = APIRouter()


@route.post("/register", response_model=RegisterUserResponse)
def register_user(payload: RegisterUserRequest):
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

    if get_user(boto3_client=boto3_client, email=email):
        logger.error(f"User with email {email} already exists")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User with email {email} already exists",
        )

    user = create_user(boto3_client, payload)
    if user:
        return RegisterUserResponse(
            userid=user["userid"],
            email=email,
            username=username,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed",
        )


@route.post("/login", response_model=LoginUserResponse)
def login_user(payload: LoginUserRequest):
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

    user = get_user(boto3_client, payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if payload.password != user["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
        )

    access_token = create_access_token(
        user["userid"], timedelta(minutes=settings.access_token_expire_minutes)
    )
    refresh_token = create_refresh_token(
        user["userid"], timedelta(minutes=settings.refresh_token_expire_minutes)
    )

    # Update the last login time
    fields_to_update = {"lastlogin": str(datetime.now(timezone.utc))}
    update_user_fields(boto3_client, user["userid"], user["email"], fields_to_update)

    logger.info(f"User logged in: {user['email']}")

    return LoginUserResponse(
        userid=user["userid"],
        email=user["email"],
        username=user["username"],
        access_token=access_token,
        refresh_token=refresh_token,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_minutes=settings.refresh_token_expire_minutes,
    )
