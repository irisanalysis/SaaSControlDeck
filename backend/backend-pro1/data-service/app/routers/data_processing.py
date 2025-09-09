"""
数据处理路由模块
"""

from fastapi import APIRouter, Depends
from shared.auth import get_current_user
from shared.models.user import User

router = APIRouter()


@router.post("/preprocess/{dataset_id}")
async def preprocess_dataset(dataset_id: int, current_user: User = Depends(get_current_user)):
    """预处理数据集"""
    return {"message": f"预处理数据集 {dataset_id} 功能待实现"}


@router.get("/status/{task_id}")
async def get_processing_status(task_id: str, current_user: User = Depends(get_current_user)):
    """获取处理状态"""
    return {"message": f"获取任务 {task_id} 状态功能待实现"}