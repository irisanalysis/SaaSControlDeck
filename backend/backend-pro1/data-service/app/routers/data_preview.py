"""
数据预览路由模块
提供数据解析、预览、统计信息生成等功能
"""

import os
import pandas as pd
import json
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from shared.auth import get_current_user
from shared.models.user import User
from shared.models.data_source import (
    DataSource, DataSourcePreview, ColumnInfo, DataQualityCheck,
    DataSourceStatus, DataQualitySeverity, DataSourceList
)
from shared.database import Database
import structlog

logger = structlog.get_logger()
router = APIRouter()

# 配置
PREVIEW_ROWS = 100  # 预览行数
MAX_SAMPLE_VALUES = 10  # 每列最多显示的样本值数量


def detect_data_type(series: pd.Series) -> str:
    """
    检测pandas Series的数据类型
    返回标准化的数据类型字符串
    """
    # 先检查是否全部为空值
    if series.isnull().all():
        return "null"

    # 去除空值后进行类型检测
    non_null_series = series.dropna()

    # 检查布尔类型
    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    # 检查数值类型
    if pd.api.types.is_numeric_dtype(series):
        # 检查是否为整数
        if pd.api.types.is_integer_dtype(series):
            return "number"
        # 检查是否为浮点数
        elif pd.api.types.is_float_dtype(series):
            return "number"
        else:
            return "number"

    # 检查日期时间类型
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"

    # 尝试解析日期字符串
    if pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
        sample_size = min(100, len(non_null_series))
        sample = non_null_series.sample(n=sample_size) if len(non_null_series) > sample_size else non_null_series

        # 检查是否为日期字符串
        date_count = 0
        for value in sample:
            try:
                pd.to_datetime(str(value))
                date_count += 1
            except:
                continue

        # 如果超过80%的样本都能解析为日期，则认为是日期类型
        if date_count / len(sample) > 0.8:
            return "date"

        # 检查是否为数值字符串
        numeric_count = 0
        for value in sample:
            try:
                float(str(value))
                numeric_count += 1
            except:
                continue

        # 如果超过80%的样本都能解析为数值，则认为是数值类型
        if numeric_count / len(sample) > 0.8:
            return "number"

    # 默认为字符串类型
    return "string"


def get_column_statistics(series: pd.Series, column_name: str, column_index: int) -> ColumnInfo:
    """
    计算列的统计信息
    """
    total_count = len(series)
    missing_count = series.isnull().sum()
    non_null_series = series.dropna()
    unique_count = len(non_null_series.unique()) if len(non_null_series) > 0 else 0

    # 获取数据类型
    data_type = detect_data_type(series)

    # 获取样本值
    sample_values = []
    if len(non_null_series) > 0:
        sample_size = min(MAX_SAMPLE_VALUES, len(non_null_series))
        samples = non_null_series.sample(n=sample_size) if len(non_null_series) > sample_size else non_null_series
        sample_values = [str(val) for val in samples.tolist()]

    # 计算最小值、最大值、平均值、标准差（仅对数值类型）
    min_value = None
    max_value = None
    avg_value = None
    std_value = None

    if data_type == "number" and len(non_null_series) > 0:
        try:
            # 尝试转换为数值类型
            numeric_series = pd.to_numeric(non_null_series, errors='coerce').dropna()
            if len(numeric_series) > 0:
                min_value = str(numeric_series.min())
                max_value = str(numeric_series.max())
                avg_value = float(numeric_series.mean())
                std_value = float(numeric_series.std()) if len(numeric_series) > 1 else 0.0
        except Exception as e:
            logger.warning("数值统计计算失败", column=column_name, error=str(e))

    elif data_type == "string" and len(non_null_series) > 0:
        # 对字符串类型，统计长度
        lengths = non_null_series.astype(str).str.len()
        min_value = str(lengths.min())
        max_value = str(lengths.max())
        avg_value = float(lengths.mean())
        std_value = float(lengths.std()) if len(lengths) > 1 else 0.0

    elif data_type == "date" and len(non_null_series) > 0:
        try:
            # 尝试转换为日期类型
            date_series = pd.to_datetime(non_null_series, errors='coerce').dropna()
            if len(date_series) > 0:
                min_value = str(date_series.min())
                max_value = str(date_series.max())
        except Exception as e:
            logger.warning("日期统计计算失败", column=column_name, error=str(e))

    return ColumnInfo(
        column_name=column_name,
        column_index=column_index,
        data_type=data_type,
        is_nullable=(missing_count > 0),
        unique_count=unique_count,
        missing_count=int(missing_count),
        min_value=min_value,
        max_value=max_value,
        avg_value=avg_value,
        std_value=std_value,
        sample_values=sample_values
    )


def load_dataframe_from_file(file_path: str, file_type: str) -> pd.DataFrame:
    """
    根据文件类型加载数据到DataFrame
    """
    try:
        if file_type == 'csv':
            # 尝试不同的编码和分隔符
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                for sep in [',', ';', '\t', '|']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, sep=sep, nrows=PREVIEW_ROWS * 10)
                        # 检查是否成功读取（至少有一列且不全为空）
                        if len(df.columns) > 0 and not df.empty:
                            logger.info(f"成功读取CSV文件", encoding=encoding, separator=sep)
                            return df
                    except Exception:
                        continue

            # 如果上面都失败，使用默认参数再试一次
            df = pd.read_csv(file_path, nrows=PREVIEW_ROWS * 10)

        elif file_type == 'json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # 尝试从字典的值中创建DataFrame
                if all(isinstance(v, list) for v in data.values()):
                    df = pd.DataFrame(data)
                else:
                    # 将字典转换为单行DataFrame
                    df = pd.DataFrame([data])
            else:
                raise ValueError("不支持的JSON数据格式")

        elif file_type == 'excel':
            df = pd.read_excel(file_path, nrows=PREVIEW_ROWS * 10)

        elif file_type == 'parquet':
            df = pd.read_parquet(file_path)
            # 对parquet文件只取前面的行进行预览
            if len(df) > PREVIEW_ROWS * 10:
                df = df.head(PREVIEW_ROWS * 10)

        else:
            raise ValueError(f"不支持的文件类型: {file_type}")

        return df

    except Exception as e:
        logger.error("文件读取失败", file_path=file_path, file_type=file_type, error=str(e))
        raise HTTPException(status_code=400, detail=f"文件读取失败: {str(e)}")


async def analyze_data_quality(df: pd.DataFrame, dataset_id: int) -> List[DataQualityCheck]:
    """
    分析数据质量问题
    """
    quality_checks = []

    # 检查缺失值
    missing_values = df.isnull().sum()
    total_rows = len(df)

    for column, missing_count in missing_values.items():
        if missing_count > 0:
            percentage = (missing_count / total_rows) * 100
            severity = DataQualitySeverity.INFO
            if percentage > 50:
                severity = DataQualitySeverity.CRITICAL
            elif percentage > 20:
                severity = DataQualitySeverity.ERROR
            elif percentage > 10:
                severity = DataQualitySeverity.WARNING

            quality_checks.append({
                'dataset_id': dataset_id,
                'check_type': 'missing_values',
                'column_name': column,
                'severity': severity.value,
                'message': f'列 "{column}" 有 {missing_count} 个缺失值 ({percentage:.1f}%)',
                'details': {
                    'missing_count': int(missing_count),
                    'total_count': total_rows,
                    'percentage': round(percentage, 2)
                },
                'affected_rows': int(missing_count)
            })

    # 检查重复行
    duplicate_rows = df.duplicated().sum()
    if duplicate_rows > 0:
        percentage = (duplicate_rows / total_rows) * 100
        severity = DataQualitySeverity.WARNING if percentage > 10 else DataQualitySeverity.INFO

        quality_checks.append({
            'dataset_id': dataset_id,
            'check_type': 'duplicates',
            'column_name': None,
            'severity': severity.value,
            'message': f'发现 {duplicate_rows} 行重复数据 ({percentage:.1f}%)',
            'details': {
                'duplicate_count': int(duplicate_rows),
                'total_count': total_rows,
                'percentage': round(percentage, 2)
            },
            'affected_rows': int(duplicate_rows)
        })

    # 检查数据类型一致性
    for column in df.columns:
        series = df[column].dropna()
        if len(series) > 0:
            # 检查数值列中的异常值
            if pd.api.types.is_numeric_dtype(series):
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = series[(series < lower_bound) | (series > upper_bound)]

                if len(outliers) > 0:
                    percentage = (len(outliers) / len(series)) * 100
                    severity = DataQualitySeverity.WARNING if percentage > 5 else DataQualitySeverity.INFO

                    quality_checks.append({
                        'dataset_id': dataset_id,
                        'check_type': 'outliers',
                        'column_name': column,
                        'severity': severity.value,
                        'message': f'列 "{column}" 发现 {len(outliers)} 个异常值 ({percentage:.1f}%)',
                        'details': {
                            'outlier_count': len(outliers),
                            'percentage': round(percentage, 2),
                            'lower_bound': float(lower_bound),
                            'upper_bound': float(upper_bound)
                        },
                        'affected_rows': len(outliers)
                    })

    return quality_checks


async def save_quality_checks(quality_checks: List[Dict]) -> None:
    """
    保存数据质量检查结果到数据库
    """
    if not quality_checks:
        return

    # 批量插入数据质量检查结果
    insert_query = """
    INSERT INTO data_quality_checks (
        dataset_id, check_type, column_name, severity, message, details, affected_rows
    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
    """

    batch_data = []
    for check in quality_checks:
        batch_data.append((
            check['dataset_id'],
            check['check_type'],
            check['column_name'],
            check['severity'],
            check['message'],
            json.dumps(check['details']),
            check['affected_rows']
        ))

    await Database.execute_many(insert_query, batch_data)


async def save_column_info(columns: List[ColumnInfo], dataset_id: int) -> None:
    """
    保存列信息到数据库
    """
    # 先删除现有的列信息
    delete_query = "DELETE FROM dataset_columns WHERE dataset_id = $1"
    await Database.execute(delete_query, dataset_id)

    # 插入新的列信息
    insert_query = """
    INSERT INTO dataset_columns (
        dataset_id, column_name, column_index, data_type, is_nullable,
        unique_count, missing_count, min_value, max_value, avg_value,
        std_value, sample_values
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """

    batch_data = []
    for col in columns:
        batch_data.append((
            dataset_id,
            col.column_name,
            col.column_index,
            col.data_type,
            col.is_nullable,
            col.unique_count,
            col.missing_count,
            col.min_value,
            col.max_value,
            col.avg_value,
            col.std_value,
            col.sample_values
        ))

    await Database.execute_many(insert_query, batch_data)


async def process_dataset_analysis(dataset_id: int, background_tasks: BackgroundTasks):
    """
    后台处理数据集分析任务
    """
    try:
        # 获取数据集信息
        dataset_query = """
        SELECT id, file_path, type, name
        FROM datasets
        WHERE id = $1 AND status = $2
        """
        dataset = await Database.fetch_one(dataset_query, dataset_id, DataSourceStatus.PROCESSING.value)

        if not dataset:
            logger.error("数据集不存在或状态无效", dataset_id=dataset_id)
            return

        # 更新处理开始时间
        await Database.execute(
            "UPDATE datasets SET processing_started_at = $1 WHERE id = $2",
            datetime.utcnow(), dataset_id
        )

        # 加载数据
        df = load_dataframe_from_file(dataset['file_path'], dataset['type'])

        # 生成列信息
        columns = []
        data_types = {}
        for i, column_name in enumerate(df.columns):
            col_info = get_column_statistics(df[column_name], column_name, i)
            columns.append(col_info)
            data_types[column_name] = col_info.data_type

        # 生成预览数据
        preview_df = df.head(PREVIEW_ROWS)
        # 将NaN值转换为None以便JSON序列化
        preview_data = preview_df.where(pd.notnull(preview_df), None).to_dict('records')

        # 计算统计信息
        total_missing = df.isnull().sum().sum()

        # 构建元数据
        metadata = {
            'columns': [col.model_dump() for col in columns],
            'data_types': data_types,
            'sample_data': preview_data,
            'missing_values_count': int(total_missing),
            'file_info': {
                'original_rows': len(df),
                'memory_usage': int(df.memory_usage(deep=True).sum())
            }
        }

        # 数据质量分析
        quality_checks = await analyze_data_quality(df, dataset_id)

        # 保存分析结果
        update_query = """
        UPDATE datasets SET
            rows_count = $1,
            columns_count = $2,
            metadata = $3,
            preview_data = $4,
            status = $5,
            processing_completed_at = $6,
            updated_at = $7
        WHERE id = $8
        """

        await Database.execute(
            update_query,
            len(df),
            len(df.columns),
            json.dumps(metadata),
            json.dumps(preview_data),
            DataSourceStatus.READY.value,
            datetime.utcnow(),
            datetime.utcnow(),
            dataset_id
        )

        # 保存列信息和质量检查结果
        await save_column_info(columns, dataset_id)
        await save_quality_checks(quality_checks)

        logger.info(
            "数据集分析完成",
            dataset_id=dataset_id,
            rows=len(df),
            columns=len(df.columns),
            quality_issues=len(quality_checks)
        )

    except Exception as e:
        logger.error("数据集分析失败", dataset_id=dataset_id, error=str(e))

        # 更新状态为错误
        await Database.execute(
            """
            UPDATE datasets SET
                status = $1,
                error_details = $2,
                processing_completed_at = $3,
                updated_at = $4
            WHERE id = $5
            """,
            DataSourceStatus.ERROR.value,
            str(e),
            datetime.utcnow(),
            datetime.utcnow(),
            dataset_id
        )


@router.get("/datasets/{dataset_id}/preview", response_model=DataSourcePreview)
async def get_data_preview(
    dataset_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    获取数据集预览信息
    """
    # 验证数据集权限
    dataset_query = """
    SELECT d.*, p.user_id
    FROM datasets d
    JOIN projects p ON d.project_id = p.id
    WHERE d.id = $1 AND p.user_id = $2
    """
    dataset = await Database.fetch_one(dataset_query, dataset_id, current_user.id)

    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在或无权限访问")

    if dataset['status'] != DataSourceStatus.READY.value:
        raise HTTPException(
            status_code=400,
            detail=f"数据集状态为 {dataset['status']}，无法预览"
        )

    # 获取列信息
    columns_query = """
    SELECT * FROM dataset_columns
    WHERE dataset_id = $1
    ORDER BY column_index
    """
    column_rows = await Database.fetch_all(columns_query, dataset_id)
    columns = [ColumnInfo(**row) for row in column_rows]

    # 从元数据中获取其他信息
    metadata = dataset.get('metadata', {})
    preview_data = dataset.get('preview_data', [])

    # 构建数据类型映射
    data_types = {col.column_name: col.data_type for col in columns}

    # 构建缺失值统计
    missing_values_summary = {col.column_name: col.missing_count for col in columns}

    return DataSourcePreview(
        dataset_id=dataset_id,
        rows_count=dataset['rows_count'] or 0,
        columns_count=dataset['columns_count'] or 0,
        columns=columns,
        sample_data=preview_data,
        data_types=data_types,
        missing_values_summary=missing_values_summary,
        memory_usage=metadata.get('file_info', {}).get('memory_usage')
    )


@router.get("/datasets", response_model=DataSourceList)
async def list_datasets(
    project_id: Optional[int] = Query(None, description="项目ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    type: Optional[str] = Query(None, description="类型过滤"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据集列表
    """
    # 构建查询条件
    conditions = ["p.user_id = $1"]
    params = [current_user.id]

    if project_id:
        conditions.append(f"d.project_id = ${len(params) + 1}")
        params.append(project_id)

    if status:
        conditions.append(f"d.status = ${len(params) + 1}")
        params.append(status)

    if type:
        conditions.append(f"d.type = ${len(params) + 1}")
        params.append(type)

    # 查询总数
    count_query = f"""
    SELECT COUNT(*)
    FROM datasets d
    JOIN projects p ON d.project_id = p.id
    WHERE {' AND '.join(conditions)}
    """
    total = await Database.fetch_val(count_query, *params)

    # 查询数据
    offset = (page - 1) * size
    query = f"""
    SELECT d.*
    FROM datasets d
    JOIN projects p ON d.project_id = p.id
    WHERE {' AND '.join(conditions)}
    ORDER BY d.created_at DESC
    LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
    """
    params.extend([size, offset])

    rows = await Database.fetch_all(query, *params)
    datasets = [DataSource(**row) for row in rows]

    pages = (total + size - 1) // size

    return DataSourceList(
        items=datasets,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.get("/datasets/{dataset_id}/quality", response_model=List[DataQualityCheck])
async def get_quality_checks(
    dataset_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    获取数据质量检查结果
    """
    # 验证数据集权限
    dataset_query = """
    SELECT d.id
    FROM datasets d
    JOIN projects p ON d.project_id = p.id
    WHERE d.id = $1 AND p.user_id = $2
    """
    dataset = await Database.fetch_one(dataset_query, dataset_id, current_user.id)

    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在或无权限访问")

    # 获取质量检查结果
    query = """
    SELECT * FROM data_quality_checks
    WHERE dataset_id = $1
    ORDER BY severity DESC, created_at DESC
    """
    rows = await Database.fetch_all(query, dataset_id)

    # 解析details字段
    checks = []
    for row in rows:
        check_data = dict(row)
        if check_data['details']:
            try:
                check_data['details'] = json.loads(check_data['details'])
            except:
                check_data['details'] = {}
        checks.append(DataQualityCheck(**check_data))

    return checks


@router.post("/datasets/{dataset_id}/analyze")
async def trigger_analysis(
    dataset_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    触发数据集重新分析
    """
    # 验证数据集权限
    dataset_query = """
    SELECT d.*
    FROM datasets d
    JOIN projects p ON d.project_id = p.id
    WHERE d.id = $1 AND p.user_id = $2
    """
    dataset = await Database.fetch_one(dataset_query, dataset_id, current_user.id)

    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在或无权限访问")

    # 更新状态为处理中
    await Database.execute(
        "UPDATE datasets SET status = $1, updated_at = $2 WHERE id = $3",
        DataSourceStatus.PROCESSING.value,
        datetime.utcnow(),
        dataset_id
    )

    # 添加后台分析任务
    background_tasks.add_task(process_dataset_analysis, dataset_id, background_tasks)

    return {"message": "数据分析任务已启动", "dataset_id": dataset_id}