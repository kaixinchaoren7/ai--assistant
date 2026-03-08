# Day 3 学习记录

## 今日改动概览

### 1. 新增 `core/logger.py` —— JSON 格式日志

```python
class CustomJsonFormatter(JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = log_record.pop("asctime", self.formatTime(record))
        log_record["level"] = log_record.pop("levelname", record.levelname).upper()
        if "trace_id" not in log_record:
            log_record["trace_id"] = None
        if "duration_ms" not in log_record:
            log_record["duration_ms"] = None

def get_logger(name: str = "ai-agent") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = CustomJsonFormatter(fmt="%(asctime)s %(levelname)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = get_logger()
```

- 自定义 `CustomJsonFormatter`，继承 `python-json-logger` 的 `JsonFormatter`，统一日志输出为 JSON 格式
- 每条日志固定包含 5 个字段：`timestamp`、`level`、`message`、`trace_id`、`duration_ms`
- `get_logger()` 工厂函数创建 logger，内部通过 `if not logger.handlers` 防止重复添加 handler
- 模块底部 `logger = get_logger()` 预创建实例，其他文件直接 `from core.logger import logger` 即可使用

### 2. 新增 `middleware/trace_id.py` —— 请求追踪中间件

```python
trace_id_var = contextvars.ContextVar("trace_id", default=None)

class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = str(uuid.uuid4())
        trace_id_var.set(trace_id)
        method = request.method
        path = request.url.path
        logger.info(f"[START] {method} {path}", extra={"trace_id": trace_id})
        start_time = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"[END] {method} {path}", extra={"trace_id": trace_id, "duration_ms": duration_ms})
        response.headers["X-Trace-Id"] = trace_id
        return response
```

- 每次请求生成唯一 `trace_id`（uuid4），存入 `contextvars.ContextVar`，方便全链路追踪
- 请求开始时记录 `[START] GET /chat`，请求结束时记录 `[END] GET /chat` 及耗时 `duration_ms`
- 响应 header 中添加 `X-Trace-Id`，方便前端或调用方排查问题

### 3. 修改 `main.py` —— 注册中间件

```python
from middleware.trace_id import TraceIdMiddleware

app = FastAPI()
app.add_middleware(TraceIdMiddleware)
```

- 通过 `app.add_middleware()` 注册中间件，所有请求都会经过 `TraceIdMiddleware` 处理

---

## 知识点总结

### 1. Python `logging` 模块核心概念

```
Logger（记录器）  →  Handler（处理器）  →  Formatter（格式化器）
  负责产生日志       负责日志输出到哪里       负责日志长什么样
```

- `logging.getLogger(name)`：相同 name 返回同一个 logger 实例（单例机制）
- `StreamHandler(sys.stdout)`：日志输出到标准输出（控制台），容器部署中方便日志采集
- `Formatter`：控制日志格式，这里用 `JsonFormatter` 输出 JSON，方便 ELK 等系统解析

### 2. `contextvars.ContextVar` —— 协程安全的上下文变量

```python
trace_id_var = contextvars.ContextVar("trace_id", default=None)

# 存值
trace_id_var.set("abc-123")

# 取值（在同一请求的任意位置）
trace_id_var.get()  # → "abc-123"
```

- 类似 Java 的 `ThreadLocal`，但适用于 Python 异步协程
- 每个请求有独立的上下文，不同请求之间互不干扰
- 必须在**模块级别创建一次**，不能每次请求都 `ContextVar("trace_id")`，否则会丢失引用

### 3. `BaseHTTPMiddleware` —— 中间件基类（模板方法模式）

```python
class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 请求前的逻辑
        response = await call_next(request)  # 交给下一层处理
        # 请求后的逻辑
        return response
```

- 来自 Starlette（FastAPI 底层框架），封装了 ASGI 协议细节
- 子类只需重写 `dispatch` 方法，专注业务逻辑
- `call_next(request)` 调用下一个中间件或路由，拿到 response 后可以做后处理
- 好处：中间件不依赖 `app` 对象，在 `main.py` 中通过 `app.add_middleware()` 注册，保持单向依赖

### 4. 中间件的执行流程

```
请求进入
  → TraceIdMiddleware.dispatch()
    → 生成 trace_id，记录 [START]
    → call_next(request)
      → 路由处理（如 /chat）
    ← 拿到 response
    → 记录 [END] + duration_ms
    → 添加 X-Trace-Id header
  ← 返回 response
响应返回
```

中间件像"洋葱"一样包裹在路由外面，请求进来时从外到内，响应出去时从内到外。

### 5. `time.time()` 计算耗时

```python
start_time = time.time()                                    # 记录开始时间（秒）
response = await call_next(request)                         # 执行请求
duration_ms = round((time.time() - start_time) * 1000, 2)  # 转为毫秒，保留2位小数
```

- `time.time()` 返回当前时间戳（浮点数，单位秒）
- 两次调用的差值就是耗时，乘以 1000 转为毫秒
