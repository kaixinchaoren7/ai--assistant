

from pydantic import BaseModel

class ChatRequest(BaseModel):
    message:str


class ChatResponse(BaseModel):
    answer:str
    trace_id:str