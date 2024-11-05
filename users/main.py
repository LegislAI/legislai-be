from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from users.config.settings import settings
from users.routes.users_routes import route as users_routes

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(users_routes, prefix="/users", tags=["Users"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
