import math
from datetime import datetime
from datetime import timezone

from config.settings import settings
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from services.dynamo_services import get_user_by_id
from services.dynamo_services import update_user_fields
from utils.exceptions import UserNotFoundException
from utils.logging_config import logger
from utils.password import SecurityUtils
from utils.schemas import QueryRequestPayload
from utils.schemas import QueryResponsePayoad
from utils.utils import decodeJWT
from utils.utils import is_authenticated
from utils.utils import JWTBearer

route = APIRouter()
security = SecurityUtils()


PLAN_QUERIES_MAP = {
    "free": 10,
    "premium": math.inf,
    "premium_plus": math.inf,
}


@route.post("/query", response_model=QueryResponsePayoad)
def query(
    payload: QueryRequestPayload,
    credentials: HTTPAuthorizationCredentials = Depends(JWTBearer()),
):
    try:
        token = credentials.credentials

        if not is_authenticated(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized",
            )

        user_id = decodeJWT(token)["sub"]

        logger.info(f"Received a request to query from user with id: {user_id}")

        user = get_user_by_id(user_id)
        user_queries = int(user.daily_queries)

        queries_for_plan = PLAN_QUERIES_MAP[user.plan]

        if user_queries < queries_for_plan:
            if payload.attachments and user.plan != "premium_plus":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Attachments are only allowed for premium plus users",
                )

            elif payload.attachments and user.plan == "premium_plus":
                # Implement auto rag
                pass
            else:
                user_queries += 1
                update_user_fields(
                    user_id=user_id,
                    email=user.email,
                    fields={"daily_queries": str(user_queries)},
                )
                return QueryResponsePayoad(
                    response="This is a response", summary="This is a summary"
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query limit exceeded",
            )

    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found with id: {user_id}",
        )
