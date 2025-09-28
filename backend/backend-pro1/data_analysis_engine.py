#!/usr/bin/env python3
"""
数据分析引擎模块
提供完整的数据分析、列统计、质量检查功能
RELEVANT FILES: unified_backend_fastapi.py, shared/database.py
"""

import io
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np
import pandas as pd

class DataAnalysisEngine:
    """数据分析引擎类"""

    @staticmethod
    def analyze_file_content(content: bytes, filename: str, mime_type: str) -> Dict[str, Any]:
        """
        分析文件内容，自动检测文件类型并提取数据信息

        Args:
            content: 文件二进制内容
            filename: 文件名
            mime_type: MIME类型

        Returns:
            包含分析结果的字典
        """
        try:
            # 根据文件扩展名判断文件类型
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ''

            # 尝试加载为DataFrame
            df = None
            if file_ext == 'csv' or mime_type == 'text/csv':
                df = pd.read_csv(io.BytesIO(content))
            elif file_ext in ['xlsx', 'xls'] or 'excel' in mime_type.lower():
                df = pd.read_excel(io.BytesIO(content))
            elif file_ext == 'json' or mime_type == 'application/json':
                try:
                    data = json.loads(content.decode('utf-8'))
                    # 如果是列表，直接转换为DataFrame
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                    # 如果是字典，尝试转换
                    elif isinstance(data, dict):
                        df = pd.DataFrame([data])
                except json.JSONDecodeError:
                    pass
            elif file_ext == 'parquet':
                df = pd.read_parquet(io.BytesIO(content))

            if df is None:
                return {
                    "success": False,
                    "error": "无法解析文件内容"
                }

            # 基础统计信息
            basic_stats = {
                "rows_count": len(df),
                "columns_count": len(df.columns),
                "file_type": file_ext or 'unknown',
                "memory_usage": df.memory_usage(deep=True).sum()
            }

            # 列详细分析
            columns_analysis = DataAnalysisEngine._analyze_columns(df)

            # 数据质量检查
            quality_checks = DataAnalysisEngine._perform_quality_checks(df)

            # 生成预览数据（前10行）
            preview_data = df.head(10).to_dict(orient='records')

            return {
                "success": True,
                "basic_stats": basic_stats,
                "columns": columns_analysis,
                "quality_checks": quality_checks,
                "preview_data": preview_data
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def _analyze_columns(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        分析数据框中的每一列

        Args:
            df: pandas DataFrame

        Returns:
            列分析结果列表
        """
        columns_info = []

        for idx, column_name in enumerate(df.columns):
            column_data = df[column_name]

            # 基础信息
            col_info = {
                "column_name": str(column_name),
                "column_index": idx,
                "data_type": str(column_data.dtype),
                "is_nullable": column_data.isnull().any(),
                "null_count": int(column_data.isnull().sum()),
                "unique_count": int(column_data.nunique()),
                "sample_values": []
            }

            # 获取样本值（前5个非空唯一值）
            non_null_values = column_data.dropna().unique()[:5]
            col_info["sample_values"] = [str(val) for val in non_null_values]

            # 数值类型的统计信息
            if pd.api.types.is_numeric_dtype(column_data):
                col_info["min_value"] = str(column_data.min()) if not column_data.empty else None
                col_info["max_value"] = str(column_data.max()) if not column_data.empty else None
                col_info["avg_value"] = float(column_data.mean()) if not column_data.empty else None
                col_info["std_value"] = float(column_data.std()) if not column_data.empty else None
                col_info["median_value"] = float(column_data.median()) if not column_data.empty else None

            # 文本类型的统计信息
            elif pd.api.types.is_string_dtype(column_data) or column_data.dtype == 'object':
                col_info["min_length"] = int(column_data.astype(str).str.len().min()) if not column_data.empty else None
                col_info["max_length"] = int(column_data.astype(str).str.len().max()) if not column_data.empty else None
                col_info["avg_length"] = float(column_data.astype(str).str.len().mean()) if not column_data.empty else None

            columns_info.append(col_info)

        return columns_info

    @staticmethod
    def _perform_quality_checks(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        执行数据质量检查

        Args:
            df: pandas DataFrame

        Returns:
            质量检查结果列表
        """
        quality_checks = []

        # 检查1: 空值比例
        for column in df.columns:
            null_ratio = df[column].isnull().sum() / len(df)
            if null_ratio > 0:
                severity = "critical" if null_ratio > 0.5 else ("warning" if null_ratio > 0.1 else "info")
                quality_checks.append({
                    "check_type": "null_values",
                    "severity": severity,
                    "message": f"列 '{column}' 包含 {null_ratio*100:.2f}% 的空值",
                    "details": {
                        "column": str(column),
                        "null_count": int(df[column].isnull().sum()),
                        "null_ratio": float(null_ratio)
                    },
                    "affected_rows": int(df[column].isnull().sum())
                })

        # 检查2: 重复行
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            duplicate_ratio = duplicate_count / len(df)
            severity = "warning" if duplicate_ratio > 0.1 else "info"
            quality_checks.append({
                "check_type": "duplicate_rows",
                "severity": severity,
                "message": f"发现 {duplicate_count} 行重复数据 ({duplicate_ratio*100:.2f}%)",
                "details": {
                    "duplicate_count": int(duplicate_count),
                    "duplicate_ratio": float(duplicate_ratio)
                },
                "affected_rows": int(duplicate_count)
            })

        # 检查3: 数据类型一致性
        for column in df.columns:
            if df[column].dtype == 'object':
                # 尝试检测混合类型
                type_counts = df[column].dropna().apply(type).value_counts()
                if len(type_counts) > 1:
                    quality_checks.append({
                        "check_type": "mixed_types",
                        "severity": "warning",
                        "message": f"列 '{column}' 包含混合数据类型",
                        "details": {
                            "column": str(column),
                            "type_distribution": {str(k): int(v) for k, v in type_counts.items()}
                        },
                        "affected_rows": int(len(df[column]))
                    })

        # 检查4: 异常值检测（仅数值列）
        for column in df.select_dtypes(include=[np.number]).columns:
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((df[column] < (Q1 - 1.5 * IQR)) | (df[column] > (Q3 + 1.5 * IQR))).sum()

            if outliers > 0:
                outlier_ratio = outliers / len(df)
                severity = "warning" if outlier_ratio > 0.05 else "info"
                quality_checks.append({
                    "check_type": "outliers",
                    "severity": severity,
                    "message": f"列 '{column}' 检测到 {outliers} 个异常值",
                    "details": {
                        "column": str(column),
                        "outlier_count": int(outliers),
                        "outlier_ratio": float(outlier_ratio),
                        "Q1": float(Q1),
                        "Q3": float(Q3),
                        "IQR": float(IQR)
                    },
                    "affected_rows": int(outliers)
                })

        return quality_checks

    @staticmethod
    def calculate_quality_score(quality_checks: List[Dict[str, Any]]) -> float:
        """
        根据质量检查结果计算数据质量分数（0-100）

        Args:
            quality_checks: 质量检查结果列表

        Returns:
            质量分数（0-100）
        """
        if not quality_checks:
            return 100.0

        # 权重配置
        severity_weights = {
            "info": 0.5,
            "warning": 2.0,
            "error": 5.0,
            "critical": 10.0
        }

        # 计算总扣分
        total_deduction = sum(
            severity_weights.get(check["severity"], 1.0)
            for check in quality_checks
        )

        # 计算最终分数（最低0分）
        score = max(0.0, 100.0 - total_deduction)

        return round(score, 2)

    @staticmethod
    def generate_ai_insights(df: pd.DataFrame, columns_analysis: List[Dict], quality_checks: List[Dict]) -> Dict[str, Any]:
        """
        生成AI洞察信息

        Args:
            df: pandas DataFrame
            columns_analysis: 列分析结果
            quality_checks: 质量检查结果

        Returns:
            AI洞察字典
        """
        insights = {
            "summary": "",
            "recommendations": [],
            "data_characteristics": {},
            "generated_at": datetime.now().isoformat()
        }

        # 生成概述
        row_count = len(df)
        col_count = len(df.columns)
        insights["summary"] = f"数据集包含 {row_count} 行和 {col_count} 列。"

        # 数据特征
        numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
        text_cols = len(df.select_dtypes(include=['object']).columns)

        insights["data_characteristics"] = {
            "total_rows": row_count,
            "total_columns": col_count,
            "numeric_columns": numeric_cols,
            "text_columns": text_cols,
            "data_density": float(df.notna().sum().sum() / (row_count * col_count)) if row_count > 0 and col_count > 0 else 0.0
        }

        # 生成建议
        critical_issues = [c for c in quality_checks if c["severity"] == "critical"]
        warning_issues = [c for c in quality_checks if c["severity"] == "warning"]

        if critical_issues:
            insights["recommendations"].append({
                "priority": "high",
                "category": "data_quality",
                "message": f"发现 {len(critical_issues)} 个严重的数据质量问题，建议立即处理"
            })

        if warning_issues:
            insights["recommendations"].append({
                "priority": "medium",
                "category": "data_quality",
                "message": f"发现 {len(warning_issues)} 个需要注意的数据质量问题"
            })

        # 检查是否有高比例空值的列
        high_null_cols = [col for col in columns_analysis if col.get("null_count", 0) / row_count > 0.3]
        if high_null_cols:
            insights["recommendations"].append({
                "priority": "medium",
                "category": "data_cleaning",
                "message": f"{len(high_null_cols)} 个列的空值比例超过30%，考虑删除或填充"
            })

        return insights