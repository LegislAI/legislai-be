#!/usr/bin/env python3
import sys
from pathlib import Path

# Add the root project directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import argparse
import json
import os
from datetime import timedelta
from pathlib import Path

import boto3
from authentication.services.dynamo_services import create_user
from authentication.services.dynamo_services import get_user_by_email
from authentication.utils.auth import create_access_token
from authentication.utils.logging_config import logger
from authentication.utils.schemas import RegisterRequest
from conversation.services.dynamo_services import add_messages_to_new_conversation
from conversation.utils.schemas import Message
from conversation.utils.schemas import NewConversationRequest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION_NAME = os.getenv("AWS_REGION")

DEFAULT_USER_EMAIL = "paulorocha.01@gmail.com"
DEFAULT_USER_NAME = "Paulo Rocha"
DEFAULT_USER_PASSWORD = "Arnold123"

client = boto3.client(
    "dynamodb",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME,
)


def delete_user(user_id: str, email: str):
    try:
        client.delete_item(
            TableName="users",
            Key={
                "user_id": {"S": user_id},
                "email": {"S": email},
            },
        )
        logger.info("User deleted successfully!")
    except boto3.exceptions.ClientError as e:
        logger.error(f"Error deleting user: {e.response['Error']['Message']}")
        raise e


def register_user(email, username, password):
    user = get_user_by_email(email)
    if user:
        logger.info("User already exists, deleting user")
        delete_user(user["user_id"], email)
    logger.info("Registering new user.")
    register_user_request = RegisterRequest(
        email=email, username=username, password=password
    )
    return create_user(register_user_request)


def generate_token(user_id):
    return create_access_token(user_id, timedelta(days=360))


def mock_conversation(user_id, mock_file="./mock_conversations.json"):
    mock_path = Path(mock_file)
    if not mock_path.exists():
        logger.error(f"Mock conversation file not found: {mock_file}")
        return

    with open(mock_path, "r") as file:
        conversation_json = json.load(file)
        for message_mock in conversation_json:
            conversation_request = NewConversationRequest(
                user_id=user_id,
                conversation_id=message_mock["conversation_id"],
                conversation_name=message_mock["conversation_name"],
                conversation_field=message_mock["conversation_field"],
                messages=[
                    Message(
                        message_index=template_message["message_index"],
                        sender=template_message["sender"],
                        timestamp=template_message["timestamp"],
                        message=template_message["message"],
                        attachments=[],
                    )
                    for template_message in message_mock["messages"]
                ],
            )
            logger.info(
                f"Adding messages to conversation {message_mock['conversation_name']}"
            )
            add_messages_to_new_conversation(
                user_id=user_id, payload=conversation_request
            )


def main():
    parser = argparse.ArgumentParser(
        description="Run user and conversation operations."
    )
    parser.add_argument(
        "--email",
        type=str,
        default=DEFAULT_USER_EMAIL,
        help="User email (default: paulo@example.com).",
    )
    parser.add_argument(
        "--username",
        type=str,
        default=DEFAULT_USER_NAME,
        help="User name (default: Paulo Rocha).",
    )
    parser.add_argument(
        "--password",
        type=str,
        default=DEFAULT_USER_PASSWORD,
        help="User password (default: Arnold123).",
    )
    parser.add_argument(
        "--mock-file",
        type=str,
        default="./mock_conversations.json",
        help="Path to mock conversation JSON file (default: ./mock_conversations.json).",
    )

    args = parser.parse_args()

    user = register_user(args.email, args.username, args.password)
    token = generate_token(user["user_id"])
    logger.info(f"User registered successfully. Access token: {token}")
    mock_conversation(user["user_id"], args.mock_file)


if __name__ == "__main__":
    main()
