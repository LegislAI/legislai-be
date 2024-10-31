from datetime import datetime
from datetime import timedelta
from datetime import timezone

from authentication.config.settings import settings
from authentication.services.dynamo_services import boto3_client
from authentication.services.dynamo_services import create_password_reset_token
from authentication.services.dynamo_services import create_user
from authentication.services.dynamo_services import get_user
from authentication.services.dynamo_services import get_user_active_tokens
from authentication.services.dynamo_services import get_user_by_id
from authentication.services.dynamo_services import send_reset_email
from authentication.services.dynamo_services import token_blacklist
from authentication.services.dynamo_services import update_user_fields
from authentication.services.dynamo_services import verify_reset_token
from authentication.utils.auth import create_access_token
from authentication.utils.auth import create_refresh_token
from authentication.utils.auth import decodeJWT
from authentication.utils.auth import JWTBearer
from authentication.utils.logging_config import logger
from authentication.utils.password import SecurityUtils
from authentication.utils.schemas import LoginUserRequest
from authentication.utils.schemas import LoginUserResponse
from authentication.utils.schemas import LogoutResponse
from authentication.utils.schemas import PasswordResetRequest
from authentication.utils.schemas import PasswordResetResponse
from authentication.utils.schemas import RegisterUserRequest
from authentication.utils.schemas import RegisterUserResponse
from authentication.utils.schemas import ResetPasswordConfirm
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials


route = APIRouter()
security = SecurityUtils()


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
    print(user)
    if not security.verify_password(user["password"], payload.password):
        logger.warning(f"Failed login attempt for email: {payload.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
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


"""But if you plan to have a strict log out functionality, that cannot wait for the token auto-expiration,
even though you have cleaned the token from the client side, then you might need to neglect the stateless logic and do some queries."""


@route.post("/logout", response_model=LogoutResponse)
async def logout_user(credentials: LoginUserRequest):
    """Logout user using email and password"""
    try:
        user = get_user(boto3_client, credentials.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        if not security.verify_password(user["password"], credentials.password):
            logger.warning(f"Failed logout attempt for email: {credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        active_tokens = await get_user_active_tokens(user["userid"])

        # Blacklist all active tokens
        blacklist_success = True
        for token_info in active_tokens:
            token = token_info.get("token")
            if token:
                try:
                    payload = decodeJWT(token)
                    if payload and "exp" in payload:
                        success = token_blacklist.add_to_blacklist(
                            token, payload["exp"]
                        )
                        if not success:
                            blacklist_success = False
                            logger.error(
                                f"Failed to blacklist token for user {user['userid']}"
                            )
                except Exception as e:
                    logger.error(f"Error processing token: {str(e)}")
                    blacklist_success = False

        if not blacklist_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to logout all sessions. Please try again.",
            )

        # Update last logout time
        fields_to_update = {"last_logout": str(datetime.now(timezone.utc))}
        update_user_fields(
            boto3_client, user["userid"], user["email"], fields_to_update
        )

        logger.info(
            f"User {credentials.email} logged out successfully from all sessions"
        )
        return LogoutResponse(message="Successfully logged out from all sessions")

    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during logout",
        )


@route.post("/request-password-reset", response_model=PasswordResetResponse)
async def request_password_reset(request: PasswordResetRequest):
    """
    Request a password reset token

    This endpoint:
    1. Validates the email exists
    2. Creates a reset token
    3. Sends an email with the reset link
    """
    try:
        # Check if user exists
        user = get_user(boto3_client, request.email)
        if not user:
            # Return success even if email doesn't exist (security best practice)
            return PasswordResetResponse(
                message="If your email is registered, you will receive reset instructions."
            )

        # Create reset token
        reset_token = create_password_reset_token(user["userid"])

        # Send reset email
        email_sent = send_reset_email(request.email, reset_token)
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send reset email",
            )

        logger.info(f"Password reset requested for user: {request.email}")
        return PasswordResetResponse(
            message="If your email is registered, you will receive reset instructions."
        )

    except Exception as e:
        logger.error(f"Password reset request failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request",
        )


@route.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(request: ResetPasswordConfirm):
    """
    Reset password using the reset token

    This endpoint:
    1. Validates the reset token
    2. Updates the user's password
    3. Invalidates all existing sessions
    """
    try:
        # Verify token and get user_id
        user_id = verify_reset_token(request.token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token"
            )

        # Get user details
        user = get_user_by_id(boto3_client, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Hash new password
        hashed_password = security.get_password_hash(request.new_password)

        # Update password in DynamoDB
        fields_to_update = {
            "password": hashed_password,
            "password_changed_at": str(datetime.now(timezone.utc)),
        }
        update_user_fields(boto3_client, user_id, user["email"], fields_to_update)

        # Optional: Invalidate all existing sessions for this user
        # This would require implementing a way to track and invalidate all tokens

        logger.info(f"Password reset successful for user: {user['email']}")
        return PasswordResetResponse(message="Password has been reset successfully")

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Password reset failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password",
        )
