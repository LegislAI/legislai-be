import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conversation.config.settings import settings
from conversation.routes.conversation_routes import route as conversation_routes
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(conversation_routes, prefix="/conversations", tags=["conversation"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("conversation.main:app", host="127.0.0.1", port=5001, reload=True)
