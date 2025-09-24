#!/usr/bin/env python3
"""
迁移示例：从自定义HTTP服务器到FastAPI
展示核心功能的对等迁移
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import jwt
import uuid

# 创建FastAPI应用
app = FastAPI(
    title="SaaS Control Deck - 迁移版本",
    description="从自定义HTTP服务器迁移到FastAPI",
    version="1.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT配置
SECRET_KEY = "your-super-secret-key-32-chars-minimum"
ALGORITHM = "HS256"
security = HTTPBearer()

# 测试用户数据 (迁移自原始代码)
TEST_USER = {
    "id": 1,
    "email": "test@saascontrol.dev",
    "password": "TestPass123",
    "full_name": "测试 用户",
    "first_name": "测试",
    "last_name": "用户",
    "is_active": True,
    "email_verified": True,
    "created_at": "2024-01-01T00:00:00Z",
    "avatar_url": None
}

# 存储活跃令牌 (生产环境应使用Redis)
active_tokens = {}

# Pydantic模型定义
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict

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

# JWT工具函数
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return payload
    except jwt.PyJWTError:
        return None

# 认证依赖
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未授权",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    email = payload.get("sub")
    if email != TEST_USER["email"]:
        raise credentials_exception

    return UserResponse(**{k: v for k, v in TEST_USER.items() if k != "password"})

# API端点
@app.get("/health")
async def health_check():
    """健康检查 - 迁移自原始代码"""
    return {
        "status": "healthy",
        "service": "unified-backend-fastapi-migration",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": ["FastAPI", "JWT认证", "Pydantic验证", "异步处理"]
    }

@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """用户登录 - 迁移并改进原始实现"""
    # 验证凭据
    if request.email != TEST_USER["email"] or request.password != TEST_USER["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误"
        )

    # 创建令牌
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": TEST_USER["email"]},
        expires_delta=access_token_expires
    )
    refresh_token = f"refresh_{uuid.uuid4().hex[:16]}"

    # 存储活跃令牌 (生产环境应使用Redis)
    active_tokens[access_token] = {
        "user_email": TEST_USER["email"],
        "expires": datetime.utcnow() + access_token_expires
    }

    user_response = {k: v for k, v in TEST_USER.items() if k != "password"}

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60,  # 30分钟
        user=user_response
    )

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """获取当前用户信息 - 使用依赖注入简化认证"""
    return current_user

@app.post("/data/sources")
async def create_data_source(
    name: str,
    description: str = "",
    current_user: UserResponse = Depends(get_current_user)
):
    """创建数据源 - 展示FastAPI的自动参数验证"""
    source_id = f"ds_{uuid.uuid4().hex[:16]}"

    data_source = {
        "id": source_id,
        "name": name,
        "description": description,
        "type": "file",
        "created_at": datetime.now().isoformat(),
        "created_by": current_user.email,
        "status": "active"
    }

    return data_source

# 启动配置
if __name__ == "__main__":
    import uvicorn

    print("🚀 启动FastAPI迁移版本")
    print("📍 服务地址: http://localhost:8001")
    print("📖 API文档: http://localhost:8001/docs")
    print("👤 测试账号: test@saascontrol.dev / TestPass123")

    uvicorn.run(
        "migration_example_fastapi:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )