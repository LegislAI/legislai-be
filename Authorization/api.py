from datetime import timedelta
from fastapi import FastAPI, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from Authorization.utils.schemas import GetUser, LoginUser, CreateUser
from Authorization.utils.auth import create_access_token, create_refresh_token
from dotenv import load_dotenv
import os
import json
from pathlib import Path
from contextlib import asynccontextmanager
import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict

import logging
import uuid
import datetime
from datetime import timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
LOG = logging.getLogger(__name__)

route = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2bearer = OAuth2PasswordBearer(tokenUrl="auth/login")

load_dotenv()
boto3_client = boto3.client(
    "dynamodb",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name=os.environ.get("AWS_REGION"),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    openapi_spec = app.openapi()
    output_path = Path(__file__).resolve().parent / "openapi.json"
    with open(output_path, "w") as f:
        json.dump(openapi_spec, f, indent=2)
    LOG.info(f"OpenAPI spec saved to {output_path}")

    yield


app = FastAPI(lifespan=lifespan)


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
