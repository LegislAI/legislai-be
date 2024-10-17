from datetime import timedelta
from fastapi import FastAPI, APIRouter, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from Authorization.utils.schemas import GetUser, LoginUser, CreateUser
from Authorization.utils.auth import create_access_token, create_refresh_token
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.base_client import OAuthError
from dotenv import load_dotenv
from starlette.middleware.sessions import (
    SessionMiddleware,
)  # Use Starlette's session middleware
import os
import json
from pathlib import Path
from contextlib import asynccontextmanager
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict
from starlette.config import Config

import logging
import uuid
import time
import datetime
from datetime import timezone

"""
na pasta inf/terraform
terraform init
terraform plan
terraform apply
uvicorn Authorization.api:app --reload
"""

load_dotenv()
# When using windows specify the all path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
LOG = logging.getLogger(__name__)

route = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2bearer = OAuth2PasswordBearer(tokenUrl="auth/login")


@asynccontextmanager
async def lifespan(app: FastAPI):
    openapi_spec = app.openapi()
    output_path = Path(__file__).resolve().parent / "openapi.json"
    with open(output_path, "w") as f:
        json.dump(openapi_spec, f, indent=2)
    LOG.info(f"OpenAPI spec saved to {output_path}")

    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    SessionMiddleware, secret_key=os.environ.get("secret_key_middleware")
)  # session_cookie="legislai_cookie", same_site="Lax", https_only=False)

client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
config_data = {"GOOGLE_CLIENT_ID": client_id, "GOOGLE_CLIENT_SECRET": client_secret}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)


GOOGLE_REDIRECT_URI = "https://localhost/auth/google/callback"

# Register the Google OAuth provider
oauth.register(
    name="google",
    access_token_url="https://accounts.google.com/o/oauth2/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    redirect_uri=GOOGLE_REDIRECT_URI,
    client_kwargs={"scope": "openid email profile"},
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
)


boto3_client = boto3.client(
    "dynamodb",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name=os.environ.get("AWS_REGION"),
)


async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


def _get_user(boto3_client, email: Optional[str] = None) -> Optional[dict]:
    """
    Fetch a user by email from the DynamoDB table.
    """
    try:
        response = boto3_client.query(
            TableName="users",
            IndexName="EmailIndex",
            KeyConditionExpression="email = :email",
            ExpressionAttributeValues={":email": {"S": email}},
            ProjectionExpression="userid, email, username, password",
        )

        if response["Items"]:
            user = response["Items"][0]
            return {
                "userid": user["userid"]["S"],
                "email": user["email"]["S"],
                "username": user["username"]["S"],
                "password": user["password"]["S"],
            }

    except ClientError as e:
        LOG.error(f"Error fetching user: {e.response['Error']['Message']}")

    return None


def _create_user(db, user_data: CreateUser) -> bool:
    """
    Create a new user in the DynamoDB table.
    """
    try:
        db.put_item(
            TableName="users",
            Item={
                "userid": {"S": str(uuid.uuid4())},
                "username": {"S": user_data.username},
                "email": {"S": user_data.email},
                "password": {"S": user_data.password},
                "usercreated": {"S": str(datetime.datetime.now(timezone.utc))},
                "lastlogin": {"S": str(datetime.datetime.now(timezone.utc))},
            },
        )
        return True

    except ClientError as e:
        LOG.error(f"Error creating user: {e.response['Error']['Message']}")
        return False


def _update_user_fields(db, userid: str, email: str, fields: Dict[str, str]) -> bool:
    """
    Update specified fields for the user in the DynamoDB table.

    :param db: DynamoDB client
    :param userid: User's unique ID (partition key)
    :param email: User's email (sort key)
    :param fields: A dictionary of fields to update, e.g., {"lastlogin": "new_value"}
    :return: True if the update was successful, False otherwise
    """
    update_expression = "SET " + ", ".join(f"{k} =: {k}" for k in fields.keys())
    expression_attribute_values = {f": {k}": {"S": v} for k, v in fields.items()}

    try:
        db.update_item(
            TableName="users",
            Key={
                "userid": {"S": userid},  # Partition key
                "email": {"S": email},  # Sort key
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
        )
        return True

    except ClientError as e:
        LOG.error(f"Error updating user fields: {e.response['Error']['Message']}")
        return False


@app.get("/world")
def index():
    return "Hello World"


# Google Login Route
@route.get("/google/login")
# async def google_login(request: Request):
#     state = str(uuid4())
#     request.session['state'] = state
#     response = await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)
#     return response
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    response = await oauth.google.authorize_redirect(request, redirect_uri)

    return response


# async def google_login(request: Request):
#     LOG.info("Initiating Google login with OAuth")

#     # Generate a state and store it in the session for CSRF protection
#     state = secrets.token_urlsafe(16)
#     request.session['state'] = state
#     LOG.info(f"State stored in session: {state}")

#     # Construct the full redirect URL manually to log it
#     redirect_url = (
#         f"https://accounts.google.com/o/oauth2/auth"
#         f"?response_type=code&client_id={os.getenv('GOOGLE_CLIENT_ID')}"
#         f"&redirect_uri={GOOGLE_REDIRECT_URI}"
#         f"&scope=openid%20email%20profile"
#         f"&state={state}"
#     )

#     # Log the URL for debugging
#     LOG.info(f"Redirecting to Google: {redirect_url}")

#     # Perform the actual redirect
#     return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI, state=state)


# Google Callback Route - This route will handle the response from Google
@route.get("/google/callback")
async def google_callback(request: Request):
    LOG.info(f"1. Full request received: {request.url}")
    returned_state = request.query_params.get("state")
    LOG.info(f"2. Returned state from Google callback: {returned_state}")

    # Compare with the original state from the session
    original_state = request.session.get("state")
    LOG.info(f"3. Original state stored in session: {original_state}")

    # if returned_state != original_state:
    #     LOG.error("State mismatch! Possible CSRF attack.")
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid state parameter")

    LOG.info(f"{oauth.google.authorize_access_token(request)}")

    try:
        token = await oauth.google.authorize_access_token(request)
        LOG.info(f"exists token: {token} !!!!!!!!!!")
    except OAuthError as e:
        LOG.error(f"OAuthError occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user_info = await oauth.google.parse_id_token(token, None)

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )

    user = _get_user(boto3_client, email=user_info["email"])  # ver se ja existe

    if not user:
        LOG.info(f"{user_info}")
        _create_user(
            boto3_client,
            CreateUser(
                username=user_info["email"].split("@")[0],
                email=user_info["email"],
                password="password",
            ),
        )

    access_token = create_access_token(user_info["email"], timedelta(minutes=30))
    refresh_token = create_refresh_token(user_info["email"], timedelta(minutes=1008))

    # print(f"Access token created for user {user_info['email']}.")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "email": user_info["email"],
        "name": user_info["email"].split("@")[0],
    }


@route.post("/register", response_model=GetUser)
def register_user(payload: CreateUser):
    if not payload.email:
        LOG.error(f"User with payload: {payload} is missing email")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="email field is required",
        )

    if not payload.username:
        LOG.error(f"User with payload: {payload} is missing username")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="username field is required",
        )

    user_by_email = _get_user(boto3_client=boto3_client, email=payload.email)
    if user_by_email:
        LOG.error(f"User with email {payload.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User with email {payload.email} already exists",
        )

    user_created = _create_user(boto3_client, payload)
    if user_created:
        LOG.info(f"User created: {payload.email}")
        return {
            "userid": str(uuid.uuid4()),
            "email": payload.email,
            "username": payload.username,
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

    user = _get_user(boto3_client, payload.email)
    if not user or user["password"] != payload.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
        )

    token = create_access_token(user["userid"], timedelta(minutes=30))
    refresh = create_refresh_token(user["userid"], timedelta(minutes=1008))

    LOG.info(f"User logged in: {user['email']}")

    # Update the last login time using both userid and email
    fields_to_update = {"lastlogin": str(datetime.datetime.now(timezone.utc))}
    _update_user_fields(boto3_client, user["userid"], user["email"], fields_to_update)

    return {
        "access_token": token,
        "token_type": "bearer",
        "refresh_token": refresh,
        "userid": user["userid"],
        "email": user["email"],
        "username": user["username"],
    }


app.include_router(route)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
