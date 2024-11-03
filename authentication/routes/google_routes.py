from datetime import timedelta

from authentication.config.settings import settings
from authentication.services.dynamo_services import boto3_client
from authentication.services.dynamo_services import create_user
from authentication.services.dynamo_services import get_user_by_email
from authentication.utils.auth import create_access_token
from authentication.utils.auth import create_refresh_token
from authentication.utils.exceptions import UserNotFoundException
from authentication.utils.logging_config import logger
from authentication.utils.schemas import LoginResponse
from authentication.utils.schemas import RegisterRequest
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from starlette.config import Config


route = APIRouter()


config_data = {
    "GOOGLE_CLIENT_ID": settings.google_client_id,
    "GOOGLE_CLIENT_SECRET": settings.google_client_secret,
}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)

# Register the Google OAuth provider
oauth.register(
    name="google",
    access_token_url="https://accounts.google.com/o/oauth2/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    redirect_uri=settings.google_redirect_uri,
    client_kwargs={"scope": "openid email profile"},
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
)

# Google Login Route
@route.get("/google/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    response = await oauth.google.authorize_redirect(request, redirect_uri)

    logger.info("Login with google!")
    return response


# Google Callback Route - This route will handle the response from Google
@route.get("/google/callback", response_model=LoginResponse)
async def google_callback(request: Request):
    returned_state = request.query_params.get("state")
    if not returned_state:
        logger.error("Authorization state not found")
    else:
        logger.info(f"Returned state from Google callback: {returned_state}")

    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    # user_info = await oauth.google.parse_id_token(token, None)
    resp = await oauth.google.get(
        "https://openidconnect.googleapis.com/v1/userinfo", token=token
    )

    user_info = resp.json()
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )

    username = user_info.get("username")
    email = user_info.get("email")

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
        user = create_user(
            boto3_client,
            RegisterRequest(
                email=email,
                username=username,
            ),
        )
    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed registration attempt",
        )

    access_token = create_access_token(
        user["email"], timedelta(minutes=settings.access_token_expire_minutes)
    )
    refresh_token = create_refresh_token(
        user["email"], timedelta(minutes=settings.refresh_token_expire_minutes)
    )

    return LoginResponse(
        user_id=user["user_id"],
        email=user["email"],
        username=user["username"],
        access_token=access_token,
        refresh_token=refresh_token,
    )
