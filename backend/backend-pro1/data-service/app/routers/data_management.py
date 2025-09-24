"""
数据管理路由模块
提供数据集的增删改查、统计分析等功能
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from shared.auth import get_current_user
from shared.models.user import User
from shared.models.data_source import (
    DataSource, DataSourceUpdate, DataSourceAnalytics,
    DataSourceStatus, UploadSessionStatus
)
from shared.database import Database
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.get("/datasets/{dataset_id}", response_model=DataSource)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取单个数据集详情"""
    # 验证数据集权限
    query = """
    SELECT d.*
    FROM datasets d
    JOIN projects p ON d.project_id = p.id
    WHERE d.id = $1 AND p.user_id = $2
    """
    dataset = await Database.fetch_one(query, dataset_id, current_user.id)

    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在或无权限访问")

    return DataSource(**dataset)


@router.put("/datasets/{dataset_id}", response_model=DataSource)
async def update_dataset(
    dataset_id: int,
    update_data: DataSourceUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新数据集信息"""
    # 验证数据集权限
    query = """
    SELECT d.*
    FROM datasets d
    JOIN projects p ON d.project_id = p.id
    WHERE d.id = $1 AND p.user_id = $2
    """
    dataset = await Database.fetch_one(query, dataset_id, current_user.id)

    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在或无权限访问")

    # 构建更新字段
    update_fields = []
    params = []
    param_index = 1

    if update_data.name is not None:
        update_fields.append(f"name = ${param_index}")
        params.append(update_data.name)
        param_index += 1

    if update_data.description is not None:
        # 注意：datasets表中没有description字段，这里假设有
        # 实际上可能需要在metadata中存储描述信息
        metadata = dataset.get('metadata', {})
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        metadata['description'] = update_data.description
        update_fields.append(f"metadata = ${param_index}")
        params.append(json.dumps(metadata))
        param_index += 1

    if update_data.status is not None:
        update_fields.append(f"status = ${param_index}")
        params.append(update_data.status.value)
        param_index += 1

    if not update_fields:
        # 没有更新字段，直接返回原数据
        return DataSource(**dataset)

    # 添加更新时间
    update_fields.append(f"updated_at = ${param_index}")
    params.append(datetime.utcnow())
    param_index += 1

    # 添加WHERE条件参数
    params.append(dataset_id)

    update_query = f"""
    UPDATE datasets
    SET {', '.join(update_fields)}
    WHERE id = ${param_index}
    RETURNING *
    """

    updated_dataset = await Database.fetch_one(update_query, *params)
    return DataSource(**updated_dataset)


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user)
):
    """删除数据集"""
    # 验证数据集权限
    query = """
    SELECT d.*
    FROM datasets d
    JOIN projects p ON d.project_id = p.id
    WHERE d.id = $1 AND p.user_id = $2
    """
    dataset = await Database.fetch_one(query, dataset_id, current_user.id)

    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在或无权限访问")

    try:
        # 开始事务
        async with Database.get_connection() as conn:
            async with conn.transaction():
                # 删除数据质量检查记录
                await conn.execute(
                    "DELETE FROM data_quality_checks WHERE dataset_id = $1",
                    dataset_id
                )

                # 删除列信息
                await conn.execute(
                    "DELETE FROM dataset_columns WHERE dataset_id = $1",
                    dataset_id
                )

                # 更新相关的上传会话
                await conn.execute(
                    "UPDATE upload_sessions SET dataset_id = NULL WHERE dataset_id = $1",
                    dataset_id
                )

                # 删除数据集记录
                await conn.execute(
                    "DELETE FROM datasets WHERE id = $1",
                    dataset_id
                )

        # 删除文件
        if dataset['file_path'] and os.path.exists(dataset['file_path']):
            try:
                os.remove(dataset['file_path'])
                logger.info("数据集文件已删除", file_path=dataset['file_path'])
            except Exception as e:
                logger.warning("文件删除失败", file_path=dataset['file_path'], error=str(e))

        logger.info(
            "数据集删除成功",
            dataset_id=dataset_id,
            dataset_name=dataset['name'],
            user_id=current_user.id
        )

        return {"message": "数据集删除成功", "dataset_id": dataset_id}

    except Exception as e:
        logger.error("数据集删除失败", dataset_id=dataset_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/analytics", response_model=DataSourceAnalytics)
async def get_analytics(
    project_id: Optional[int] = Query(None, description="项目ID过滤"),
    current_user: User = Depends(get_current_user)
):
    """获取数据源分析统计"""
    # 构建基础查询条件
    conditions = ["p.user_id = $1"]
    params = [current_user.id]

    if project_id:
        conditions.append(f"d.project_id = ${len(params) + 1}")
        params.append(project_id)

    where_clause = ' AND '.join(conditions)

    # 查询总数据集数量
    total_query = f"""
    SELECT COUNT(*) as total_datasets
    FROM datasets d
    JOIN projects p ON d.project_id = p.id
    WHERE {where_clause}
    """
    total_result = await Database.fetch_one(total_query, *params)
    total_datasets = total_result['total_datasets']

    # 按类型分组统计
    type_query = f"""
    SELECT d.type, COUNT(*) as count
    FROM datasets d
    JOIN projects p ON d.project_id = p.id
    WHERE {where_clause}
    GROUP BY d.type
    """
    type_results = await Database.fetch_all(type_query, *params)
    datasets_by_type = {row['type']: row['count'] for row in type_results}

    # 按状态分组统计
    status_query = f"""
    SELECT d.status, COUNT(*) as count
    FROM datasets d
    JOIN projects p ON d.project_id = p.id
    WHERE {where_clause}
    GROUP BY d.status
    """
    status_results = await Database.fetch_all(status_query, *params)
    datasets_by_status = {row['status']: row['count'] for row in status_results}

    # 统计总文件大小和总行数
    size_query = f"""
    SELECT
        COALESCE(SUM(d.file_size), 0) as total_size,
        COALESCE(SUM(d.rows_count), 0) as total_rows
    FROM datasets d
    JOIN projects p ON d.project_id = p.id
    WHERE {where_clause} AND d.file_size IS NOT NULL
    """
    size_result = await Database.fetch_one(size_query, *params)

    # 获取最近上传的数据集
    recent_query = f"""
    SELECT d.*
    FROM datasets d
    JOIN projects p ON d.project_id = p.id
    WHERE {where_clause}
    ORDER BY d.created_at DESC
    LIMIT 5
    """
    recent_results = await Database.fetch_all(recent_query, *params)
    recent_uploads = [DataSource(**row) for row in recent_results]

    # 统计数据质量问题
    quality_query = f"""
    SELECT COUNT(DISTINCT dqc.id) as quality_issues
    FROM data_quality_checks dqc
    JOIN datasets d ON dqc.dataset_id = d.id
    JOIN projects p ON d.project_id = p.id
    WHERE {where_clause} AND dqc.severity IN ('error', 'critical')
    """
    quality_result = await Database.fetch_one(quality_query, *params)

    return DataSourceAnalytics(
        total_datasets=total_datasets,
        datasets_by_type=datasets_by_type,
        datasets_by_status=datasets_by_status,
        total_size=size_result['total_size'],
        total_rows=size_result['total_rows'],
        recent_uploads=recent_uploads,
        quality_issues=quality_result['quality_issues']
    )


@router.post("/cleanup")
async def cleanup_expired_sessions(
    current_user: User = Depends(get_current_user)
):
    """清理过期的上传会话（管理员功能）"""
    # 这里简化处理，实际应该检查用户权限

    # 查找过期的会话
    expired_query = """
    SELECT id, temp_file_path FROM upload_sessions
    WHERE expires_at < NOW() AND status NOT IN ('completed', 'cancelled')
    """
    expired_sessions = await Database.fetch_all(expired_query)

    if not expired_sessions:
        return {"message": "没有找到过期的上传会话"}

    # 删除过期会话
    cleanup_count = 0
    for session in expired_sessions:
        try:
            # 删除临时文件
            if session['temp_file_path'] and os.path.exists(session['temp_file_path']):
                os.remove(session['temp_file_path'])

            # 更新会话状态
            await Database.execute(
                "UPDATE upload_sessions SET status = $1 WHERE id = $2",
                UploadSessionStatus.CANCELLED.value,
                session['id']
            )
            cleanup_count += 1

        except Exception as e:
            logger.error("清理会话失败", session_id=session['id'], error=str(e))

    logger.info("清理过期会话完成", cleaned_count=cleanup_count, total_found=len(expired_sessions))

    return {
        "message": f"清理完成，共清理 {cleanup_count} 个过期会话",
        "cleaned_count": cleanup_count,
        "total_found": len(expired_sessions)
    }


@router.get("/projects/{project_id}/datasets/summary")
async def get_project_datasets_summary(
    project_id: int,
    current_user: User = Depends(get_current_user)
):
    """获取项目的数据集摘要信息"""
    # 验证项目权限
    project_query = """
    SELECT id FROM projects
    WHERE id = $1 AND user_id = $2 AND status = 'active'
    """
    project = await Database.fetch_one(project_query, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在或无权限")

    # 获取项目数据集统计
    summary_query = """
    SELECT
        COUNT(*) as total_count,
        COUNT(CASE WHEN status = 'ready' THEN 1 END) as ready_count,
        COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_count,
        COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count,
        COALESCE(SUM(file_size), 0) as total_size,
        COALESCE(SUM(rows_count), 0) as total_rows
    FROM datasets
    WHERE project_id = $1
    """
    summary = await Database.fetch_one(summary_query, project_id)

    return {
        "project_id": project_id,
        "datasets_summary": dict(summary)
    }