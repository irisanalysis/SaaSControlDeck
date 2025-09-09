"""
认证路由模块
处理用户认证、注册、登录等功能
"""

from datetime import timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, validator
import structlog

from shared.config import get_settings, Settings
from shared.auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_password_hash,
    verify_refresh_token
)
from shared.database import Database
from shared.models.user import User, UserCreate, UserResponse
from app.core.exceptions import (
    AuthenticationError,
    ValidationError,
    ResourceConflictError
)

logger = structlog.get_logger()
router = APIRouter()


class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    
    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not any(c.isdigit() for c in v):
            raise ValueError("密码必须包含至少一个数字")
        if not any(c.isalpha() for c in v):
            raise ValueError("密码必须包含至少一个字母")
        return v
    
    @validator("first_name", "last_name")
    def validate_name(cls, v):
        if len(v.strip()) < 1:
            raise ValueError("姓名不能为空")
        return v.strip()


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str


@router.post("/register", response_model=Dict[str, Any])
async def register(
    user_data: UserRegisterRequest,
    request: Request,
    settings: Settings = Depends(get_settings)
):
    """用户注册"""
    request_id = getattr(request.state, "request_id", None)
    
    logger.info(
        "用户注册请求",
        email=user_data.email,
        request_id=request_id
    )
    
    # 检查用户是否已存在
    existing_user = await Database.fetch_one(
        "SELECT id FROM users WHERE email = $1",
        user_data.email
    )
    
    if existing_user:
        raise ResourceConflictError("用户已存在", "用户")
    
    # 创建用户
    password_hash = get_password_hash(user_data.password)
    
    try:
        # 插入用户记录
        user_id = await Database.fetch_val(
            """
            INSERT INTO users (email, password_hash, is_active, email_verified)
            VALUES ($1, $2, true, false)
            RETURNING id
            """,
            user_data.email,
            password_hash
        )
        
        # 插入用户档案
        await Database.execute(
            """
            INSERT INTO user_profiles (user_id, first_name, last_name)
            VALUES ($1, $2, $3)
            """,
            user_id,
            user_data.first_name,
            user_data.last_name
        )
        
        # 获取完整用户信息
        user_record = await Database.fetch_one(
            """
            SELECT u.*, p.first_name, p.last_name, p.avatar_url
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            WHERE u.id = $1
            """,
            user_id
        )
        
        user = User.from_record(user_record)
        
        logger.info(
            "用户注册成功",
            user_id=user_id,
            email=user_data.email,
            request_id=request_id
        )
        
        # TODO: 发送验证邮件
        
        return {
            "success": True,
            "message": "注册成功，请检查邮箱完成验证",
            "user": UserResponse.from_user(user)
        }
        
    except Exception as e:
        logger.error(
            "用户注册失败",
            email=user_data.email,
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLoginRequest,
    request: Request,
    settings: Settings = Depends(get_settings)
):
    """用户登录"""
    request_id = getattr(request.state, "request_id", None)
    
    logger.info(
        "用户登录请求",
        email=user_data.email,
        request_id=request_id
    )
    
    # 认证用户
    user = await authenticate_user(user_data.email, user_data.password)
    if not user:
        logger.warning(
            "登录失败：用户名或密码错误",
            email=user_data.email,
            request_id=request_id
        )
        raise AuthenticationError("用户名或密码错误")
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    
    # 创建刷新令牌
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    # 更新最后登录时间
    await Database.execute(
        "UPDATE users SET last_login_at = NOW() WHERE id = $1",
        user.id
    )
    
    logger.info(
        "用户登录成功",
        user_id=user.id,
        email=user.email,
        request_id=request_id
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.from_user(user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    request: Request,
    settings: Settings = Depends(get_settings)
):
    """刷新访问令牌"""
    request_id = getattr(request.state, "request_id", None)
    
    # 验证刷新令牌
    payload = verify_refresh_token(token_data.refresh_token)
    if not payload:
        raise AuthenticationError("无效的刷新令牌")
    
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("无效的刷新令牌")
    
    # 获取用户信息
    user_record = await Database.fetch_one(
        """
        SELECT u.*, p.first_name, p.last_name, p.avatar_url
        FROM users u
        LEFT JOIN user_profiles p ON u.id = p.user_id
        WHERE u.id = $1 AND u.is_active = true
        """,
        int(user_id)
    )
    
    if not user_record:
        raise AuthenticationError("用户不存在或已被禁用")
    
    user = User.from_record(user_record)
    
    # 创建新的访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    
    # 创建新的刷新令牌
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    logger.info(
        "令牌刷新成功",
        user_id=user.id,
        request_id=request_id
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.from_user(user)
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """用户登出"""
    request_id = getattr(request.state, "request_id", None)
    
    # TODO: 将令牌加入黑名单（Redis）
    
    logger.info(
        "用户登出",
        user_id=current_user.id,
        request_id=request_id
    )
    
    return {
        "success": True,
        "message": "登出成功"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse.from_user(current_user)