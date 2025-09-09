"""
请求ID中间件
为每个请求生成唯一ID，用于日志跟踪
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求ID中间件"""
    
    async def dispatch(self, request: Request, call_next):
        # 生成或获取请求ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # 将请求ID存储在request state中
        request.state.request_id = request_id
        
        # 调用下一个中间件或路由处理器
        response: Response = await call_next(request)
        
        # 在响应头中添加请求ID
        response.headers["X-Request-ID"] = request_id
        
        return response