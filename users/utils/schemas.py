from typing import Optional

from pydantic import BaseModel
from pydantic import EmailStr


class UsersResponse(BaseModel):
    user_id: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    plan: Optional[str] = None


class UsersRequestPayload(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None


class UsersUpdatePlanRequest(BaseModel):
    plan: str


class UsersPlanResponse(BaseModel):
    user_id: str
    plan: str
