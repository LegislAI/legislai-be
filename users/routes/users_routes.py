from datetime import datetime
from datetime import timezone

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from config.settings import settings
from services.dynamo_services import get_user_by_id
from services.dynamo_services import update_user_info
from services.dynamo_services import update_user_plan as service_update_plan
from utils.exceptions import UserNotFoundException
from utils.logging_config import logger
from utils.password import SecurityUtils
from utils.schemas import UsersPlanResponse
from utils.schemas import UsersRequestPayload
from utils.schemas import UsersResponse
from utils.schemas import UsersUpdatePlanRequest
from utils.users import decodeJWT
from utils.users import is_authenticated
from utils.users import JWTBearer

route = APIRouter()
security = SecurityUtils()


@route.get("/", response_model=UsersResponse)
def get_user_info(credentials: HTTPAuthorizationCredentials = Depends(JWTBearer())):
    init_time = datetime.now(timezone.utc)
    token = credentials.credentials

    if not is_authenticated(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    try:
        user_id = decodeJWT(token)["sub"]
        logger.info(
            f"Received request to get user with id: {user_id} info at {init_time}"
        )
        user = get_user_by_id(user_id)

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


@route.patch("/", response_model=UsersResponse)
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
        user_id = decodeJWT(token)["sub"]
        response = update_user_info(payload, user_id)
        return response
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found with id: {user_id}",
        )
    except Exception as e:
        logger.error(f"Failed to update user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user information",
        )


@route.get("/plan/", response_model=UsersPlanResponse)
def get_user_plan(credentials: HTTPAuthorizationCredentials = Depends(JWTBearer())):
    token = credentials.credentials

    if not is_authenticated(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    user_id = decodeJWT(token)["sub"]

    try:
        user = get_user_by_id(user_id)
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


@route.patch("/plan/", response_model=UsersPlanResponse)
def update_user_plan(
    plan_request: UsersUpdatePlanRequest,
    credentials: HTTPAuthorizationCredentials = Depends(JWTBearer()),
):
    plans_name = ["free", "premium", "premium_plus"]
    token = credentials.credentials

    if not is_authenticated(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    user_id = decodeJWT(token)["sub"]
    user = get_user_by_id(user_id)
    try:
        if plan_request.plan not in plans_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan name",
            )

        response = service_update_plan(user_id, user.email, plan_request.plan)
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
