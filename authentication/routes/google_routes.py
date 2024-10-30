import os
from datetime import timedelta

from authentication.services.dynamo_services import boto3_client
from authentication.services.dynamo_services import create_user
from authentication.services.dynamo_services import get_user
from authentication.utils.auth import create_access_token
from authentication.utils.auth import create_refresh_token
from authentication.utils.logging_config import logger
from authentication.utils.schemas import CreateUser
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from starlette.config import Config


route = APIRouter()


client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
config_data = {"GOOGLE_CLIENT_ID": client_id, "GOOGLE_CLIENT_SECRET": client_secret}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)

GOOGLE_REDIRECT_URI = "http://localhost/auth/google/callback"

# Register the Google OAuth provider
oauth.register(
    name="google",
    access_token_url="https://accounts.google.com/o/oauth2/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    redirect_uri=GOOGLE_REDIRECT_URI,
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
@route.get("/google/callback")
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

    name = user_info.get("name")
    email = user_info.get("email")

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )

    user = get_user(boto3_client, email=email)
    if not user:
        user_id = create_user(
            boto3_client,
            CreateUser(
                username=name,
                email=email,
                password="password",
            ),
        )
    else:
        logger.info("User already exists!")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed",
        )

    access_token = create_access_token(user_id, timedelta(minutes=30))
    refresh_token = create_refresh_token(user_id, timedelta(minutes=1008))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "email": email,
        "name": name,
    }
