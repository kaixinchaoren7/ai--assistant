import uuid

from core.exceptions import LLMTimeoutError, LLMServiceError
from schemas.chat import ChatResponse
from services import llm_client


def safe_chat(message: str) -> ChatResponse:
    try:
        answer = llm_client.chat_completion(
            "你是一个有帮助的AI助手，用中文回答。", message
        )
    except LLMTimeoutError:
        answer = "请求超时，请稍后重试"
    except LLMServiceError:
        answer = "服务暂时不可用，请稍后重试"
    return ChatResponse(answer=answer, trace_id=str(uuid.uuid4()))
