from typing import List
from typing import Optional

from pydantic import BaseModel


class Attachment(BaseModel):
    content: str
    designation: str
    url: str


class Message(BaseModel):
    message_index: str
    sender: str
    timestamp: str
    message: str
    attachments: Optional[List[Attachment]] = []


class Conversation(BaseModel):
    conversation_id: str
    conversation_name: str
    conversation_field: str
    updated_at: str
    messages: List[Message]


class NewConversationRequest(BaseModel):
    user_id: str
    messages: List[Message]
    conversation_name: str
    conversation_field: str
    conversation_id: str


class ConversationRequest(BaseModel):
    user_id: str
    conversation_id: str


class ConversationResponse(BaseModel):
    conversation_id: str


class AddMessageRequest(BaseModel):
    user_id: str
    conversation_id: str
    messages: List[Message]


class MessageResponse(BaseModel):
    message: str
