import uvicorn
from fastapi import FastAPI
from routes.stream_route import route as stream_route

app = FastAPI()
app.include_router(stream_route, prefix="/stream", tags=["Answer"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5005, reload=True)
