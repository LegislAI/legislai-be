import uuid
from typing import List

from conversation.services.dynamo_services import add_messages_to_conversation
from conversation.services.dynamo_services import add_messages_to_new_conversation
from conversation.services.dynamo_services import check_conversation
from conversation.services.dynamo_services import delete_all_conversations
from conversation.services.dynamo_services import delete_conversation
from conversation.services.dynamo_services import get_conversation
from conversation.services.dynamo_services import get_recent_conversations
from conversation.services.dynamo_services import get_recent_messages
from conversation.utils.auth_classes import decodeJWT
from conversation.utils.auth_classes import JWTBearer
from conversation.utils.exceptions import ConversationNotFound
from conversation.utils.exceptions import UserIDTokenNotFound
from conversation.utils.logging_config import logger
from conversation.utils.schemas import Conversation
from conversation.utils.schemas import ConversationResponse
from conversation.utils.schemas import Message
from conversation.utils.schemas import MessageResponse
from conversation.utils.schemas import NewConversationRequest
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials


route = APIRouter()


@route.post(
    "/new_conversation",
    response_model=ConversationResponse,
)
def create_new_conversation_route(
    payload: NewConversationRequest,
    credentials: HTTPAuthorizationCredentials = Depends(JWTBearer()),
):
    """
    Creates a new conversation
    """
    token = credentials.credentials

    try:
        user_id = decodeJWT(token)["sub"]
        add_messages_to_new_conversation(user_id, payload)

    except UserIDTokenNotFound as e:
        logger.error(f"Error creating new conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="UserID in token not found",
        )

    except Exception as e:
        logger.error(f"Error creating conversation: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating conversation",
        )

    return ConversationResponse(message="Conversation created successfully")


@route.delete(
    "/{conversation_id}/delete",
    response_model=ConversationResponse,
)
def delete_conversation_route(
    conversation_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(JWTBearer()),
):
    """
    Deletes an existing conversation by its ID.
    """
    token = credentials.credentials

    try:
        user_id = decodeJWT(token)["sub"]
        if check_conversation(user_id, conversation_id):
            delete_conversation(conversation_id, user_id)
        else:
            raise ConversationNotFound("Conversation not found")

    except ConversationNotFound as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    except UserIDTokenNotFound as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="UserID in token not found",
        )

    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting conversation",
        )

    return ConversationResponse(
        message=f"Conversation with id {conversation_id} deleted"
    )


@route.get(
    "/load_last_conversations",
    response_model=List[Conversation],
)
async def get_recent_conversations_route(
    offset: int = Query(0),
    limit: int = Query(10),
    credentials: HTTPAuthorizationCredentials = Depends(JWTBearer()),
):
    """
    Gets the 10 last conversations with the 16 last messages in each
    """
    token = credentials.credentials

    try:
        user_id = decodeJWT(token)["sub"]
        conversations = get_recent_conversations(user_id, offset=offset, limit=limit)
        return conversations

    except UserIDTokenNotFound as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="UserID in token not found",
        )

    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting conversations",
        )


@route.get(
    "/{conversation_id}",
    response_model=Conversation,
)
def get_conversation_route(
    conversation_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(JWTBearer()),
):
    """
    Gets a conversation by its ID
    """
    token = credentials.credentials

    try:
        user_id = decodeJWT(token)["sub"]
        if check_conversation(user_id, conversation_id):
            return get_conversation(conversation_id, user_id)
        else:
            raise ConversationNotFound("Conversation not found")

    except ConversationNotFound as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    except UserIDTokenNotFound as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="UserID in token not found",
        )

    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting conversation",
        )


@route.delete(
    "/delete_all_conversations",
    response_model=MessageResponse,
)
async def delete_all_conversation_route(
    credentials: HTTPAuthorizationCredentials = Depends(JWTBearer()),
):
    """
    Deletes all the conversations
    """
    token = credentials.credentials

    try:
        user_id = decodeJWT(token)["sub"]
        delete_all_conversations(user_id)
        return MessageResponse(message="All conversations deleted")

    except UserIDTokenNotFound as e:
        logger.error(f"Error deleting conversations: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in token",
        )

    except Exception as e:
        logger.error(f"Error deleting conversations: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting conversations",
        )


@route.post(
    "/{conversation_id}/add_messages",
    response_model=MessageResponse,
)
def add_messages_route(
    conversation_id: str,
    messages: List[Message],
    credentials: HTTPAuthorizationCredentials = Depends(JWTBearer()),
):
    """
    Creates a new Message for some conversation
    """
    token = credentials.credentials

    try:
        user_id = decodeJWT(token)["sub"]
        if check_conversation(user_id, conversation_id):
            add_messages_to_conversation(user_id, conversation_id, messages)
        else:
            raise ConversationNotFound("Conversation not found")

    except ConversationNotFound as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    except UserIDTokenNotFound as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in token",
        )

    except Exception as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating message",
        )

    return MessageResponse(message="New message created")


@route.get(
    "/{conversation_id}/messages/load_last_messages",
    response_model=List[Message],
)
async def get_recent_messages_route(
    conversation_id: str,
    offset: int = Query(0),
    limit: int = Query(16),
    credentials: HTTPAuthorizationCredentials = Depends(JWTBearer()),
):
    """
    Gets the 16 last messages of a conversation
    """
    token = credentials.credentials

    try:
        user_id = decodeJWT(token)["sub"]
        if check_conversation(user_id, conversation_id):
            return get_recent_messages(
                user_id,
                conversation_id=conversation_id,
                last_evaluated_key=offset,
                limit=limit,
            )["messages"]
        else:
            raise ConversationNotFound("Conversation not found")

    except ConversationNotFound as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    except UserIDTokenNotFound as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in token",
        )

    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting messages",
        )
