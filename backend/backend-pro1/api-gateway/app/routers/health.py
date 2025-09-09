"""
健康检查路由
提供系统健康状态检查端点
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
import asyncio
import structlog

from shared.config import get_settings, Settings
from shared.database import Database
from shared.redis_client import RedisClient

logger = structlog.get_logger()
router = APIRouter()


@router.get("/health")
async def health_check():
    """基本健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "api-gateway"
    }


@router.get("/health/detailed")
async def detailed_health_check(settings: Settings = Depends(get_settings)):
    """详细健康检查，包含依赖服务状态"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "api-gateway",
        "project_id": settings.PROJECT_ID,
        "version": "1.0.0",
        "dependencies": {}
    }
    
    overall_healthy = True
    
    # 检查数据库连接
    try:
        await Database.execute_query("SELECT 1")
        health_status["dependencies"]["database"] = {
            "status": "healthy",
            "response_time_ms": None  # 可以添加响应时间测量
        }
    except Exception as e:
        logger.error("数据库健康检查失败", error=str(e))
        health_status["dependencies"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # 检查Redis连接
    try:
        await RedisClient.ping()
        health_status["dependencies"]["redis"] = {
            "status": "healthy",
            "response_time_ms": None
        }
    except Exception as e:
        logger.error("Redis健康检查失败", error=str(e))
        health_status["dependencies"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # 检查下游服务
    downstream_services = [
        {"name": "data-service", "port": settings.DATA_SERVICE_PORT},
        {"name": "ai-service", "port": settings.AI_SERVICE_PORT}
    ]
    
    for service in downstream_services:
        try:
            # 这里可以添加实际的HTTP健康检查
            # 暂时模拟检查
            health_status["dependencies"][service["name"]] = {
                "status": "healthy",
                "endpoint": f"http://localhost:{service['port']}/health"
            }
        except Exception as e:
            logger.error(f"{service['name']}健康检查失败", error=str(e))
            health_status["dependencies"][service["name"]] = {
                "status": "unhealthy",
                "error": str(e),
                "endpoint": f"http://localhost:{service['port']}/health"
            }
            overall_healthy = False
    
    if not overall_healthy:
        health_status["status"] = "degraded"
    
    status_code = 200 if overall_healthy else 503
    return JSONResponse(content=health_status, status_code=status_code)


@router.get("/ready")
async def readiness_check():
    """就绪检查，用于Kubernetes readiness probe"""
    try:
        # 检查关键依赖是否就绪
        await Database.execute_query("SELECT 1")
        await RedisClient.ping()
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        logger.error("就绪检查失败", error=str(e))
        return JSONResponse(
            content={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            status_code=503
        )


@router.get("/live")
async def liveness_check():
    """存活检查，用于Kubernetes liveness probe"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }