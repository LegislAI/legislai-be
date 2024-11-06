import uuid
from datetime import datetime
from datetime import timezone
from typing import Dict
from typing import List

import boto3
from authentication.utils.logging_config import logger
from botocore.exceptions import ClientError
from conversation.config.settings import settings
from conversation.utils.schemas import AddMessageRequest
from conversation.utils.schemas import NewConversationRequest
from fastapi import HTTPException
from fastapi import status

# Flow deverá ser algo como
# Clica em nova conversa -- create_conversation (nunca se pode mandar mensagens a uma conversa que n exista)
# Escreve algo para ser interpretado -- create_message (aqui o campo field e name da conversa são mudados)
# AI responde -- create_message


boto3_client = boto3.client(
    "dynamodb",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region,
)


def check_conversation_exists(conversation_id: str) -> bool:
    response = boto3_client.get_item(
        TableName="conversations", Key={"conversation_id": {"S": conversation_id}}
    )
    return "Item" in response


def create_conversation() -> Dict:
    while True:
        conversation_id = str(uuid.uuid4())
        if not check_conversation_exists(conversation_id):
            break

    conversation_name = "Nova conversa"
    conversation_field = "Ainda não foi possivel obter o tema"

    updated_at = datetime.now(timezone.utc).isoformat() + "Z"

    # Initial message if we wnat to use it
    initial_message = {
        "M": {
            "message_index": {"S": "0"},
            "sender": {"S": "AI"},
            "timestamp": {"S": updated_at},
            "message": {"S": "Olá!! Em que posso ser útil?"},
            "attachments": {"L": []},
        }
    }

    formatted_messages = [initial_message]

    try:
        boto3_client.put_item(
            TableName="conversations",
            Item={
                "conversation_id": {"S": conversation_id},
                "conversation_name": {"S": conversation_name},
                "conversation_field": {"S": conversation_field},
                "updated_at": {"S": updated_at},
                "messages": {"L": formatted_messages},
            },
        )
        logger.info("Conversation created successfully")
        return {
            "conversation_id": conversation_id,
            "conversation_name": conversation_name,
            "conversation_field": conversation_field,
            "updated_at": updated_at,
            "messages": formatted_messages,
        }
    except ClientError as e:
        logger.error(f"Error creating conversation: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating conversation",
        )


def alter_name_theme_conversation(conversation_id: str, name: str, theme: str) -> None:
    try:
        boto3_client.update_item(
            TableName="conversations",
            Key={"conversation_id": {"S": conversation_id}},
            UpdateExpression="SET conversation_name = :new_name, theme = :new_theme",
            ExpressionAttributeValues={
                ":new_name": {"S": name},
                ":new_theme": {"S": theme},
            },
        )
        logger.info(
            f"Conversation {conversation_id} updated with new name: {name} and theme: {theme}."
        )
    except ClientError as e:
        logger.error(
            f"Error updating conversation name and theme: {e.response['Error']['Message']}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating conversation name and theme",
        )


def delete_conversation(conversation_id: str) -> Dict:
    try:
        # Check if the conversation exists before attempting deletion
        response = boto3_client.get_item(
            TableName="conversations", Key={"conversation_id": {"S": conversation_id}}
        )

        if "Item" not in response:
            logger.info(f"Conversation {conversation_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

        boto3_client.delete_item(
            TableName="conversations", Key={"conversation_id": {"S": conversation_id}}
        )

        logger.info(f"Conversation {conversation_id} deleted successfully")
        return {"message": f"Conversation {conversation_id} deleted successfully"}

    except ClientError as e:
        logger.error(f"Error deleting conversation: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting conversation",
        )


def get_conversation(conversation_id: str):
    try:
        response = boto3_client.get_item(
            TableName="conversations", Key={"conversation_id": {"S": conversation_id}}
        )

        if "Item" not in response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
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
                    "message_index": int(msg["M"]["message_index"]["S"]),
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


def get_recent_conversations(offset: int = 0, limit: int = 10) -> List[Dict]:
    try:
        response = boto3_client.scan(
            TableName="conversations",
            ProjectionExpression="conversation_id, conversation_name,conversation_field, updated_at",
            Limit=offset + limit,
        )

        # Ordena as conversas pelo campo `updated_at` pela ordem decrescente
        conversations = sorted(
            response.get("Items", []), key=lambda x: x["updated_at"]["S"], reverse=True
        )

        # Retorna apenas o intervalo entre `offset` e `offset + limit`
        paginated_conversations = conversations[offset : offset + limit]

        conversations_with_messages = []
        for conv in paginated_conversations:
            conversation_id = conv["conversation_id"]["S"]

            recent_messages = get_recent_messages(
                conversation_id=conversation_id, last_evaluated_key=0, limit=16
            )

            conversation_with_messages = {
                "conversation_id": conversation_id,
                "conversation_name": conv["conversation_name"]["S"],
                "conversation_field": conv["conversation_field"]["S"],
                "updated_at": conv["updated_at"]["S"],
                "recent_messages": recent_messages,
            }
            conversations_with_messages.append(conversation_with_messages)

        return conversations_with_messages
    except ClientError as e:
        logger.error(
            f"Error retrieving conversations: {e.response['Error']['Message']}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving conversations",
        )


# Just for Testing purposes
def delete_all_conversations() -> Dict:
    try:
        # Fazer uma leitura de todas as conversas na tabela
        response = boto3_client.scan(TableName="conversations")

        # Verificar se há conversas na tabela
        if "Items" not in response or not response["Items"]:
            logger.info("No conversations found to delete.")
            return {"message": "No conversations to delete."}

        # Excluir todas as conversas
        for item in response["Items"]:
            conversation_id = item["conversation_id"]["S"]

            # Deletar a conversa
            boto3_client.delete_item(
                TableName="conversations",
                Key={"conversation_id": {"S": conversation_id}},
            )
            logger.info(f"Deleted conversation {conversation_id}.")

        return {"message": "All conversations have been deleted successfully."}

    except ClientError as e:
        logger.error(f"Error deleting conversations: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting conversations",
        )


#####################################################################################################################


def create_message(conversation_id: str, payload: AddMessageRequest) -> Dict:
    try:
        response = boto3_client.get_item(
            TableName="conversations",
            Key={"conversation_id": {"S": conversation_id}},
        )

        logger.info(f"Conversation {conversation_id} found. Adding messages.")
        existing_messages = response["Item"].get("messages", {"L": []})["L"]

        current_index = (
            int(existing_messages[-1]["M"]["message_index"]["S"]) + 1
            if existing_messages
            else 0
        )

        # Formatar e adicionar as novas mensagens(se no futuro quisermos por mais do que uma mensagem)
        new_formatted_messages = []
        for i, message in enumerate(payload.messages):
            current_timestamp = datetime.now(timezone.utc).isoformat() + "Z"
            formatted_message = {
                "M": {
                    "message_index": {"S": str(current_index + i)},
                    "sender": {"S": message.sender},
                    "timestamp": {"S": current_timestamp},
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
            existing_messages.append(formatted_message)
            new_formatted_messages.append(formatted_message)

            # FIXME: these two need the logic to be retrieved correctly
            if i == 0:
                new_conversation_name = "name"
                new_theme = "theme"

                alter_name_theme_conversation(
                    conversation_id, new_conversation_name, new_theme
                )

        # Atualizar a conversa com as novas mensagens e atualizar o campo `updated_at`
        updated_at = datetime.now(timezone.utc).isoformat() + "Z"
        boto3_client.update_item(
            TableName="conversations",
            Key={"conversation_id": {"S": conversation_id}},
            UpdateExpression="SET messages = :messages, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":messages": {"L": existing_messages},
                ":updated_at": {"S": updated_at},
            },
        )

        logger.info(f"Messages processed for conversation {conversation_id}")
        return {
            "conversation_id": conversation_id,
            "new_messages": new_formatted_messages,
        }

    except ClientError as e:
        logger.error(f"Error processing conversation: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing conversation",
        )


def delete_message(conversation_id: str, message_index: int) -> Dict:
    try:
        response = boto3_client.get_item(
            TableName="conversations", Key={"conversation_id": {"S": conversation_id}}
        )

        if "Item" not in response:
            logger.info(f"Conversation {conversation_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

        existing_messages = response["Item"].get("messages", {"L": []})["L"]
        updated_messages = [
            msg
            for msg in existing_messages
            if int(msg["M"]["message_index"]["S"]) != message_index
        ]

        if len(updated_messages) == len(existing_messages):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
            )

        updated_at = datetime.now(timezone.utc).isoformat() + "Z"
        boto3_client.update_item(
            TableName="conversations",
            Key={"conversation_id": {"S": conversation_id}},
            UpdateExpression="SET messages = :messages, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":messages": {"L": updated_messages},
                ":updated_at": {"S": updated_at},
            },
        )

        logger.info(
            f"Message {message_index} deleted from conversation {conversation_id}"
        )
        return {
            "conversation_id": conversation_id,
            "deleted_message_index": message_index,
        }

    except ClientError as e:
        logger.error(f"Error deleting message: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting message",
        )


def get_message(conversation_id: str, message_index: int):
    try:
        response = boto3_client.get_item(
            TableName="conversations", Key={"conversation_id": {"S": conversation_id}}
        )

        if "Item" not in response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

        messages = response["Item"]["messages"]["L"]
        for msg in messages:
            if int(msg["M"]["message_index"]["S"]) == message_index:
                message = {
                    "message_index": int(msg["M"]["message_index"]["S"]),
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
                logger.info(
                    f"Message {message_index} from conversation {conversation_id} retrieved successfully."
                )
                return message

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found in the conversation",
        )

    except ClientError as e:
        logger.error(f"Error retrieving message: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving message",
        )


def get_recent_messages(
    conversation_id: str, limit: int, last_evaluated_key: int = None
) -> Dict:
    try:
        response = boto3_client.get_item(
            TableName="conversations",
            Key={"conversation_id": {"S": conversation_id}},
        )

        # Check if the conversation exists
        if "Item" not in response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

        # Retrieve and sort messages by `message_index` in descending order
        messages = response["Item"].get("messages", {"L": []})["L"]
        sorted_messages = sorted(
            messages, key=lambda x: int(x["M"]["message_index"]["S"]), reverse=True
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
