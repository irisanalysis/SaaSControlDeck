"""
AI分析服务 - 主应用入口点
负责AI模型调用、分布式计算和结果分析
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
import ray

# 添加共享模块到Python路径
current_dir = Path(__file__).parent.parent.parent
shared_dir = current_dir / "shared"
sys.path.insert(0, str(shared_dir))

from shared.config import get_settings
from shared.logging import setup_logging
from shared.database import Database
from shared.redis_client import RedisClient
from shared.middleware.request_id import RequestIDMiddleware
from shared.middleware.metrics import MetricsMiddleware

from app.routers import ai_analysis, model_management, distributed_tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()
    logger = structlog.get_logger()
    
    logger.info("Starting AI Service", project_id=settings.PROJECT_ID)
    
    # 初始化连接
    await Database.connect(settings.DATABASE_URL)
    await RedisClient.connect(settings.REDIS_URL)
    
    # 初始化Ray集群
    try:
        if not ray.is_initialized():
            ray.init(
                address=f"{settings.RAY_HEAD_NODE_HOST}:{settings.RAY_HEAD_NODE_PORT}",
                _redis_password=settings.RAY_REDIS_PASSWORD or None,
            )
        logger.info("Ray cluster connected")
    except Exception as e:
        logger.warning("Ray cluster connection failed", error=str(e))
        # 使用本地模式
        ray.init()
        logger.info("Ray initialized in local mode")
    
    logger.info("AI Service started successfully")
    
    yield
    
    logger.info("Shutting down AI Service")
    ray.shutdown()
    await Database.disconnect()
    await RedisClient.disconnect()


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    
    app = FastAPI(
        title=f"{settings.PROJECT_NAME} - AI Service",
        description="AI分析和分布式计算服务",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # 添加中间件
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(MetricsMiddleware)
    
    if settings.DEBUG:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # 注册路由
    app.include_router(ai_analysis.router, prefix="/analysis", tags=["AI分析"])
    app.include_router(model_management.router, prefix="/models", tags=["模型管理"])
    app.include_router(distributed_tasks.router, prefix="/tasks", tags=["分布式任务"])
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy", 
            "service": "ai-service",
            "ray_initialized": ray.is_initialized()
        }
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.AI_SERVICE_PORT,
        reload=settings.DEBUG,
    )