"""
API Gateway - 主应用入口点
负责路由、认证、限流和服务聚合
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# 添加共享模块到Python路径
current_dir = Path(__file__).parent.parent.parent
shared_dir = current_dir / "shared"
sys.path.insert(0, str(shared_dir))

from shared.config import get_settings
from shared.logging import setup_logging
from shared.database import Database
from shared.redis_client import RedisClient
from shared.middleware.rate_limit import RateLimitMiddleware
from shared.middleware.request_id import RequestIDMiddleware
from shared.middleware.metrics import MetricsMiddleware

from app.routers import auth, users, projects, analysis, health
from app.core.exceptions import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()
    logger = structlog.get_logger()
    
    # 启动时初始化
    logger.info("Starting API Gateway", project_id=settings.PROJECT_ID)
    
    # 初始化数据库连接
    await Database.connect(settings.DATABASE_URL)
    logger.info("Database connected")
    
    # 初始化Redis连接
    await RedisClient.connect(settings.REDIS_URL)
    logger.info("Redis connected")
    
    # 应用运行期间
    yield
    
    # 关闭时清理
    logger.info("Shutting down API Gateway")
    await Database.disconnect()
    await RedisClient.disconnect()


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    settings = get_settings()
    
    # 设置日志
    setup_logging(settings.LOG_LEVEL)
    logger = structlog.get_logger()
    
    # 初始化Sentry（生产环境）
    if settings.SENTRY_DSN and not settings.DEBUG:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[FastApiIntegration(auto_enable=True)],
            traces_sample_rate=0.1,
            environment=settings.ENVIRONMENT,
        )
    
    # 创建FastAPI应用
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="AI数据分析平台API网关",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # 添加中间件
    setup_middleware(app, settings)
    
    # 注册路由
    setup_routers(app)
    
    # 注册异常处理器
    setup_exception_handlers(app)
    
    logger.info(
        "API Gateway created",
        project_id=settings.PROJECT_ID,
        port=settings.API_GATEWAY_PORT,
        debug=settings.DEBUG,
    )
    
    return app


def setup_middleware(app: FastAPI, settings):
    """设置中间件"""
    # 请求ID中间件（最先添加）
    app.add_middleware(RequestIDMiddleware)
    
    # 指标收集中间件
    app.add_middleware(MetricsMiddleware)
    
    # 限流中间件
    app.add_middleware(RateLimitMiddleware, redis_url=settings.REDIS_URL)
    
    # CORS中间件
    if settings.DEBUG:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://yourplatform.com", "https://app.yourplatform.com"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        )
    
    # 受信任主机中间件（生产环境）
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["yourplatform.com", "*.yourplatform.com"],
        )


def setup_routers(app: FastAPI):
    """设置路由"""
    # API版本前缀
    api_v1_prefix = "/api/v1"
    
    # 健康检查和指标（无前缀）
    app.include_router(health.router, tags=["健康检查"])
    
    # 认证路由
    app.include_router(
        auth.router,
        prefix=f"{api_v1_prefix}/auth",
        tags=["认证"]
    )
    
    # 用户管理路由
    app.include_router(
        users.router,
        prefix=f"{api_v1_prefix}/users",
        tags=["用户管理"]
    )
    
    # 项目管理路由
    app.include_router(
        projects.router,
        prefix=f"{api_v1_prefix}/projects",
        tags=["项目管理"]
    )
    
    # 数据分析路由
    app.include_router(
        analysis.router,
        prefix=f"{api_v1_prefix}/analysis",
        tags=["数据分析"]
    )


# Prometheus指标端点
@app.get("/metrics")
async def get_metrics():
    """获取Prometheus指标"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.API_GATEWAY_PORT,
        reload=settings.DEBUG,
        access_log=settings.DEBUG,
    )