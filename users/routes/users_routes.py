from datetime import datetime
from datetime import timezone

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from users.config.settings import settings
from users.services.dynamo_services import get_user_by_email
from users.services.dynamo_services import update_user_info
from users.services.dynamo_services import update_user_plan as service_update_plan
from users.utils.exceptions import UserNotFoundException
from users.utils.logging_config import logger
from users.utils.password import SecurityUtils
from users.utils.schemas import UsersPlanResponse
from users.utils.schemas import UsersRequestPayload
from users.utils.schemas import UsersResponse
from users.utils.schemas import UsersUpdatePlanRequest
from users.utils.users import decodeJWT
from users.utils.users import is_authenticated
from users.utils.users import JWTBearer

route = APIRouter()
security = SecurityUtils()


@route.get("/{user_id}", response_model=UsersResponse)
def get_user_info(
    user_id: str, credentials: HTTPAuthorizationCredentials = Depends(JWTBearer())
):
    init_time = datetime.now(timezone.utc)
    token = credentials.credentials

    logger.info(f"Received request to get user with id: {user_id} info at {init_time}")

    if not is_authenticated(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    try:
        user_email = decodeJWT(token)["sub"]
        user = get_user_by_email(user_email)

        return user
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found with id: {user_id}",
        )
    except Exception as e:
        logger.error(f"Failed to fetch user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user information",
        )
    finally:
        end_time = datetime.now(timezone.utc)
        logger.info(
            f"Completed request to get user info for user_id: {user_id} at {end_time}. Duration: {end_time - init_time}"
        )


@route.patch("/{user_id}", response_model=UsersResponse)
def update_user(
    credentials: HTTPAuthorizationCredentials = Depends(JWTBearer()),
    payload: UsersRequestPayload = Depends(),
):
    token = credentials.credentials

    if not is_authenticated(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    try:
        user_email = decodeJWT(token)["sub"]
        response = update_user_info(payload, user_email)
        return response
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found with email: {user_email}",
        )
    except Exception as e:
        logger.error(f"Failed to update user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user information",
        )


@route.get("/plan/{user_id}", response_model=UsersPlanResponse)
def get_user_plan(
    user_id: str, credentials: HTTPAuthorizationCredentials = Depends(JWTBearer())
):
    token = credentials.credentials

    if not is_authenticated(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    email = decodeJWT(token)["sub"]

    try:
        user = get_user_by_email(email)
        return UsersPlanResponse(user_id=user_id, plan=user.plan)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found with id: {user_id}",
        )
    except Exception as e:
        logger.error(f"Failed to fetch user plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user plan",
        )


@route.patch("/plan/{user_id}", response_model=UsersPlanResponse)
def update_user_plan(
    user_id: str,
    plan_request: UsersUpdatePlanRequest,
    credentials: HTTPAuthorizationCredentials = Depends(JWTBearer()),
):
    token = credentials.credentials

    if not is_authenticated(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    email = decodeJWT(token)["sub"]

    try:
        response = service_update_plan(user_id, email, plan_request.plan)
        return response
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not with id: {user_id} found",
        )
    except Exception as e:
        logger.error(f"Failed to update user plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user plan for user: {user_id}",
        )
