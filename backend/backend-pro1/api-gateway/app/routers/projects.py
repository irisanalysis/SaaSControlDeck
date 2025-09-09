"""
项目管理路由模块
"""

from fastapi import APIRouter, Depends
from shared.auth import get_current_user
from shared.models.user import User

router = APIRouter()


@router.get("/")
async def get_projects(current_user: User = Depends(get_current_user)):
    """获取项目列表"""
    return {"message": "Project list endpoint - 待实现"}


@router.post("/")
async def create_project(current_user: User = Depends(get_current_user)):
    """创建项目"""
    return {"message": "Create project endpoint - 待实现"}