"""
数据管理路由模块
"""

from fastapi import APIRouter, Depends
from shared.auth import get_current_user
from shared.models.user import User

router = APIRouter()


@router.get("/datasets")
async def get_datasets(current_user: User = Depends(get_current_user)):
    """获取数据集列表"""
    return {"message": "数据集列表功能待实现"}


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: int, current_user: User = Depends(get_current_user)):
    """删除数据集"""
    return {"message": f"删除数据集 {dataset_id} 功能待实现"}