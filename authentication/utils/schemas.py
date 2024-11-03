from typing import Optional

from pydantic import BaseModel
from pydantic import EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: Optional[str] = None


class RegisterResponse(BaseModel):
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    user_id: str
    email: EmailStr
    username: str
    access_token: str
    refresh_token: str


class LogoutRequest(BaseModel):
    email: EmailStr


class LogoutResponse(BaseModel):
    message: str


class RefreshTokenRequest(BaseModel):
    email: EmailStr


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
