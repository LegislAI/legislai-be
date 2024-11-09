import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from authentication.config.settings import settings
from authentication.routes.auth_routes import route as auth_routes
from authentication.routes.google_routes import route as google_routes
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware


app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(auth_routes, prefix="/auth", tags=["Authentication"])
app.include_router(google_routes, prefix="/auth", tags=["Google OAuth"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("authentication.main:app", host="127.0.0.1", port=5002, reload=True)
