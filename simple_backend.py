#!/usr/bin/env python3
"""
# 简单统一后端服务
# 文件位置: /home/user/studio/simple_backend.py
# 功能: 为SaaS Control Deck提供统一的FastAPI后端服务
# 原因: 解决复杂微服务架构的模块导入和启动问题，提供快速开发环境
# 相关文件: frontend/src/app/api/, backend/backend-pro1/.env, package.json
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# 加载环境变量
backend_env = Path(__file__).parent / "backend" / "backend-pro1" / ".env"
if backend_env.exists():
    load_dotenv(backend_env)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="SaaS Control Deck - 统一后端服务",
    description="AI数据分析平台统一后端API",
    version="1.0.0"
)

# CORS配置 - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9000", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全认证
security = HTTPBearer()

# Pydantic模型
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    created_at: str

class DataUploadResponse(BaseModel):
    success: bool
    filename: str
    size: int
    message: str

class AnalysisRequest(BaseModel):
    data_source: str
    analysis_type: str
    parameters: Dict[str, Any] = {}

class AnalysisResponse(BaseModel):
    task_id: str
    status: str
    created_at: str

# 模拟数据存储
users_db = []
data_files = []
analysis_tasks = []

# 辅助函数
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证JWT令牌 - 简化版本"""
    token = credentials.credentials
    # 这里应该验证JWT token，现在简单返回示例用户
    if token == "demo-token":
        return {"user_id": 1, "username": "demo_user"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials"
    )

# 路由定义

@app.get("/", response_model=Dict[str, str])
async def root():
    """根路径"""
    return {
        "message": "SaaS Control Deck 统一后端服务",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        services={
            "database": "connected",
            "redis": "connected",
            "api": "running"
        }
    )

@app.get("/api/ready")
async def ready_check():
    """就绪检查 - 供前端使用"""
    return {"status": "ready", "timestamp": datetime.now().isoformat()}

# 认证相关API
@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """用户登录"""
    logger.info(f"用户登录尝试: {user_data.username}")

    # 简化验证 - 演示用
    if user_data.username == "admin" and user_data.password == "password":
        return TokenResponse(
            access_token="demo-token",
            token_type="bearer",
            expires_in=3600
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="用户名或密码错误"
    )

@app.post("/api/v1/auth/register", response_model=Dict[str, str])
async def register(user_data: UserRegister):
    """用户注册"""
    logger.info(f"用户注册: {user_data.username}")

    # 检查用户是否已存在
    for user in users_db:
        if user["username"] == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

    # 添加新用户
    new_user = {
        "id": len(users_db) + 1,
        "username": user_data.username,
        "email": user_data.email,
        "created_at": datetime.now().isoformat()
    }
    users_db.append(new_user)

    return {"message": "用户注册成功", "user_id": str(new_user["id"])}

@app.get("/api/v1/auth/me", response_model=UserInfo)
async def get_current_user(current_user: dict = Depends(verify_token)):
    """获取当前用户信息"""
    return UserInfo(
        id=current_user["user_id"],
        username=current_user["username"],
        email="demo@example.com",
        created_at=datetime.now().isoformat()
    )

# 数据管理API
@app.post("/api/v1/data/upload", response_model=DataUploadResponse)
async def upload_data(file: UploadFile = File(...), current_user: dict = Depends(verify_token)):
    """数据文件上传"""
    logger.info(f"文件上传: {file.filename}")

    try:
        # 读取文件内容 (简化处理)
        content = await file.read()
        file_size = len(content)

        # 保存文件信息
        file_info = {
            "id": len(data_files) + 1,
            "filename": file.filename,
            "size": file_size,
            "uploaded_by": current_user["user_id"],
            "uploaded_at": datetime.now().isoformat()
        }
        data_files.append(file_info)

        return DataUploadResponse(
            success=True,
            filename=file.filename,
            size=file_size,
            message="文件上传成功"
        )

    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )

@app.get("/api/v1/data/files")
async def list_data_files(current_user: dict = Depends(verify_token)):
    """获取数据文件列表"""
    return {
        "files": data_files,
        "total": len(data_files)
    }

# AI分析API
@app.post("/api/v1/analysis/start", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest, current_user: dict = Depends(verify_token)):
    """启动AI分析任务"""
    logger.info(f"启动分析任务: {request.analysis_type}")

    task = {
        "task_id": f"task_{len(analysis_tasks) + 1}",
        "data_source": request.data_source,
        "analysis_type": request.analysis_type,
        "parameters": request.parameters,
        "status": "pending",
        "created_by": current_user["user_id"],
        "created_at": datetime.now().isoformat()
    }
    analysis_tasks.append(task)

    return AnalysisResponse(
        task_id=task["task_id"],
        status="pending",
        created_at=task["created_at"]
    )

@app.get("/api/v1/analysis/tasks")
async def list_analysis_tasks(current_user: dict = Depends(verify_token)):
    """获取分析任务列表"""
    return {
        "tasks": analysis_tasks,
        "total": len(analysis_tasks)
    }

@app.get("/api/v1/analysis/task/{task_id}")
async def get_analysis_task(task_id: str, current_user: dict = Depends(verify_token)):
    """获取特定分析任务详情"""
    for task in analysis_tasks:
        if task["task_id"] == task_id:
            return task

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="任务不存在"
    )

# 项目管理API
@app.get("/api/v1/projects")
async def list_projects(current_user: dict = Depends(verify_token)):
    """获取项目列表"""
    return {
        "projects": [
            {
                "id": 1,
                "name": "Demo Project",
                "description": "演示项目",
                "created_at": datetime.now().isoformat(),
                "owner": current_user["username"]
            }
        ],
        "total": 1
    }

if __name__ == "__main__":
    # 获取端口配置
    port = int(os.getenv("API_GATEWAY_PORT", 8000))

    logger.info(f"启动统一后端服务，端口: {port}")
    logger.info("API文档: http://localhost:{}/docs".format(port))

    uvicorn.run(
        "simple_backend:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )