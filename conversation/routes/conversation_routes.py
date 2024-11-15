from typing import Dict
from typing import List

from conversation.services.dynamo_services import create_conversation
from conversation.services.dynamo_services import delete_all_conversations
from conversation.services.dynamo_services import delete_conversation
from conversation.services.dynamo_services import get_conversation
from conversation.services.dynamo_services import get_recent_conversations
from conversation.utils.schemas import ConversationResponse
from conversation.utils.schemas import NewConversationRequest
from fastapi import APIRouter
from fastapi import Query


route = APIRouter()


@route.post("/new_conversation", response_model=ConversationResponse)
def new_conversation():
    """
    Creates a new conversation
    """
    create_conversation()
    return ConversationResponse(message="New conversation created")


@route.post("/{conversation_id}/delete", response_model=ConversationResponse)
def delete_conversation_r(conversation_id: str):
    """
    Deletes an existent conversation
    """
    delete_conversation(conversation_id)
    return ConversationResponse(
        message=f"Convesation with id {conversation_id} deleted"
    )


@route.get("/{conversation_id}")
def get_conversation_r(conversation_id: str):
    """
    Retrieves an existing conversation by its ID.
    """
    return get_conversation(conversation_id)


@route.get("/", response_model=List[Dict])
async def get_recent_conversations_route(
    offset: int = Query(0), limit: int = Query(10)
):
    """
    Gets the 10 most recent conversations. Supports pagination.
    """
    return get_recent_conversations(offset=offset, limit=limit)


@route.post("/")
async def delete_all_conversation_r():
    """
    JUST FOR TESTING
    Deletes all the conversations
    """
    return delete_all_conversations()
