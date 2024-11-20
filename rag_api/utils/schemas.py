from typing import Optional

from pydantic import BaseModel
from pydantic import EmailStr


class QueryResponsePayoad(BaseModel):
    response: Optional[str] = None
    summary: Optional[str] = None


class QueryRequestPayload(BaseModel):
    query: str
    attachments: Optional[str] = None


class UserDataResponse(BaseModel):
    user_id: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    plan: Optional[str] = None
    weekly_queries: Optional[str] = None
