import json
import math

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from ocr.main import process_rag_queries
from rag import main as rag
from services.dynamo_services import get_user_by_id
from services.dynamo_services import update_user_fields
from utils.exceptions import UserNotFoundException
from utils.logging_config import logger
from utils.password import SecurityUtils
from utils.schemas import QueryRequestPayload
from utils.schemas import QueryResponsePayload
from utils.utils import decodeJWT
from utils.utils import JWTBearer

route = APIRouter()
security = SecurityUtils()
rag_service = rag.RAG()


PLAN_QUERIES_MAP = {
    "free": 10,
    "premium": math.inf,
    "premium_plus": math.inf,
}


@route.post("/query")
async def query(
    payload: QueryRequestPayload,
    credentials: HTTPAuthorizationCredentials = Depends(JWTBearer()),
):
    try:
        token = credentials.credentials
        user_id = decodeJWT(token)["sub"]

        logger.info(f"Received a request to query from user with id: {user_id}")

        user = get_user_by_id(user_id)
        user_queries = int(user.weekly_queries)
        queries_for_plan = PLAN_QUERIES_MAP[user.plan]

        logger.info(
            f"User queries: {user_queries}, Queries for plan: {queries_for_plan}"
        )

        if user_queries >= queries_for_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query limit exceeded",
            )

        if payload.attachments and user.plan != "premium_plus":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attachments are only allowed for premium plus users",
            )

        if payload.attachments and user.plan == "premium_plus":
            logger.info("Processing OCR queries")
        else:
            user_queries += 1
            update_user_fields(
                user_id=user_id,
                email=user.email,
                fields={"weekly_queries": str(user_queries)},
            )

        async def event_stream():
            async for chunk in rag_service.stream_answer(query=payload.query, topk=5):
                dump = json.dumps(
                    {
                        "response": chunk.get("answer"),
                        "summary": chunk.get("summary"),
                        "references": chunk.get("references"),
                    },
                    ensure_ascii=False,
                )
                yield f"data: {dump}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found with id: {user_id}",
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )
