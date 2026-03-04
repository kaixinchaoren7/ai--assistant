from fastapi import APIRouter

from schemas.chat import ChatRequest
from services import chat_service

router = APIRouter()

@router.post("/chat")
async def get_chat(chatRequest: ChatRequest):
    return chat_service.safe_chat(chatRequest.message)
