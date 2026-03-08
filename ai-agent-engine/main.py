# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from fastapi import FastAPI
from pydantic import BaseModel

from middleware.trace_id import TraceIdMiddleware
from routers.chat import router as chat_router

app = FastAPI()
app.add_middleware(TraceIdMiddleware)
app.include_router(chat_router)


@app.get("/")
async def root():
    return{
    "message": "Hello World"
}

@app.get("/health")
def health():
    return{"message":"AI Agent Engineer"}
