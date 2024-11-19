from typing import Any
from typing import Dict

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from conversation.utils.schemas import Attachment
from conversation.utils.schemas import Message


def format_messages(messages):
    formatted_messages = []
    for message in messages:
        formatted_message = {
            "M": {
                "message_index": {"S": message.message_index},
                "sender": {"S": message.sender},
                "timestamp": {"S": message.timestamp},
                "message": {"S": message.message},
                "attachments": {
                    "L": [
                        {
                            "M": {
                                "content": {"S": attachment.content},
                                "designation": {"S": attachment.designation},
                                "url": {"S": attachment.url},
                            }
                        }
                        for attachment in message.attachments
                    ]
                },
            }
        }
        formatted_messages.append(formatted_message)

    return formatted_messages


def parse_dynamodb_message(dynamodb_message: Dict[str, Any]) -> Message:
    """
    Parse a DynamoDB message item to match the `Message` model format.
    """
    attachments = [
        Attachment(
            content=att["M"]["content"]["S"],
            designation=att["M"]["designation"]["S"],
            url=att["M"]["url"]["S"],
        )
        for att in dynamodb_message["M"].get("attachments", {}).get("L", [])
    ]

    return Message(
        message_index=dynamodb_message["M"]["message_index"]["S"],
        sender=dynamodb_message["M"]["sender"]["S"],
        timestamp=dynamodb_message["M"]["timestamp"]["S"],
        message=dynamodb_message["M"]["message"]["S"],
        attachments=attachments,
    )