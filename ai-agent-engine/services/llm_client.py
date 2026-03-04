

"""
- services/llm_client.py 内容要求：
  - 函数 chat_completion(system_prompt: str, user_message: str) -> str
  - 用 OpenAI SDK 的 client.chat.completions.create()
  - 参数：model、messages、temperature=0.7、max_tokens=1024
  - 返回 response.choices[0].message.content
"""
from config import settings
from openai import OpenAI, APIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import APITimeoutError as Timeout
from core.exceptions import LLMTimeoutError, LLMServiceError
client = OpenAI(api_key=settings.OPENAI_API_KEY)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((LLMTimeoutError, LLMServiceError))
)
def chat_completion(system_prompt: str, user_message: str):
    try:
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1024,
            temperature=0.7,
        )
    except Timeout:
        raise LLMTimeoutError("LLM 调用超时")
    except APIError:
        raise LLMServiceError("LLM 服务错误")
    return response.choices[0].message.content
