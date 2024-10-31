from typing import Optional

from pydantic import BaseModel
from pydantic import EmailStr


class RegisterUserRequest(BaseModel):
    email: EmailStr
    username: str
    password: Optional[str] = None


class RegisterUserResponse(BaseModel):
    userid: str
    email: EmailStr
    username: str


class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str


class LoginUserResponse(BaseModel):
    userid: str
    email: EmailStr
    username: str
    access_token: str
    refresh_token: str
    access_token_expire_minutes: int
    refresh_token_expire_minutes: int


class LogoutResponse(BaseModel):
    message: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetResponse(BaseModel):
    message: str

class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str