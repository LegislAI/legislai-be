from config.settings import settings
from fastapi import FastAPI
from routes.conversation_routes import route as conversation_routes
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(conversation_routes, prefix="/conversations", tags=["conversation"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=5003, reload=True)
