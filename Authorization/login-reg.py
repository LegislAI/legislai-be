from datetime import timedelta

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from schemas import GetUser
from schemas import LoginUser
from schemas import PostUser
from sqlalchemy.orm import Session
from utils.auth import create_access_token
from utils.auth import create_refresh_token
from utils.auth import create_user
from utils.auth import get_user

# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


route = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2bearer = OAuth2PasswordBearer(tokenUrl="auth/login")

# Register new user using email, username, password
@route.post("/register", response_model=GetUser)
def register_user(payload: PostUser, db: Session = Depends(get_db)):

    if not payload.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please add Email",
        )
    user_by_email = get_user(db, payload.email)
    user_by_username = get_user(db, payload.username)
    if user_by_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User with email {payload.email} already exists",
        )

    if user_by_username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User with username {payload.username} already exists",
        )
    user = create_user(db, payload)

    return user


@route.post("/login")
def login_user(
    payload: LoginUser,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login user based on email and password
    """
    if not payload.email and not payload.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please provide email or username",
        )

    user = get_user(db, payload.email or payload.username)
    if not user or not user.check_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token(user.id, timedelta(minutes=30))
    refresh = create_refresh_token(user.id, timedelta(minutes=1008))

    return {
        "access_token": token,
        "token_type": "bearer",
        "refresh_token": refresh,
        "user_id": user.id,
    }
