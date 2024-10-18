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
import structlog

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
logger = structlog.get_logger()

route = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2bearer = OAuth2PasswordBearer(tokenUrl="auth/login")


@asynccontextmanager
async def lifespan(app: FastAPI):
    openapi_spec = app.openapi()
    output_path = Path(__file__).resolve().parent / "openapi.json"
    with open(output_path, "w") as f:
        json.dump(openapi_spec, f, indent=2)
    logger.info(f"OpenAPI spec saved to {output_path}")


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
        logger.error(f"Error fetching user: {e.response['Error']['Message']}")

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
        logger.info(f"User with email {user_data.email} created!")
        return True

    except ClientError as e:
        logger.error(f"Error creating user: {e.response['Error']['Message']}")
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
        logger.info("User updated!")
        return True

    except ClientError as e:
        logger.error(f"Error updating user fields: {e.response['Error']['Message']}")
        return False


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
    logger.info("Login with google!")
    return response



# Google Callback Route - This route will handle the response from Google
@route.get("/google/callback")
async def google_callback(request: Request):
    logger.info(f"1. Full request received: {request.url}")
    returned_state = request.query_params.get("state")
    if not returned_state:
        logger.error("Authorization state not found")
    else:
        logger.info(f"2. Returned state from Google callback: {returned_state}")

    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    #user_info = await oauth.google.parse_id_token(token, None)
    resp = await oauth.google.get('https://openidconnect.googleapis.com/v1/userinfo', token=token)

    user_info = resp.json()

    name = user_info.get("name") 
    email = user_info.get("email")

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )

    user = _get_user(boto3_client, email=email) 

    if not user:
        _create_user(
            boto3_client,
            CreateUser(
                username=name,
                email=email,
                password="password",
            ),
        )
    else:
        logger.error("User already exists!")

    access_token = create_access_token(user_info["email"], timedelta(minutes=30))
    refresh_token = create_refresh_token(user_info["email"], timedelta(minutes=1008))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "email": user_info["email"],
        "name": name,
        "info": user_info,
    }


@route.post("/register", response_model=GetUser)
def register_user(payload: CreateUser):
    if not payload.email:
        logger.error(f"User with payload: {payload} is missing email")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="email field is required",
        )

    if not payload.username:
        logger.error(f"User with payload: {payload} is missing username")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="username field is required",
        )

    user_by_email = _get_user(boto3_client=boto3_client, email=payload.email)
    if user_by_email:
        logger.error(f"User with email {payload.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User with email {payload.email} already exists",
        )

    user_created = _create_user(boto3_client, payload)
    if user_created:
        logger.info(f"User created: {payload.email}")
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

    logger.info(f"User logged in: {user['email']}")

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
