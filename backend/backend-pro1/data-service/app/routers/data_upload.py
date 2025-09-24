"""
数据上传路由模块
提供文件上传、分块上传、上传进度跟踪等功能
"""

import os
import hashlib
import uuid
import asyncio
import tempfile
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import (
    APIRouter, UploadFile, File, Depends, Request, HTTPException,
    Form, BackgroundTasks, Query
)
from fastapi.responses import JSONResponse
from shared.auth import get_current_user
from shared.models.user import User
from shared.models.data_source import (
    DataSource, DataSourceCreate, UploadSession, UploadSessionCreate,
    FileUploadResponse, ChunkUploadResponse, DataSourceStatus, UploadSessionStatus
)
from shared.database import Database
from shared.redis_client import RedisClient
import structlog

logger = structlog.get_logger()
router = APIRouter()

# 配置
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_TYPES = {'csv', 'json', 'xlsx', 'xls', 'parquet'}
ALLOWED_MIME_TYPES = {
    'text/csv', 'application/json', 'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/octet-stream'  # for parquet files
}
UPLOAD_DIR = Path(tempfile.gettempdir()) / "data_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def get_file_type_from_filename(filename: str) -> str:
    """从文件名获取文件类型"""
    ext = Path(filename).suffix.lower()
    if ext == '.csv':
        return 'csv'
    elif ext == '.json':
        return 'json'
    elif ext in ['.xlsx', '.xls']:
        return 'excel'
    elif ext == '.parquet':
        return 'parquet'
    else:
        raise ValueError(f"不支持的文件类型: {ext}")


def validate_file_upload(file: UploadFile) -> None:
    """验证上传文件"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 检查文件扩展名
    ext = Path(file.filename).suffix.lower().lstrip('.')
    if ext not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}。支持的类型: {', '.join(ALLOWED_TYPES)}"
        )

    # 检查MIME类型
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        logger.warning(
            "MIME类型不在允许列表中",
            content_type=file.content_type,
            filename=file.filename
        )


async def calculate_file_hash(file_path: Path) -> str:
    """计算文件SHA256哈希值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


async def create_upload_session(
    session_data: UploadSessionCreate,
    user_id: int
) -> UploadSession:
    """创建上传会话"""
    session_id = str(uuid.uuid4())
    total_chunks = (session_data.file_size + session_data.chunk_size - 1) // session_data.chunk_size

    query = """
    INSERT INTO upload_sessions (
        id, user_id, project_id, filename, file_size, chunk_size,
        total_chunks, status, created_at, updated_at, expires_at
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
    RETURNING *
    """

    now = datetime.utcnow()
    expires_at = now + timedelta(hours=24)

    row = await Database.fetch_one(
        query, session_id, user_id, session_data.project_id,
        session_data.filename, session_data.file_size, session_data.chunk_size,
        total_chunks, UploadSessionStatus.UPLOADING.value, now, now, expires_at
    )

    return UploadSession(**row)


async def get_upload_session(session_id: str, user_id: int) -> Optional[UploadSession]:
    """获取上传会话"""
    query = """
    SELECT * FROM upload_sessions
    WHERE id = $1 AND user_id = $2
    """
    row = await Database.fetch_one(query, session_id, user_id)
    return UploadSession(**row) if row else None


async def process_uploaded_file(
    file_path: Path,
    session: UploadSession,
    user_id: int
) -> int:
    """处理上传完成的文件"""
    try:
        # 计算文件哈希
        file_hash = await calculate_file_hash(file_path)

        # 检查是否已存在相同文件
        existing_query = """
        SELECT id FROM datasets
        WHERE file_hash = $1 AND project_id = $2
        """
        existing = await Database.fetch_one(existing_query, file_hash, session.project_id)

        if existing:
            logger.info("发现重复文件", file_hash=file_hash, existing_id=existing['id'])
            raise HTTPException(status_code=400, detail="文件已存在")

        # 获取文件类型
        file_type = get_file_type_from_filename(session.filename)

        # 创建数据集记录
        dataset_query = """
        INSERT INTO datasets (
            project_id, name, type, file_path, file_size, original_filename,
            file_hash, mime_type, status, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING id
        """

        name = Path(session.filename).stem  # 文件名不含扩展名
        now = datetime.utcnow()

        result = await Database.fetch_one(
            dataset_query, session.project_id, name, file_type,
            str(file_path), session.file_size, session.filename,
            file_hash, "application/octet-stream", DataSourceStatus.PROCESSING.value,
            now, now
        )

        dataset_id = result['id']

        # 更新上传会话
        update_session_query = """
        UPDATE upload_sessions
        SET dataset_id = $1, status = $2, updated_at = $3
        WHERE id = $4
        """
        await Database.execute(
            update_session_query, dataset_id,
            UploadSessionStatus.PROCESSING.value, now, session.id
        )

        logger.info(
            "文件上传完成，开始处理",
            dataset_id=dataset_id,
            session_id=session.id,
            filename=session.filename
        )

        return dataset_id

    except Exception as e:
        logger.error("文件处理失败", error=str(e), session_id=session.id)
        # 更新会话状态为失败
        update_query = """
        UPDATE upload_sessions
        SET status = $1, error_message = $2, updated_at = $3
        WHERE id = $4
        """
        await Database.execute(
            update_query, UploadSessionStatus.FAILED.value,
            str(e), datetime.utcnow(), session.id
        )
        raise


@router.post("/session", response_model=UploadSession)
async def create_upload_session_endpoint(
    request: Request,
    session_data: UploadSessionCreate,
    current_user: User = Depends(get_current_user)
):
    """创建文件上传会话"""
    request_id = getattr(request.state, "request_id", None)

    logger.info(
        "创建上传会话",
        filename=session_data.filename,
        file_size=session_data.file_size,
        user_id=current_user.id,
        request_id=request_id
    )

    # 验证文件大小
    if session_data.file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超出限制 ({MAX_FILE_SIZE // 1024 // 1024}MB)"
        )

    # 验证项目权限
    project_query = """
    SELECT id FROM projects
    WHERE id = $1 AND user_id = $2 AND status = 'active'
    """
    project = await Database.fetch_one(project_query, session_data.project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在或无权限")

    session = await create_upload_session(session_data, current_user.id)
    return session


@router.post("/file", response_model=FileUploadResponse)
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_id: int = Form(...),
    current_user: User = Depends(get_current_user)
):
    """上传完整文件（小文件直接上传）"""
    request_id = getattr(request.state, "request_id", None)

    logger.info(
        "文件上传请求",
        filename=file.filename,
        content_type=file.content_type,
        user_id=current_user.id,
        request_id=request_id
    )

    # 验证文件
    validate_file_upload(file)

    # 检查文件大小
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超出限制 ({MAX_FILE_SIZE // 1024 // 1024}MB)"
        )

    # 验证项目权限
    project_query = """
    SELECT id FROM projects
    WHERE id = $1 AND user_id = $2 AND status = 'active'
    """
    project = await Database.fetch_one(project_query, project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在或无权限")

    # 创建上传会话
    session_data = UploadSessionCreate(
        filename=file.filename,
        file_size=file_size,
        project_id=project_id,
        chunk_size=file_size  # 单块上传
    )
    session = await create_upload_session(session_data, current_user.id)

    # 保存文件
    file_path = UPLOAD_DIR / f"{session.id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(content)

    # 后台处理文件
    background_tasks.add_task(process_uploaded_file, file_path, session, current_user.id)

    return FileUploadResponse(
        success=True,
        session_id=session.id,
        message="文件上传成功，正在处理中"
    )


@router.post("/chunk/{session_id}", response_model=ChunkUploadResponse)
async def upload_chunk(
    session_id: str,
    chunk_index: int = Form(...),
    chunk: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """上传文件分块"""
    # 获取上传会话
    session = await get_upload_session(session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="上传会话不存在")

    if session.status != UploadSessionStatus.UPLOADING:
        raise HTTPException(status_code=400, detail="上传会话状态无效")

    # 检查会话是否过期
    if session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="上传会话已过期")

    # 验证分块索引
    if chunk_index < 0 or chunk_index >= session.total_chunks:
        raise HTTPException(status_code=400, detail="无效的分块索引")

    # 保存分块文件
    chunk_dir = UPLOAD_DIR / session_id
    chunk_dir.mkdir(exist_ok=True)
    chunk_path = chunk_dir / f"chunk_{chunk_index}"

    content = await chunk.read()
    with open(chunk_path, "wb") as f:
        f.write(content)

    # 更新上传进度
    uploaded_chunks = session.uploaded_chunks + 1
    uploaded_size = session.uploaded_size + len(content)

    update_query = """
    UPDATE upload_sessions
    SET uploaded_chunks = $1, uploaded_size = $2, updated_at = $3
    WHERE id = $4
    """
    await Database.execute(
        update_query, uploaded_chunks, uploaded_size,
        datetime.utcnow(), session_id
    )

    progress_percentage = (uploaded_chunks / session.total_chunks) * 100
    is_complete = uploaded_chunks >= session.total_chunks

    # 如果所有分块都已上传，合并文件
    if is_complete:
        await merge_chunks(session_id, session, current_user.id)

    return ChunkUploadResponse(
        success=True,
        chunk_index=chunk_index,
        uploaded_chunks=uploaded_chunks,
        total_chunks=session.total_chunks,
        progress_percentage=progress_percentage,
        is_complete=is_complete,
        message="分块上传成功" if not is_complete else "文件上传完成，正在处理"
    )


async def merge_chunks(session_id: str, session: UploadSession, user_id: int):
    """合并所有分块文件"""
    chunk_dir = UPLOAD_DIR / session_id
    final_file_path = UPLOAD_DIR / f"{session_id}_{session.filename}"

    try:
        with open(final_file_path, "wb") as final_file:
            for i in range(session.total_chunks):
                chunk_path = chunk_dir / f"chunk_{i}"
                if not chunk_path.exists():
                    raise Exception(f"分块文件 {i} 不存在")

                with open(chunk_path, "rb") as chunk_file:
                    final_file.write(chunk_file.read())

        # 清理分块文件
        import shutil
        shutil.rmtree(chunk_dir)

        # 处理合并后的文件
        await process_uploaded_file(final_file_path, session, user_id)

    except Exception as e:
        logger.error("分块合并失败", error=str(e), session_id=session_id)
        # 更新会话状态
        update_query = """
        UPDATE upload_sessions
        SET status = $1, error_message = $2, updated_at = $3
        WHERE id = $4
        """
        await Database.execute(
            update_query, UploadSessionStatus.FAILED.value,
            str(e), datetime.utcnow(), session_id
        )
        raise


@router.get("/progress/{session_id}", response_model=UploadSession)
async def get_upload_progress(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取上传进度"""
    session = await get_upload_session(session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="上传会话不存在")

    return session


@router.delete("/session/{session_id}")
async def cancel_upload(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """取消上传"""
    session = await get_upload_session(session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="上传会话不存在")

    # 更新会话状态
    update_query = """
    UPDATE upload_sessions
    SET status = $1, updated_at = $2
    WHERE id = $3
    """
    await Database.execute(
        update_query, UploadSessionStatus.CANCELLED.value,
        datetime.utcnow(), session_id
    )

    # 清理临时文件
    chunk_dir = UPLOAD_DIR / session_id
    if chunk_dir.exists():
        import shutil
        shutil.rmtree(chunk_dir)

    final_file_path = UPLOAD_DIR / f"{session_id}_{session.filename}"
    if final_file_path.exists():
        final_file_path.unlink()

    return {"message": "上传已取消"}


@router.get("/sessions")
async def list_upload_sessions(
    request: Request,
    status: Optional[str] = Query(None, description="按状态过滤"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    current_user: User = Depends(get_current_user)
):
    """获取用户的上传会话列表"""
    conditions = ["user_id = $1"]
    params = [current_user.id]

    if status:
        conditions.append(f"status = ${len(params) + 1}")
        params.append(status)

    # 查询总数
    count_query = f"""
    SELECT COUNT(*) FROM upload_sessions
    WHERE {' AND '.join(conditions)}
    """
    total = await Database.fetch_val(count_query, *params)

    # 查询数据
    query = f"""
    SELECT * FROM upload_sessions
    WHERE {' AND '.join(conditions)}
    ORDER BY created_at DESC
    LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
    """
    params.extend([limit, offset])

    rows = await Database.fetch_all(query, *params)
    sessions = [UploadSession(**row) for row in rows]

    return {
        "items": sessions,
        "total": total,
        "limit": limit,
        "offset": offset
    }


# 开发环境临时测试端点 - 不需要认证
@router.post("/test-file", response_model=dict)
async def upload_test_file(
    request: Request,
    file: UploadFile = File(...),
    project_id: int = Form(default=1)  # 使用默认项目ID
):
    """临时测试文件上传端点 - 仅用于开发环境测试"""
    request_id = getattr(request.state, "request_id", None)
    logger.info(
        "测试文件上传",
        filename=file.filename,
        content_type=file.content_type,
        request_id=request_id
    )

    try:
        # 基本文件验证
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制 ({MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
            )

        # 检查文件类型
        file_ext = Path(file.filename).suffix.lower()
        if file_ext.lstrip('.') not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。支持的类型: {', '.join(ALLOWED_TYPES)}"
            )

        # 保存文件到临时目录
        file_path = UPLOAD_DIR / f"test_{uuid.uuid4()}{file_ext}"

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # 计算文件哈希
        file_hash = hashlib.sha256(content).hexdigest()

        logger.info(
            "测试文件上传成功",
            filename=file.filename,
            file_size=len(content),
            file_hash=file_hash,
            saved_path=str(file_path)
        )

        return {
            "success": True,
            "message": "文件上传成功（测试模式）",
            "filename": file.filename,
            "file_size": len(content),
            "file_hash": file_hash,
            "file_type": file_ext.lstrip('.'),
            "saved_path": str(file_path)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("测试文件上传失败", error=str(e), request_id=request_id)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")