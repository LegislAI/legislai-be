import json

from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import StreamingResponse
from generator import RAGPrompt
from streaming import StreamingRAG
from utils.logging import logger
from utils.schemas import RAGRequest

app = FastAPI()
route = APIRouter()


@route.post("/answer")
async def stream_rag_answer(request: RAGRequest):
    try:
        streaming_rag = StreamingRAG(RAGPrompt())
        logger.info(f"Streaming -> {streaming_rag}")

        async def event_stream():
            async for chunk in streaming_rag.stream_answer(
                request.context, request.question, request.code_rag
            ):
                yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error in streaming: {str(e)}")
        return {"error": str(e)}
