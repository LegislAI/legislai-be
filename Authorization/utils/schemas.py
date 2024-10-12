from typing import Optional

from pydantic import BaseModel
from pydantic import EmailStr


class GetUser(BaseModel):
    userid: str
    email: EmailStr
    username: str
    # role: int

    class Config:
        from_attributes = True
        use_enum_values = True


class LoginUser(BaseModel):
    email: Optional[EmailStr] = None  # Either email or username is required
    username: Optional[str] = None
    password: str

    class Config:
        from_attributes = True
        use_enum_values = True


class CreateUser(BaseModel):
    email: EmailStr
    username: str
    password: str

    class Config:
        from_attributes = True
        use_enum_values = True
