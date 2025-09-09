"""
数据分析路由模块
"""

from fastapi import APIRouter, Depends
from shared.auth import get_current_user
from shared.models.user import User

router = APIRouter()


@router.post("/upload")
async def upload_data(current_user: User = Depends(get_current_user)):
    """上传数据文件"""
    return {"message": "Data upload endpoint - 待实现"}


@router.get("/tasks/{task_id}")
async def get_analysis_task(task_id: str, current_user: User = Depends(get_current_user)):
    """获取分析任务状态"""
    return {"message": f"Analysis task {task_id} endpoint - 待实现"}