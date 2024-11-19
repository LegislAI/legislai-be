from typing import Dict
from typing import List

import boto3
from authentication.utils.logging_config import logger
from botocore.exceptions import ClientError
from conversation.config.settings import settings
from conversation.utils.aux_func import format_messages
from conversation.utils.aux_func import parse_dynamodb_message
from conversation.utils.schemas import AddMessageRequest
from conversation.utils.schemas import NewConversationRequest
from fastapi import HTTPException
from fastapi import status


boto3_client = boto3.client(
    "dynamodb",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region,
)


def check_conversation(user_id: str, conversation_id: str) -> bool:
    """
    Check if a conversation exists and if the user is part of it
    """
    response = boto3_client.get_item(
        TableName="conversations",
        Key={"user_id": {"S": user_id}, "conversation_id": {"S": conversation_id}},
    )

    if "Item" not in response:
        logger.error(f"Conversation {conversation_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return True


def add_messages_to_new_conversation(
    conversation_id: str, payload: NewConversationRequest
):
    """
    Add messages to a new conversation
    """
    user_id, conversation_name, conversation_field = (
        payload.user_id,
        payload.conversation_name,
        payload.conversation_field,
    )
    messages = format_messages(payload.messages)

    try:
        boto3_client.put_item(
            TableName="conversations",
            Item={
                "user_id": {"S": user_id},
                "conversation_id": {"S": conversation_id},
                "conversation_name": {"S": conversation_name},
                "conversation_field": {"S": conversation_field},
                "updated_at": {"S": messages[-1]["M"]["timestamp"]["S"]},
                "messages": {"L": messages},
            },
        )
        logger.info("Conversation created successfully")

    except ClientError as e:
        logger.error(f"Error creating conversation: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating conversation",
        )


def add_messages_to_conversation(conversation_id: str, payload: AddMessageRequest):
    """
    Add messages to an existing conversation
    """
    print(payload)
    messages = format_messages(payload.messages)
    print(payload)

    try:
        boto3_client.update_item(
            TableName="conversations",
            Key={
                "conversation_id": {"S": conversation_id},
                "user_id": {"S": payload.user_id},
            },
            UpdateExpression="SET messages = list_append(messages, :messages), updated_at = :updated_at",
            ExpressionAttributeValues={
                ":messages": {"L": messages},
                ":updated_at": {"S": messages[-1]["M"]["timestamp"]["S"]},
            },
        )
        logger.info("Messages added to conversation successfully")

    except ClientError as e:
        logger.error(
            f"Error adding messages to conversation: {e.response['Error']['Message']}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding messages to conversation",
        )


def delete_conversation(conversation_id: str, user_id: str):
    """
    Delete a conversation by its ID
    """
    try:
        boto3_client.delete_item(
            TableName="conversations",
            Key={"user_id": {"S": user_id}, "conversation_id": {"S": conversation_id}},
        )
        logger.info(f"Conversation {conversation_id} deleted successfully")

    except ClientError as e:
        logger.error(f"Error deleting conversation: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting conversation",
        )


def get_conversation(conversation_id: str, user_id: str) -> Dict:
    """
    Get a conversation by its ID
    """
    try:
        response = boto3_client.get_item(
            TableName="conversations",
            Key={"user_id": {"S": user_id}, "conversation_id": {"S": conversation_id}},
        )

        conversation = {
            "conversation_id": response["Item"]["conversation_id"]["S"],
            "conversation_name": response["Item"]
            .get("conversation_name", {})
            .get("S", ""),
            "conversation_field": response["Item"]
            .get("conversation_field", {})
            .get("S", ""),
            "updated_at": response["Item"].get("updated_at", {}).get("S", ""),
            "messages": [
                {
                    "message_index": str(msg["M"]["message_index"]["S"]),
                    "sender": msg["M"]["sender"]["S"],
                    "timestamp": msg["M"]["timestamp"]["S"],
                    "message": msg["M"]["message"]["S"],
                    "attachments": [
                        {
                            "content": att["M"]["content"]["S"],
                            "designation": att["M"]["designation"]["S"],
                            "url": att["M"]["url"]["S"],
                        }
                        for att in msg["M"]["attachments"]["L"]
                    ],
                }
                for msg in response["Item"]["messages"]["L"]
            ],
        }

        logger.info(f"Conversation {conversation_id} retrieved successfully.")
        return conversation

    except ClientError as e:
        logger.error(f"Error retrieving conversation: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving conversation",
        )


def get_recent_conversations(user_id, offset: int = 0, limit: int = 10) -> List[Dict]:
    """
    Get recent conversations with their recent messages
    """
    try:
        response = boto3_client.query(
            TableName="conversations",
            IndexName="UserIdAtIndex",
            KeyConditionExpression="user_id = :user_id",
            ExpressionAttributeValues={":user_id": {"S": user_id}},
            ProjectionExpression="conversation_id, conversation_name,conversation_field, updated_at",
            Limit=offset + limit,
        )

        # Order conversations by `updated_at` in descending order
        conversations = sorted(
            response.get("Items", []), key=lambda x: x["updated_at"]["S"], reverse=True
        )

        # Return only the range between `offset` and `offset + limit`
        paginated_conversations = conversations[offset : offset + limit]

        conversations_with_messages = []
        for conv in paginated_conversations:
            conversation_id = conv["conversation_id"]["S"]

            recent_messages = get_recent_messages(user_id, conversation_id, 16, 0)

            conversation_with_messages = {
                "conversation_id": conversation_id,
                "conversation_name": conv["conversation_name"]["S"],
                "conversation_field": conv["conversation_field"]["S"],
                "updated_at": conv["updated_at"]["S"],
                "messages": recent_messages["messages"],
            }
            conversations_with_messages.append(conversation_with_messages)

        print(conversation_with_messages)

        logger.info(f"Fetched {len(conversations_with_messages)} conversations")
        return conversations_with_messages

    except ClientError as e:
        logger.error(
            f"Error retrieving conversations: {e.response['Error']['Message']}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving conversations",
        )


def delete_all_conversations(user_id: str):
    """
    Delete all conversations for a user
    """
    try:
        response = boto3_client.scan(
            TableName="conversations",
            FilterExpression="user_id = :user_id",
            ExpressionAttributeValues={":user_id": {"S": user_id}},
        )

        conversations = response.get("Items", [])
        if not conversations:
            logger.info(f"No conversations found for user {user_id}")
            return

        for conv in conversations:
            conversation_id = conv["conversation_id"]["S"]
            delete_conversation(conversation_id, user_id)

        logger.info(f"All conversations for user {user_id} deleted successfully")

    except ClientError as e:
        logger.error(f"Error deleting conversations: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting conversations",
        )


def get_recent_messages(
    user_id: str, conversation_id: str, limit: int, last_evaluated_key: int = None
) -> Dict:
    """
    Get recent messages for a conversation
    """
    try:
        response = boto3_client.get_item(
            TableName="conversations",
            Key={"conversation_id": {"S": conversation_id}, "user_id": {"S": user_id}},
        )

        messages = response["Item"].get("messages", {"L": []})["L"]

        formatted_messages = [parse_dynamodb_message(msg) for msg in messages]

        sorted_messages = sorted(
            formatted_messages, key=lambda x: int(x.message_index), reverse=True
        )

        # Handle pagination
        start_index = last_evaluated_key if last_evaluated_key is not None else 0
        messages_to_return = sorted_messages[start_index : start_index + limit]

        # Calculate the new `last_evaluated_key`
        new_last_evaluated_key = start_index + len(messages_to_return)
        if new_last_evaluated_key >= len(sorted_messages):
            new_last_evaluated_key = (
                None  # End of the list, no more messages to paginate
            )

        logger.info(f"Fetched {len(messages_to_return)} messages")
        return {
            "messages": messages_to_return,
            "last_evaluated_key": new_last_evaluated_key,
        }

    except ClientError as e:
        logger.error(f"Error fetching messages: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching messages",
        )
