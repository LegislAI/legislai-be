import uuid
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from authentication.services.dynamo_services import boto3_client
from authentication.services.dynamo_services import create_user
from authentication.services.dynamo_services import get_user
from authentication.services.dynamo_services import update_user_fields
from authentication.utils.auth import create_access_token
from authentication.utils.auth import create_refresh_token
from authentication.utils.logging_config import logger
from authentication.utils.schemas import CreateUser
from authentication.utils.schemas import GetUser
from authentication.utils.schemas import LoginUser
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import status


route = APIRouter()


@route.post("/register", response_model=GetUser)
def register_user(payload: CreateUser):
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

    if create_user(boto3_client, payload):
        return {
            "userid": str(uuid.uuid4()),
            "email": email,
            "username": username,
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed",
        )


@route.post("/login", response_model=GetUser)
def login_user(payload: LoginUser):
    """
    Login user based on email and password
    """
    if not payload.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please provide email",
        )

    user = get_user(boto3_client, payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not payload.password or user["password"] != payload.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
        )

    token = create_access_token(user["userid"], timedelta(minutes=30))
    refresh = create_refresh_token(user["userid"], timedelta(minutes=1008))

    logger.info(f"User logged in: {user['email']}")
    # Update the last login time using both userid and email
    fields_to_update = {"lastlogin": str(datetime.now(timezone.utc))}
    update_user_fields(boto3_client, user["userid"], user["email"], fields_to_update)

    return {
        "access_token": token,
        "token_type": "bearer",
        "refresh_token": refresh,
        "userid": user["userid"],
        "email": user["email"],
        "username": user["username"],
    }
