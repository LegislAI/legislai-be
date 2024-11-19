
import uuid
from typing import List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from services.dynamo_services import add_messages_to_conversation
from services.dynamo_services import add_messages_to_new_conversation
from services.dynamo_services import check_conversation
from services.dynamo_services import delete_all_conversations
from services.dynamo_services import delete_conversation
from services.dynamo_services import get_conversation
from services.dynamo_services import get_recent_conversations
from services.dynamo_services import get_recent_messages
from utils.auth_classes import JWTBearer
from utils.exceptions import ConversationNotFound
from utils.logging_config import logger
from utils.schemas import AddMessageRequest
from utils.schemas import Conversation
from utils.schemas import ConversationRequest
from utils.schemas import ConversationResponse
from utils.schemas import Message
from utils.schemas import MessageResponse
from utils.schemas import NewConversationRequest


route = APIRouter()


@route.post(
    "/new_conversation",
    response_model=ConversationResponse,
    dependencies=[Depends(JWTBearer())],
)
def create_new_conversation_route(
    payload: NewConversationRequest,
):
    """
    Creates a new conversation
    """
    conversation_id = str(uuid.uuid4())

    try:
        add_messages_to_new_conversation(conversation_id, payload)

    except Exception as e:
        logger.error(f"Error creating conversation: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating conversation",
        )

    return ConversationResponse(conversation_id=conversation_id)


@route.delete(
    "/{conversation_id}/delete",
    response_model=ConversationResponse,
    dependencies=[Depends(JWTBearer())],
)
def delete_conversation_route(
    payload: ConversationRequest,
):
    """
    Deletes an existing conversation by its ID.
    """
    user_id, conversation_id = payload.user_id, payload.conversation_id

    try:
        if check_conversation(user_id, conversation_id):
            delete_conversation(conversation_id,user_id)
        else:
            raise ConversationNotFound("Conversation not found")

    except ConversationNotFound as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting conversation",
        )

    return ConversationResponse(
        conversation_id=f"Conversation with id {conversation_id} deleted"
    )


@route.get(
    "/{conversation_id}",
    response_model=Conversation,
    dependencies=[Depends(JWTBearer())],
)
def get_conversation_route(
    user_id: str,
    conversation_id: str,
):
    """
    Gets a conversation by its ID
    """
    try:
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

    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting conversation",
        )


@route.get(
    "/load_last_conversations/",
    response_model=List[Conversation],
    dependencies=[Depends(JWTBearer())],
)
async def get_recent_conversations_route(
    user_id: str,
    offset: int = Query(0),
    limit: int = Query(10),
):
    """
    Gets the 10 last conversations with the 16 last messages in each
    """
    try:
        conversations = get_recent_conversations(user_id, offset=offset, limit=limit)
        return conversations

    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting conversations",
        )


@route.delete(
    "/delete_all_conversations",
    response_model=MessageResponse,
    dependencies=[Depends(JWTBearer())],
)
async def delete_all_conversation_route(user_id: str):
    """
    Deletes all the conversations
    """
    try:
        delete_all_conversations(user_id)
        return MessageResponse(message="All conversations deleted")

    except Exception as e:
        logger.error(f"Error deleting conversations: {e.response['Error']['Message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting conversations",
        )


@route.post(
    "/{conversation_id}/add_messages",
    response_model=MessageResponse,
    dependencies=[Depends(JWTBearer())],
)
def add_messages_route(
    payload: AddMessageRequest,
):
    """
    Creates a new Message for some conversation
    """
    user_id, conversation_id = payload.user_id, payload.conversation_id
    try:
        if check_conversation(user_id, conversation_id):
            add_messages_to_conversation(conversation_id, payload)
        else:
            raise ConversationNotFound("Conversation not found")

    except ConversationNotFound as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    except Exception as e:
        logger.error(f"Error creating message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating message",
        )

    return MessageResponse(message="New message created")


@route.get(
    "/{conversation_id}/messages/load_last_messages/",
    response_model=List[Message],
    dependencies=[Depends(JWTBearer())],
)
async def get_recent_messages_route(
    user_id: str,
    conversation_id: str,
    offset: int = Query(0),
    limit: int = Query(16),
):
    """
    Gets the 16 last messages of a conversation
    """
    try:
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

    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting messages",
        )
