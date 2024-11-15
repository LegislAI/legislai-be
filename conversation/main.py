from conversation.config.settings import settings
from conversation.routes.conversation_routes import route as conversation_routes
from conversation.routes.messages_routes import route as messages_routes
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(conversation_routes, prefix="/conversations", tags=["conversation"])
app.include_router(messages_routes, prefix="/conversations", tags=["messages"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
