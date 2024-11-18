from typing import Dict
from typing import List

from conversation.services.dynamo_services import create_message
from conversation.services.dynamo_services import delete_message
from conversation.services.dynamo_services import get_message
from conversation.services.dynamo_services import get_recent_messages
from conversation.utils.schemas import AddMessageRequest
from conversation.utils.schemas import MessageResponse
from fastapi import APIRouter
from fastapi import Query


route = APIRouter()


@route.post("/add_messages/{conversation_id}", response_model=MessageResponse)
def new_message(conversation_id: str, payload: AddMessageRequest):
    """
    Creates a new Message for some conversation
    """
    create_message(conversation_id, payload)
    return MessageResponse(message="New message created")


@route.post("/{conversation_id}/delete_message")
def delete_mesage_r(conversation_id: str, message_index: int):
    """
    Deletes some message
    """
    delete_message(conversation_id, message_index)
    return MessageResponse(
        message=f"Message with id {message_index} from {conversation_id} deleted"
    )


@route.get("/{conversation_id}/messages/{message_index}")
def get_message_r(conversation_id: str, message_index: int):
    """
    Gets some message from some conversation
    """
    return get_message(conversation_id, message_index)


@route.get("/{conversation_id}/messages/", response_model=List[Dict])
async def get_recent_messages_route(
    conversation_id: str, offset: int = Query(0), limit: int = Query(16)
):
    """
    Gets the 16 last messages in a certain conversation
    """
    result = get_recent_messages(
        conversation_id=conversation_id, limit=limit, last_evaluated_key=offset
    )

    return result["messages"]
