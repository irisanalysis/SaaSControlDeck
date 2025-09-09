"""
用户管理路由模块
"""

from fastapi import APIRouter, Depends, Request
from shared.auth import get_current_user
from shared.models.user import User, UserResponse

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """获取用户档案"""
    return UserResponse.from_user(current_user)


@router.put("/profile")
async def update_user_profile(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """更新用户档案"""
    return {"message": "Profile update endpoint - 待实现"}