class LLMTimeoutError(Exception):
    """LLM 调用超时异常"""
    pass


class LLMServiceError(Exception):
    """LLM 服务通用错误异常"""
    pass
