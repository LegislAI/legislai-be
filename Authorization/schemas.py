from typing import Optional

from pydantic import BaseModel
from pydantic import EmailStr


class GetUser(BaseModel):
    email: EmailStr
    username: str
    role: int

    class Config:
        orm_mode = True
        use_enum_values = True


class LoginUser(BaseModel):
    email: Optional[EmailStr] = None  # Either email or username is required
    username: Optional[str] = None
    password: str

    class Config:
        orm_mode = True
        use_enum_values = True


# Model for user registration
class PostUser(BaseModel):
    email: EmailStr
    username: str
    password: str

    class Config:
        orm_mode = True
        use_enum_values = True
