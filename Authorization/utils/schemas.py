from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr


class GetUser(BaseModel):
    userid: str
    email: EmailStr
    username: str
    # role: int
    ConfigDict(from_attributes=True, use_enum_values=True)


class LoginUser(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    password: Optional[str] = None
    ConfigDict(from_attributes=True, use_enum_values=True)


class CreateUser(BaseModel):
    email: EmailStr
    username: str
    password: Optional[str] = None
    ConfigDict(from_attributes=True, use_enum_values=True)

    # class Config:
    #     from_attributes = True
    #     use_enum_values = True
