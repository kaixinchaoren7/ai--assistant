from fastapi import APIRouter

from schemas.chat import ChatRequest
from schemas.chat import ChatResponse
import uuid

from services import llm_client

router = APIRouter()

@router.post("/chat")
async def get_chat(chatRequest:ChatRequest):
    res = llm_client.chat_completion("你是一个有帮助的AI助手，用中文回答。",chatRequest.message)
    return res

