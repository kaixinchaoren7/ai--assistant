# Day 2 学习记录

## 今日改动概览

### 1. 新增 `core/exceptions.py` —— 自定义异常类

```python
class LLMTimeoutError(Exception):
    """LLM 调用超时异常"""
    pass

class LLMServiceError(Exception):
    """LLM 服务通用错误异常"""
    pass
```

- 定义了两个自定义异常，用于统一封装 LLM 调用过程中的错误类型
- `LLMTimeoutError`：LLM 接口调用超时
- `LLMServiceError`：LLM 服务通用错误（如 API 返回错误码）

### 2. 新增 `services/chat_service.py` —— 业务层（降级兜底）

```python
def safe_chat(message: str) -> ChatResponse:
    try:
        answer = llm_client.chat_completion("你是一个有帮助的AI助手，用中文回答。", message)
    except LLMTimeoutError:
        answer = "请求超时，请稍后重试"
    except LLMServiceError:
        answer = "服务暂时不可用，请稍后重试"
    return ChatResponse(answer=answer, trace_id=str(uuid.uuid4()))
```

- 新增 `safe_chat()` 函数，作为业务层封装
- 通过 `try/except` 捕获自定义异常，返回降级文案，保证接口不会直接报错

### 3. 修改 `services/llm_client.py` —— 异常转换 + 重试

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((LLMTimeoutError, LLMServiceError))
)
def chat_completion(system_prompt: str, user_message: str):
    try:
        response = client.chat.completions.create(...)
    except Timeout:
        raise LLMTimeoutError("LLM 调用超时")
    except APIError:
        raise LLMServiceError("LLM 服务错误")
    return response.choices[0].message.content
```

- 在函数内部捕获 OpenAI SDK 的原始异常（`Timeout`、`APIError`），转换为自定义异常抛出
- `@retry` 装饰器根据自定义异常类型决定是否重试

### 4. 修改 `routers/chat.py` —— 路由层简化

```python
@router.post("/chat")
async def get_chat(chatRequest: ChatRequest):
    return chat_service.safe_chat(chatRequest.message)
```

- 路由层不再直接调用 `llm_client`，改为调用 `chat_service.safe_chat()`
- 路由层只负责接收请求和返回响应，业务逻辑下沉到 service 层

---

## 知识点总结

### 1. Python 类的继承语法

```python
class 子类名(父类名):
    pass
```

括号里的就是父类，例如 `class LLMTimeoutError(Exception)` 表示继承自 `Exception`。

### 2. 函数返回值类型注解 `-> Type`

```python
def safe_chat(message: str) -> ChatResponse:
```

- `-> ChatResponse` 表示函数返回 `ChatResponse` 类型
- 仅做提示，Python 运行时不强制检查
- 好处：IDE 智能补全、代码可读性、配合 mypy 做静态类型检查

### 3. tenacity 重试库 `@retry` 装饰器

```python
@retry(
    stop=stop_after_attempt(3),           # 最多重试 3 次
    wait=wait_exponential(min=1, max=10), # 指数退避等待（1s, 2s, 4s...最大10s）
    retry=retry_if_exception_type((...))  # 只在特定异常时重试
)
```

- `@retry` 包在函数外层，像一个"门卫"，只看函数**最终抛出的异常**来决定是否重试
- 函数内部的 `try/except` 将原始异常转换为自定义异常后抛出，`@retry` 看到的是转换后的异常

### 5. 分层架构设计

```
routers/chat.py        → 路由层：接收请求、返回响应
services/chat_service.py → 业务层：降级兜底、业务逻辑
services/llm_client.py   → 基础设施层：API 调用、重试、异常转换
core/exceptions.py       → 公共层：自定义异常定义
```

- **底层负责重试**（llm_client 的 @retry）
- **上层负责兜底**（chat_service 的 try/except 降级文案）
- 各层职责清晰，互不依赖具体实现
