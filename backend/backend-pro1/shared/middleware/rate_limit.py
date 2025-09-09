"""
限流中间件
基于Redis的分布式限流
"""

import time
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import structlog

logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(
        self,
        app,
        redis_url: str,
        default_rate_limit: int = 100,  # 每分钟请求数
        window_size: int = 60,  # 时间窗口（秒）
    ):
        super().__init__(app)
        self.redis_url = redis_url
        self.default_rate_limit = default_rate_limit
        self.window_size = window_size
        self._redis_client = None
    
    async def _get_redis_client(self):
        """获取Redis客户端"""
        if self._redis_client is None:
            from ..redis_client import RedisClient
            # 使用全局Redis客户端
            self._redis_client = RedisClient._client
        return self._redis_client
    
    async def dispatch(self, request: Request, call_next):
        # 获取客户端标识
        client_id = self._get_client_id(request)
        
        # 检查限流
        is_allowed, remaining_requests, reset_time = await self._check_rate_limit(
            client_id, request
        )
        
        if not is_allowed:
            logger.warning(
                "请求被限流",
                client_id=client_id,
                path=str(request.url),
                method=request.method,
                request_id=getattr(request.state, "request_id", None)
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "请求过于频繁，请稍后重试"
                    },
                    "rate_limit": {
                        "remaining": 0,
                        "reset_time": reset_time
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(self.default_rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(int(reset_time - time.time()))
                }
            )
        
        # 处理请求
        response = await call_next(request)
        
        # 在响应头中添加限流信息
        response.headers["X-RateLimit-Limit"] = str(self.default_rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining_requests)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """获取客户端标识"""
        # 优先使用认证用户ID
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        # 使用IP地址
        client_ip = request.client.host if request.client else "unknown"
        
        # 检查是否有代理IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            client_ip = real_ip
        
        return f"ip:{client_ip}"
    
    async def _check_rate_limit(
        self, 
        client_id: str, 
        request: Request
    ) -> tuple[bool, int, int]:
        """检查限流状态"""
        try:
            redis_client = await self._get_redis_client()
            if not redis_client:
                # Redis不可用时跳过限流
                logger.warning("Redis不可用，跳过限流检查")
                return True, self.default_rate_limit, int(time.time()) + self.window_size
            
            current_time = int(time.time())
            window_start = current_time - (current_time % self.window_size)
            
            # 限流键
            rate_limit_key = f"rate_limit:{client_id}:{window_start}"
            
            # 获取当前请求计数
            current_count = await redis_client.get(rate_limit_key, deserialize_json=False)
            current_count = int(current_count) if current_count else 0
            
            # 检查是否超过限制
            if current_count >= self.default_rate_limit:
                reset_time = window_start + self.window_size
                return False, 0, reset_time
            
            # 增加计数
            pipe = redis_client.pipeline()
            pipe.incr(rate_limit_key)
            pipe.expire(rate_limit_key, self.window_size)
            await pipe.execute()
            
            remaining_requests = max(0, self.default_rate_limit - current_count - 1)
            reset_time = window_start + self.window_size
            
            return True, remaining_requests, reset_time
            
        except Exception as e:
            logger.error(
                "限流检查失败，允许请求通过",
                client_id=client_id,
                error=str(e),
                exc_info=True
            )
            # 发生错误时允许请求通过
            return True, self.default_rate_limit, int(time.time()) + self.window_size