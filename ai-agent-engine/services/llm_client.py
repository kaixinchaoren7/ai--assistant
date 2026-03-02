

"""
- services/llm_client.py 内容要求：
  - 函数 chat_completion(system_prompt: str, user_message: str) -> str
  - 用 OpenAI SDK 的 client.chat.completions.create()
  - 参数：model、messages、temperature=0.7、max_tokens=1024
  - 返回 response.choices[0].message.content
"""
from config import settings
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def chat_completion(system_prompt:str,user_message:str):
    response = client.chat.completions.create(
        model=settings.MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=1024,
        temperature=0.7,
    )
    return response.choices[0].message.content