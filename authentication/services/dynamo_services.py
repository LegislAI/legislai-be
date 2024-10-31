import uuid
from datetime import datetime
from datetime import timezone, timedelta
from typing import Dict
from fastapi import HTTPException,status
import boto3
from authentication.config.settings import settings
from authentication.utils.logging_config import logger
from authentication.utils.schemas import RegisterUserRequest
from botocore.exceptions import ClientError
from authentication.utils.password import SecurityUtils
import secrets
import jwt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import smtplib
security = SecurityUtils()
boto3_client = boto3.client(
    "dynamodb",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region,
)



def get_user(boto3_client, email: str) -> Dict:
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
        return {}


def get_user_by_id(boto3_client, userid) -> Dict:
    """
    Fetch a user by id from the DynamoDB table.
    """
    try:
        response = boto3_client.query(
            TableName="users",
            IndexName="EmailIndex",
            KeyConditionExpression="userid = :userid",
            ExpressionAttributeValues={":userid": {"S": userid}},
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
        return {}


def create_user(db, user_data: RegisterUserRequest) -> Dict:
    """
    Create a new user in the DynamoDB table.
    """
    email, username = user_data.email, user_data.username
    user_id = str(uuid.uuid4())
    hashed_password = security.hash_password(user_data.password)
    try:
        db.put_item(
            TableName="users",
            Item={
                "userid": {"S": user_id},
                "email": {"S": email},
                "username": {"S": username},
                "password": {"S": hashed_password},
                "usercreated": {"S": str(datetime.now(timezone.utc))},
                "lastlogin": {"S": str(datetime.now(timezone.utc))},
            },
        )
        logger.info(f"User with email {email} created!")
        return {
            "userid": user_id,
            "email": email,
            "username": username,
            "password": hashed_password,
        }

    except ClientError as e:
        logger.error(f"Error creating user: {e.response['Error']['Message']}")
        return {}


def update_user_fields(db, userid: str, email: str, fields: Dict[str, str]) -> bool:
    """
    Update specified fields for the user in the DynamoDB table.

    :param db: DynamoDB client
    :param userid: User's unique ID (partition key)
    :param email: User's email (sort key)
    :param fields: A dictionary of fields to update, e.g., {"lastlogin": "new_value"}
    :return: True if the update was successful, False otherwise
    """
    update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in fields.keys())
    expression_attribute_values = {f":{k}": {"S": v} for k, v in fields.items()}

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


class TokenBlacklist:
    """Handles token blacklisting operations in DynamoDB"""
    
    def __init__(self, dynamodb_client):
        self.client = dynamodb_client
        self.table_name = "token_blacklist"

    def add_to_blacklist(self, token: str, expires_at: int) -> bool:
        try:
            self.client.put_item(
                TableName=self.table_name,
                Item={
                    "token": {"S": token},
                    "expires_at": {"N": str(expires_at)},
                    "blacklisted_at": {"S": str(datetime.now(timezone.utc))}
                }
            )
            return True
        except Exception as e:
            logger.error(f"Failed to blacklist token: {str(e)}")
            return False

    def is_blacklisted(self, token: str) -> bool:
        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key={"token": {"S": token}}
            )
            return "Item" in response
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {str(e)}")
            return False



token_blacklist = TokenBlacklist(boto3_client)
def is_token_blacklisted(self, token: str) -> bool:
    return token_blacklist.is_blacklisted(token)



# reset password
def send_reset_email(email: str, reset_token: str):
    """Send password reset email using AWS SES"""
    try:
        ses_client = boto3.client(
            'ses',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )

       
        reset_link = f"{settings.frontend_url}/reset-password?token={reset_token}"

        # Create the email message
        message = MIMEMultipart()
        message["Subject"] = "Password Reset Request"
        message["From"] = settings.ses_sender_email
        message["To"] = email

        html_content = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>You have requested to reset your password. Click the link below to reset it:</p>
                <p><a href="{reset_link}">Reset Password</a></p>
                <p>If you didn't request this, please ignore this email.</p>
                <p>This link will expire in 30 minutes.</p>
            </body>
        </html>
        """

        # Attach HTML content
        part = MIMEText(html_content, "html")
        message.attach(part)

        # Send email
        # ses_client.send_raw_email(
        #     Source=settings.ses_sender_email,
        #     Destinations=[email],
        #     RawMessage={"Data": message.as_string()}
        # )
        s = smtplib.SMTP('localhost',8000)
        s.sendmail(email,'localhost',message ), 
        s.quit()


        logger.info(f"Password reset email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send reset email: {str(e)}")
        return False

def create_password_reset_token(user_id: str) -> str:
    """Create a secure reset token"""
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        "jti": secrets.token_hex(32)  # Unique token ID
    }
    token = jwt.encode(
        payload,
        settings.reset_token_secret,
        algorithm=settings.algorithm
    )
    return token

def verify_reset_token(token: str) -> Optional[str]:
    """Verify the reset token and return the user_id if valid"""
    try:
        payload = jwt.decode(
            token,
            settings.reset_token_secret,
            algorithms=[settings.algorithm]
        )
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
