"""
指标收集中间件
收集API请求的性能指标
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from prometheus_client import Counter, Histogram, Gauge
import structlog

logger = structlog.get_logger()

# Prometheus指标定义
REQUEST_COUNT = Counter(
    "http_requests_total",
    "总HTTP请求数",
    ["method", "endpoint", "status_code", "project_id"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP请求持续时间",
    ["method", "endpoint", "project_id"]
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "当前活跃请求数",
    ["project_id"]
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """指标收集中间件"""
    
    def __init__(self, app, project_id: str = "unknown"):
        super().__init__(app)
        self.project_id = project_id
    
    async def dispatch(self, request: Request, call_next):
        # 记录开始时间
        start_time = time.time()
        
        # 增加活跃请求计数
        ACTIVE_REQUESTS.labels(project_id=self.project_id).inc()
        
        try:
            # 调用下一个中间件或路由处理器
            response: Response = await call_next(request)
            
            # 记录指标
            duration = time.time() - start_time
            method = request.method
            endpoint = self._get_endpoint_name(request)
            status_code = response.status_code
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                project_id=self.project_id
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint,
                project_id=self.project_id
            ).observe(duration)
            
            # 记录慢请求日志
            if duration > 2.0:  # 超过2秒的请求
                logger.warning(
                    "慢请求检测",
                    method=method,
                    path=str(request.url),
                    duration=duration,
                    status_code=status_code,
                    request_id=getattr(request.state, "request_id", None)
                )
            
            return response
            
        except Exception as e:
            # 记录错误指标
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=self._get_endpoint_name(request),
                status_code=500,
                project_id=self.project_id
            ).inc()
            
            logger.error(
                "请求处理异常",
                method=request.method,
                path=str(request.url),
                error=str(e),
                request_id=getattr(request.state, "request_id", None),
                exc_info=True
            )
            raise
        
        finally:
            # 减少活跃请求计数
            ACTIVE_REQUESTS.labels(project_id=self.project_id).dec()
    
    def _get_endpoint_name(self, request: Request) -> str:
        """获取端点名称"""
        # 尝试获取路由名称
        if hasattr(request.scope, "route") and hasattr(request.scope["route"], "name"):
            return request.scope["route"].name
        
        # 简化路径（替换路径参数）
        path = request.url.path
        
        # 常见的路径参数替换
        import re
        path = re.sub(r'/\d+', '/{id}', path)
        path = re.sub(r'/[a-f0-9-]{36}', '/{uuid}', path)  # UUID
        
        return path