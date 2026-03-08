import contextvars
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from core.logger import logger

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
