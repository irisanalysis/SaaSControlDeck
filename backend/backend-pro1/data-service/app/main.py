"""
数据处理服务 - 主应用入口点
负责数据上传、预处理、存储和管理
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

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

from app.routers import data_upload, data_management, data_processing


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()
    logger = structlog.get_logger()
    
    logger.info("Starting Data Service", project_id=settings.PROJECT_ID)
    
    # 初始化连接
    await Database.connect(settings.DATABASE_URL)
    await RedisClient.connect(settings.REDIS_URL)
    logger.info("Data Service started successfully")
    
    yield
    
    logger.info("Shutting down Data Service")
    await Database.disconnect()
    await RedisClient.disconnect()


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    
    app = FastAPI(
        title=f"{settings.PROJECT_NAME} - Data Service",
        description="数据处理和管理服务",
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
    app.include_router(data_upload.router, prefix="/upload", tags=["数据上传"])
    app.include_router(data_management.router, prefix="/manage", tags=["数据管理"])
    app.include_router(data_processing.router, prefix="/process", tags=["数据处理"])
    
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "data-service"}
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.DATA_SERVICE_PORT,
        reload=settings.DEBUG,
    )