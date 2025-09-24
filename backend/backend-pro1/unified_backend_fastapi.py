#!/usr/bin/env python3
"""
SaaS Control Deck - 专业统一后端服务 (简化版)
基于FastAPI的完整后端实现，支持认证、文件上传、数据管理
解决页面刷新后的"Internal Server Error"问题
专门设计用于Firebase Studio环境，最小化外部依赖
"""

import os
import sys
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import hashlib
import base64
import hmac
import json

from fastapi import FastAPI, Depends, HTTPException, status, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

# 应用配置
class Settings:
    SECRET_KEY = "your-super-secret-key-32-chars-minimum-saascontrol-dev-2024"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    DEBUG = True
    PORT = 8000

settings = Settings()

# HTTP Bearer安全方案
security = HTTPBearer()

# 内存存储
uploaded_files: Dict[str, Any] = {}
data_sources: Dict[str, Any] = {}
active_tokens: Dict[str, Any] = {}

# Pydantic模型
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    email_verified: bool
    created_at: str
    avatar_url: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class DataSourceCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    type: str = "file"
    file_id: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    port: int
    features: List[str]
    timestamp: str
    uptime: float

# 密码和令牌工具函数
def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    salt = settings.SECRET_KEY[:16]
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return hashed.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    salt = settings.SECRET_KEY[:16]
    expected_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode(), salt.encode(), 100000)
    stored_hash = bytes.fromhex(hashed_password)
    return hmac.compare_digest(expected_hash, stored_hash)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    email = data.get('sub')
    if expires_delta:
        expire_time = datetime.utcnow() + expires_delta
    else:
        expire_time = datetime.utcnow() + timedelta(minutes=15)

    token_data = f"{email}:{expire_time.timestamp()}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        token_data.encode(),
        hashlib.sha256
    ).hexdigest()

    token = base64.b64encode(f"{token_data}:{signature}".encode()).decode()
    return token

def create_refresh_token(data: dict):
    """创建刷新令牌"""
    email = data.get('sub')
    expire_time = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    token_data = f"{email}:refresh:{expire_time.timestamp()}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        token_data.encode(),
        hashlib.sha256
    ).hexdigest()

    token = base64.b64encode(f"{token_data}:{signature}".encode()).decode()
    return token

def verify_token(token: str):
    """验证令牌"""
    try:
        decoded = base64.b64decode(token.encode()).decode()
        parts = decoded.split(':')

        if len(parts) >= 3:
            email = parts[0]
            expire_timestamp = float(parts[1])
            provided_signature = parts[2]

            # 验证签名
            token_data = f"{email}:{expire_timestamp}"
            expected_signature = hmac.new(
                settings.SECRET_KEY.encode(),
                token_data.encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(provided_signature, expected_signature):
                return None

            # 验证过期时间
            if datetime.utcnow().timestamp() > expire_timestamp:
                return None

            return {"sub": email}
    except Exception:
        pass

    return None

# 测试用户数据
TEST_USERS_DB = {
    "test@saascontrol.dev": {
        "id": 1,
        "email": "test@saascontrol.dev",
        "password_hash": get_password_hash("TestPass123"),
        "full_name": "测试 用户",
        "first_name": "测试",
        "last_name": "用户",
        "is_active": True,
        "email_verified": True,
        "created_at": datetime.now().isoformat(),
        "avatar_url": None
    }
}

# 认证依赖
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未授权",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        print(f"Token验证失败: {token[:20]}...")
        raise credentials_exception

    email = payload.get("sub")
    if email not in TEST_USERS_DB:
        print(f"用户不存在: {email}")
        raise credentials_exception

    user_data = TEST_USERS_DB[email]
    print(f"用户认证成功: {email}")
    return UserResponse(**user_data)

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print(f"启动专业统一后端服务，端口: {settings.PORT}")
    print("使用内存存储模式，支持SSR和完整错误处理")

    yield

    print("专业统一后端服务已停止")

# 创建FastAPI应用
app = FastAPI(
    title="SaaS Control Deck - 专业统一后端服务",
    description="FastAPI后端，支持认证、文件上传、数据管理，解决SSR问题",
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9000", "*"] if settings.DEBUG else ["http://localhost:9000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    print(f"未处理的异常: {request.method} {request.url} - {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "error": "服务器遇到了一个内部错误，请稍后重试",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )

# 健康检查端点
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    import time
    uptime = time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0

    return HealthResponse(
        status="healthy",
        service="unified-backend-service",
        port=settings.PORT,
        features=["fastapi", "authentication", "file-upload", "data-management", "ssr-support"],
        timestamp=datetime.now().isoformat(),
        uptime=uptime
    )

# 认证端点
@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """用户登录"""
    print(f"收到登录请求: {request.email}")

    # 验证用户凭据
    user_data = TEST_USERS_DB.get(request.email)
    if not user_data or not verify_password(request.password, user_data["password_hash"]):
        print(f"登录失败：凭据错误 - {request.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )

    # 创建令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data["email"]},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user_data["email"]})

    # 存储活跃令牌
    active_tokens[access_token] = {
        "user_email": user_data["email"],
        "expires": datetime.utcnow() + access_token_expires
    }

    user_response = UserResponse(**{k: v for k, v in user_data.items() if k != "password_hash"})

    print(f"登录成功: {request.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_response
    )

@app.post("/auth/register")
async def register(request: RegisterRequest):
    """用户注册"""
    print(f"收到注册请求: {request.email}")

    # 检查用户是否已存在
    if request.email in TEST_USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户已存在"
        )

    # 创建新用户
    user_id = len(TEST_USERS_DB) + 1
    password_hash = get_password_hash(request.password)

    new_user = {
        "id": user_id,
        "email": request.email,
        "password_hash": password_hash,
        "full_name": f"{request.first_name} {request.last_name}",
        "first_name": request.first_name,
        "last_name": request.last_name,
        "is_active": True,
        "email_verified": True,
        "created_at": datetime.now().isoformat(),
        "avatar_url": None
    }

    TEST_USERS_DB[request.email] = new_user

    user_response = UserResponse(**{k: v for k, v in new_user.items() if k != "password_hash"})

    print(f"注册成功: {request.email}")

    return {
        "success": True,
        "message": "注册成功",
        "user": user_response
    }

@app.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """刷新访问令牌"""
    print("收到令牌刷新请求")

    payload = verify_token(request.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )

    email = payload.get("sub")
    user_data = TEST_USERS_DB.get(email)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    # 创建新令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": email},
        expires_delta=access_token_expires
    )
    new_refresh_token = create_refresh_token(data={"sub": email})

    user_response = UserResponse(**{k: v for k, v in user_data.items() if k != "password_hash"})

    print(f"令牌刷新成功: {email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_response
    )

@app.post("/auth/logout")
async def logout(current_user: UserResponse = Depends(get_current_user)):
    """用户登出"""
    print(f"用户登出: {current_user.email}")

    return {"success": True, "message": "登出成功"}

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """获取当前用户信息"""
    print(f"获取用户信息: {current_user.email}")
    return current_user

# 文件上传端点
@app.post("/upload/file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """文件上传"""
    print(f"收到文件上传请求: {file.filename} - 用户: {current_user.email}")

    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 生成文件ID
    file_id = f"file_{uuid.uuid4().hex[:16]}"

    # 读取文件内容
    content = await file.read()

    # 存储文件信息
    file_info = {
        "id": file_id,
        "filename": file.filename,
        "size": len(content),
        "content_type": file.content_type,
        "uploaded_at": datetime.now().isoformat(),
        "uploaded_by": current_user.email,
        "content": content  # 在实际应用中应该保存到文件系统或对象存储
    }

    uploaded_files[file_id] = file_info

    # 返回文件信息（不包含内容）
    response_data = {k: v for k, v in file_info.items() if k != "content"}

    print(f"文件上传成功: {file_id} - {file.filename}")

    return {
        "success": True,
        "message": "文件上传成功",
        "file": response_data
    }

# 数据管理端点
@app.post("/data/sources")
async def create_data_source(
    request: DataSourceCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """创建数据源"""
    print(f"创建数据源: {request.name} - 用户: {current_user.email}")

    source_id = f"ds_{uuid.uuid4().hex[:16]}"

    data_source = {
        "id": source_id,
        "name": request.name,
        "description": request.description,
        "type": request.type,
        "file_id": request.file_id,
        "created_at": datetime.now().isoformat(),
        "created_by": current_user.email,
        "status": "active",
        "row_count": 0,
        "column_count": 0
    }

    # 如果关联了文件，添加文件信息
    if request.file_id and request.file_id in uploaded_files:
        file_info = uploaded_files[request.file_id]
        data_source["file_info"] = {k: v for k, v in file_info.items() if k != "content"}
        # 模拟解析文件内容
        data_source["row_count"] = 100
        data_source["column_count"] = 5

    data_sources[source_id] = data_source

    print(f"数据源创建成功: {source_id} - {request.name}")

    return data_source

@app.get("/data/sources")
async def get_data_sources(current_user: UserResponse = Depends(get_current_user)):
    """获取数据源列表"""
    print(f"获取数据源列表 - 用户: {current_user.email}")

    user_sources = [
        source for source in data_sources.values()
        if source["created_by"] == current_user.email
    ]

    return {
        "data_sources": user_sources,
        "total": len(user_sources)
    }

@app.delete("/data/sources/{source_id}")
async def delete_data_source(
    source_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """删除数据源"""
    print(f"删除数据源: {source_id} - 用户: {current_user.email}")

    if source_id not in data_sources:
        raise HTTPException(status_code=404, detail="数据源不存在")

    source = data_sources[source_id]
    if source["created_by"] != current_user.email:
        raise HTTPException(status_code=403, detail="无权限删除此数据源")

    del data_sources[source_id]

    print(f"数据源删除成功: {source_id}")

    return {"message": "数据源删除成功"}

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    import time
    app.state.start_time = time.time()
    print(f"专业统一后端服务启动完成 - 端口: {settings.PORT}")
    print("功能: FastAPI + JWT认证 + CORS支持 + SSR兼容 + 全局异常处理")

if __name__ == "__main__":
    import uvicorn

    print(f"启动专业统一后端服务 - 端口: {settings.PORT}")

    uvicorn.run(
        "unified_backend_fastapi:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )