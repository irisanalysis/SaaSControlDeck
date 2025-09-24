# 数据管理功能 - API接口规范

## 🌐 API架构概览

基于RESTful设计原则，为数据管理功能提供完整的API接口，支持文件上传、质量分析、AI对话和结果导出等核心功能。所有接口遵循统一的认证、限流和错误处理标准。

## 🔗 API网关路由配置

### 服务路由分发 (API Gateway: 8000/8100)

```python
# 路由配置
API_ROUTES = {
    "/api/v1/data-management/*": "file-processing-service:8005",
    "/api/v1/quality-analysis/*": "quality-service:8003",
    "/api/v1/ai-chat/*": "ai-chat-service:8004",
    "/api/v1/reports/*": "api-gateway:8000",  # 本地处理
    "/api/v1/admin/data-management/*": "api-gateway:8000"  # 管理接口
}
```

### 统一响应格式

```python
# 成功响应格式
{
    "success": true,
    "data": {},
    "message": "操作成功",
    "timestamp": "2024-09-20T10:30:00Z",
    "request_id": "uuid-string"
}

# 错误响应格式
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求参数验证失败",
        "details": {},
        "field_errors": []
    },
    "timestamp": "2024-09-20T10:30:00Z",
    "request_id": "uuid-string"
}
```

## 📁 数据上传和管理接口

### 1. 文件上传接口

#### POST /api/v1/data-management/upload
```python
# 请求头
Authorization: Bearer {jwt_token}
Content-Type: multipart/form-data

# 请求参数
{
    "file": "文件对象",  # 必需，支持CSV、Excel、JSON、Parquet
    "name": "数据源名称",  # 可选，默认使用文件名
    "description": "数据源描述",  # 可选
    "auto_analyze": true,  # 可选，是否自动开始质量分析
    "tags": ["标签1", "标签2"]  # 可选，数据源标签
}

# 响应数据
{
    "data": {
        "data_source_id": "uuid-string",
        "upload_id": "uuid-string",
        "name": "sales_data_2024.csv",
        "file_size": 1048576,
        "file_type": "csv",
        "upload_status": "processing",
        "processing_progress": 0,
        "estimated_completion_time": "2024-09-20T10:32:00Z",
        "upload_url": "/api/v1/data-management/upload/{upload_id}/chunks"  # 大文件分块上传URL
    }
}
```

#### POST /api/v1/data-management/upload/{upload_id}/chunks
```python
# 大文件分块上传
# 请求头
Authorization: Bearer {jwt_token}
Content-Type: application/octet-stream
X-Chunk-Number: 1
X-Total-Chunks: 10
X-Chunk-Size: 8388608

# 请求体：文件块二进制数据

# 响应数据
{
    "data": {
        "chunk_number": 1,
        "total_chunks": 10,
        "uploaded_chunks": 1,
        "progress_percentage": 10,
        "next_chunk_url": "/api/v1/data-management/upload/{upload_id}/chunks",
        "is_complete": false
    }
}
```

### 2. 数据源预览接口

#### GET /api/v1/data-management/preview/{data_source_id}
```python
# 查询参数
?rows=10&columns=name,value,date&sample_strategy=random

# 响应数据
{
    "data": {
        "data_source_id": "uuid-string",
        "preview_data": {
            "columns": [
                {"name": "id", "type": "integer", "nullable": false},
                {"name": "name", "type": "string", "nullable": true},
                {"name": "value", "type": "float", "nullable": false},
                {"name": "created_at", "type": "datetime", "nullable": false}
            ],
            "rows": [
                {"id": 1, "name": "Product A", "value": 99.99, "created_at": "2024-01-01T00:00:00Z"},
                {"id": 2, "name": "Product B", "value": 149.99, "created_at": "2024-01-02T00:00:00Z"}
            ],
            "total_rows": 1000,
            "total_columns": 4,
            "sample_size": 10
        },
        "data_profile": {
            "file_size": 1048576,
            "row_count": 1000,
            "column_count": 4,
            "data_types": {"integer": 1, "string": 1, "float": 1, "datetime": 1},
            "null_counts": {"name": 50},
            "duplicates_count": 5
        }
    }
}
```

### 3. 数据源管理接口

#### GET /api/v1/data-management/sources
```python
# 查询参数
?page=1&size=20&sort=created_at&order=desc&status=completed&file_type=csv

# 响应数据
{
    "data": {
        "items": [
            {
                "id": "uuid-string",
                "name": "sales_data_2024.csv",
                "description": "2024年销售数据",
                "file_type": "csv",
                "file_size": 1048576,
                "row_count": 1000,
                "column_count": 4,
                "upload_status": "completed",
                "latest_quality_score": 85.5,
                "quality_grade": "B",
                "created_at": "2024-09-20T10:00:00Z",
                "last_analyzed_at": "2024-09-20T10:15:00Z",
                "tags": ["sales", "2024"]
            }
        ],
        "pagination": {
            "page": 1,
            "size": 20,
            "total": 150,
            "pages": 8,
            "has_next": true,
            "has_prev": false
        }
    }
}
```

#### DELETE /api/v1/data-management/sources/{data_source_id}
```python
# 响应数据
{
    "data": {
        "deleted_data_source_id": "uuid-string",
        "deleted_at": "2024-09-20T10:30:00Z",
        "cleanup_tasks": [
            "removed_file_storage",
            "deleted_quality_assessments",
            "archived_ai_analysis_results"
        ]
    }
}
```

## 🔍 质量分析接口

### 1. 启动质量分析

#### POST /api/v1/quality-analysis/start
```python
# 请求参数
{
    "data_source_id": "uuid-string",
    "analysis_type": "comprehensive",  # "quick", "comprehensive", "custom"
    "dimensions": ["completeness", "consistency", "accuracy", "timeliness"],  # 可选，自定义分析维度
    "quality_thresholds": {  # 可选，自定义质量阈值
        "excellent": 90,
        "good": 75,
        "fair": 60,
        "poor": 0
    },
    "generate_ai_insights": true,  # 可选，是否生成AI洞察
    "notification_webhook": "https://your-domain.com/webhook"  # 可选，完成后回调
}

# 响应数据
{
    "data": {
        "analysis_id": "uuid-string",
        "data_source_id": "uuid-string",
        "analysis_type": "comprehensive",
        "status": "running",
        "estimated_duration": 25,  # 预估分析时间(秒)
        "progress_url": "/api/v1/quality-analysis/progress/{analysis_id}",
        "result_url": "/api/v1/quality-analysis/results/{analysis_id}",
        "started_at": "2024-09-20T10:30:00Z"
    }
}
```

### 2. 查询分析进度

#### GET /api/v1/quality-analysis/progress/{analysis_id}
```python
# 响应数据
{
    "data": {
        "analysis_id": "uuid-string",
        "status": "running",  # "pending", "running", "completed", "failed"
        "overall_progress": 65,  # 0-100
        "current_step": "分析数据一致性",
        "step_progress": {
            "completeness": {"status": "completed", "score": 92.5, "duration": 3},
            "consistency": {"status": "running", "progress": 80},
            "accuracy": {"status": "pending"},
            "timeliness": {"status": "pending"}
        },
        "estimated_remaining_time": 10,  # 剩余时间(秒)
        "error_message": null
    }
}
```

### 3. 获取分析结果

#### GET /api/v1/quality-analysis/results/{analysis_id}
```python
# 响应数据
{
    "data": {
        "analysis_id": "uuid-string",
        "data_source_id": "uuid-string",
        "analysis_status": "completed",
        "analysis_duration": 28,  # 实际分析耗时(秒)

        # 质量评分
        "quality_scores": {
            "completeness": {
                "score": 92.5,
                "grade": "A",
                "details": {
                    "total_fields": 4,
                    "complete_fields": 4,
                    "missing_values": 50,
                    "completeness_rate": 0.95
                }
            },
            "consistency": {
                "score": 78.0,
                "grade": "B",
                "details": {
                    "format_consistency": 0.85,
                    "data_type_consistency": 0.90,
                    "value_range_consistency": 0.75
                }
            },
            "accuracy": {
                "score": 85.0,
                "grade": "B",
                "details": {
                    "outlier_count": 12,
                    "pattern_violations": 3,
                    "accuracy_rate": 0.85
                }
            },
            "timeliness": {
                "score": 90.0,
                "grade": "A",
                "details": {
                    "data_freshness": 0.95,
                    "update_frequency_adherence": 0.85
                }
            }
        },

        # 综合评分
        "overall_quality": {
            "score": 86.4,
            "grade": "B",
            "improvement_potential": 13.6
        },

        # 改进建议
        "improvement_suggestions": [
            {
                "dimension": "consistency",
                "priority": "high",
                "suggestion": "标准化日期格式，统一使用ISO 8601格式",
                "estimated_impact": 8.5
            },
            {
                "dimension": "accuracy",
                "priority": "medium",
                "suggestion": "检查并修复12个异常值",
                "estimated_impact": 5.2
            }
        ],

        # 分析时间戳
        "completed_at": "2024-09-20T10:30:28Z"
    }
}
```

### 4. 历史评分趋势

#### GET /api/v1/quality-analysis/trend/{data_source_id}
```python
# 查询参数
?period=30d&granularity=daily&dimensions=completeness,overall

# 响应数据
{
    "data": {
        "data_source_id": "uuid-string",
        "period": "30d",
        "granularity": "daily",
        "trend_data": [
            {
                "date": "2024-09-01",
                "overall_score": 82.3,
                "completeness": 90.0,
                "consistency": 75.5,
                "accuracy": 83.2,
                "timeliness": 88.5,
                "change_from_previous": 2.1
            },
            {
                "date": "2024-09-02",
                "overall_score": 84.1,
                "completeness": 91.2,
                "consistency": 77.0,
                "accuracy": 84.0,
                "timeliness": 88.2,
                "change_from_previous": 1.8
            }
        ],
        "summary": {
            "trend_direction": "improving",  # "improving", "declining", "stable"
            "average_score": 83.7,
            "best_score": 86.4,
            "worst_score": 79.8,
            "total_analyses": 15
        }
    }
}
```

## 🤖 AI分析和对话接口

### 1. 创建AI对话会话

#### POST /api/v1/ai-chat/sessions
```python
# 请求参数
{
    "data_source_id": "uuid-string",  # 可选，关联特定数据源
    "analysis_id": "uuid-string",  # 可选，基于特定分析结果
    "session_type": "analysis_specific",  # "general", "analysis_specific", "quality_focused"
    "session_title": "Sales Data Analysis Chat",  # 可选
    "initial_context": {  # 可选，初始上下文
        "user_intent": "数据质量分析",
        "focus_areas": ["异常值检测", "趋势分析"]
    }
}

# 响应数据
{
    "data": {
        "session_id": "uuid-string",
        "session_title": "Sales Data Analysis Chat",
        "session_type": "analysis_specific",
        "status": "active",
        "data_source_id": "uuid-string",
        "analysis_id": "uuid-string",
        "expires_at": "2024-09-21T10:30:00Z",
        "created_at": "2024-09-20T10:30:00Z",
        "ai_greeting": "您好！我是您的数据分析助手。我已经了解了您的销售数据质量分析结果，有什么问题想要讨论吗？"
    }
}
```

### 2. 发送AI对话消息

#### POST /api/v1/ai-chat/sessions/{session_id}/messages
```python
# 请求参数
{
    "message": "这个数据集的主要质量问题是什么？如何改进？",
    "message_type": "user",  # "user", "system"
    "context": {  # 可选，额外上下文
        "current_view": "quality_dashboard",
        "selected_dimensions": ["completeness", "accuracy"]
    },
    "stream": false  # 可选，是否流式响应
}

# 响应数据
{
    "data": {
        "message_id": "uuid-string",
        "session_id": "uuid-string",
        "ai_response": {
            "message": "根据您的数据质量分析结果，我发现以下主要问题：\n\n1. **一致性问题 (78分)**：\n   - 日期格式不统一，建议标准化为ISO 8601格式\n   - 部分字段存在格式差异\n\n2. **准确性问题 (85分)**：\n   - 检测到12个异常值需要人工验证\n   - 3个模式违规需要修正\n\n**改进建议**：\n1. 数据清洗：统一日期格式可提升8.5分\n2. 异常值处理：修复异常值可提升5.2分\n3. 数据验证：建立数据质量检查规则\n\n需要我详细解释某个维度的问题吗？",
            "response_type": "analysis_insights",
            "confidence_score": 92.5,
            "generated_at": "2024-09-20T10:30:05Z"
        },
        "token_usage": {
            "prompt_tokens": 1200,
            "completion_tokens": 450,
            "total_tokens": 1650
        },
        "response_time_ms": 2800
    }
}
```

### 3. 获取对话历史

#### GET /api/v1/ai-chat/sessions/{session_id}/history
```python
# 查询参数
?page=1&size=20&message_type=all&since=2024-09-20T10:00:00Z

# 响应数据
{
    "data": {
        "session_id": "uuid-string",
        "messages": [
            {
                "message_id": "uuid-string",
                "message_type": "system",
                "content": "会话开始，AI助手已准备就绪",
                "created_at": "2024-09-20T10:30:00Z"
            },
            {
                "message_id": "uuid-string",
                "message_type": "user",
                "content": "这个数据集的主要质量问题是什么？",
                "created_at": "2024-09-20T10:30:02Z"
            },
            {
                "message_id": "uuid-string",
                "message_type": "assistant",
                "content": "根据您的数据质量分析结果...",
                "ai_metadata": {
                    "model": "gpt-3.5-turbo",
                    "confidence_score": 92.5,
                    "response_time_ms": 2800
                },
                "created_at": "2024-09-20T10:30:05Z"
            }
        ],
        "pagination": {
            "page": 1,
            "size": 20,
            "total": 12,
            "has_next": false
        },
        "session_stats": {
            "total_messages": 12,
            "user_messages": 6,
            "ai_responses": 5,
            "total_tokens_used": 8500
        }
    }
}
```

### 4. AI洞察生成

#### POST /api/v1/ai-chat/generate-insights
```python
# 请求参数
{
    "analysis_id": "uuid-string",
    "insight_type": "comprehensive",  # "quick", "comprehensive", "specific"
    "focus_areas": [  # 可选，指定关注领域
        "data_quality_issues",
        "improvement_recommendations",
        "trend_analysis",
        "anomaly_detection"
    ],
    "output_format": "structured"  # "narrative", "structured", "bullet_points"
}

# 响应数据
{
    "data": {
        "insight_id": "uuid-string",
        "analysis_id": "uuid-string",
        "insights": {
            "executive_summary": "您的数据集整体质量为B级(86.4分)，主要改进空间在数据一致性方面。",
            "key_findings": [
                {
                    "category": "data_quality_issues",
                    "findings": [
                        "数据完整性优秀(92.5分)，仅有5%的缺失值",
                        "一致性有待改进(78分)，主要是格式不统一问题",
                        "准确性良好(85分)，但存在12个需要验证的异常值"
                    ]
                },
                {
                    "category": "improvement_recommendations",
                    "findings": [
                        "优先处理日期格式标准化，预计可提升8.5分",
                        "建立数据验证规则，防止格式不一致",
                        "实施异常值检测流程，提高数据准确性"
                    ]
                }
            ],
            "action_items": [
                {
                    "priority": "high",
                    "action": "标准化日期格式",
                    "estimated_impact": 8.5,
                    "effort": "medium"
                },
                {
                    "priority": "medium",
                    "action": "处理异常值",
                    "estimated_impact": 5.2,
                    "effort": "high"
                }
            ]
        },
        "generation_metadata": {
            "model": "gpt-3.5-turbo",
            "confidence_score": 94.2,
            "generation_time_ms": 3200,
            "token_usage": {
                "prompt_tokens": 2000,
                "completion_tokens": 800,
                "total_tokens": 2800
            }
        },
        "generated_at": "2024-09-20T10:30:00Z"
    }
}
```

## 📊 报告和导出接口

### 1. 生成质量报告

#### POST /api/v1/reports/generate
```python
# 请求参数
{
    "report_type": "quality_analysis",  # "quality_analysis", "trend_report", "comprehensive"
    "data_source_ids": ["uuid-1", "uuid-2"],  # 可选，特定数据源
    "analysis_ids": ["uuid-a", "uuid-b"],  # 可选，特定分析结果
    "date_range": {  # 可选，时间范围
        "start_date": "2024-09-01",
        "end_date": "2024-09-20"
    },
    "format": "pdf",  # "pdf", "excel", "json", "html"
    "include_ai_insights": true,
    "template": "standard",  # "standard", "executive", "detailed"
    "language": "zh-CN"
}

# 响应数据
{
    "data": {
        "report_id": "uuid-string",
        "report_type": "quality_analysis",
        "status": "generating",  # "pending", "generating", "completed", "failed"
        "progress": 0,
        "estimated_completion_time": "2024-09-20T10:32:00Z",
        "download_url": null,  # 完成后提供下载链接
        "preview_url": "/api/v1/reports/{report_id}/preview"
    }
}
```

### 2. 查询报告状态

#### GET /api/v1/reports/{report_id}/status
```python
# 响应数据
{
    "data": {
        "report_id": "uuid-string",
        "status": "completed",
        "progress": 100,
        "file_info": {
            "filename": "quality_analysis_report_20240920.pdf",
            "file_size": 2048576,
            "format": "pdf",
            "page_count": 15
        },
        "download_url": "/api/v1/reports/{report_id}/download",
        "expires_at": "2024-09-27T10:30:00Z",  # 下载链接过期时间
        "generated_at": "2024-09-20T10:32:00Z"
    }
}
```

### 3. 数据导出接口

#### POST /api/v1/data-management/export
```python
# 请求参数
{
    "data_source_id": "uuid-string",
    "export_type": "processed_data",  # "raw_data", "processed_data", "quality_results"
    "format": "excel",  # "csv", "excel", "json", "parquet"
    "include_metadata": true,
    "include_quality_scores": true,
    "include_ai_insights": false,
    "filters": {  # 可选，数据过滤
        "columns": ["id", "name", "value"],
        "date_range": {
            "column": "created_at",
            "start": "2024-09-01",
            "end": "2024-09-20"
        },
        "quality_threshold": 80  # 只导出质量分数>=80的记录
    }
}

# 响应数据
{
    "data": {
        "export_id": "uuid-string",
        "data_source_id": "uuid-string",
        "status": "processing",
        "progress": 25,
        "estimated_records": 1000,
        "processed_records": 250,
        "download_url": null,
        "estimated_completion_time": "2024-09-20T10:31:30Z"
    }
}
```

## 🔧 管理和监控接口

### 1. 系统健康检查

#### GET /api/v1/admin/health/detailed
```python
# 响应数据
{
    "data": {
        "overall_status": "healthy",  # "healthy", "degraded", "unhealthy"
        "services": {
            "api_gateway": {"status": "healthy", "response_time_ms": 15},
            "quality_service": {"status": "healthy", "response_time_ms": 45},
            "ai_chat_service": {"status": "healthy", "response_time_ms": 120},
            "file_processing_service": {"status": "healthy", "response_time_ms": 30}
        },
        "dependencies": {
            "postgresql": {"status": "healthy", "connection_pool": "85% used"},
            "redis": {"status": "healthy", "memory_usage": "45%"},
            "openai_api": {"status": "healthy", "rate_limit_remaining": 450}
        },
        "metrics": {
            "active_analyses": 12,
            "active_chat_sessions": 8,
            "queue_length": 3,
            "avg_response_time_ms": 250
        },
        "checked_at": "2024-09-20T10:30:00Z"
    }
}
```

### 2. 使用统计接口

#### GET /api/v1/admin/stats/usage
```python
# 查询参数
?period=24h&granularity=hourly&metrics=all

# 响应数据
{
    "data": {
        "period": "24h",
        "usage_stats": {
            "api_requests": {
                "total": 15420,
                "by_endpoint": {
                    "/api/v1/quality-analysis/start": 245,
                    "/api/v1/ai-chat/sessions": 180,
                    "/api/v1/data-management/upload": 95
                }
            },
            "data_processing": {
                "files_uploaded": 95,
                "total_data_size_mb": 2400,
                "analyses_completed": 240,
                "avg_analysis_time_seconds": 25
            },
            "ai_usage": {
                "chat_sessions": 180,
                "total_tokens": 450000,
                "avg_response_time_ms": 2800,
                "cost_usd": 12.50
            }
        },
        "performance_metrics": {
            "avg_api_response_time_ms": 180,
            "error_rate_percentage": 0.8,
            "cache_hit_rate_percentage": 85.2
        }
    }
}
```

## 🔐 认证和权限接口

### 1. API密钥管理

#### POST /api/v1/admin/api-keys
```python
# 请求参数
{
    "name": "数据分析工具集成",
    "permissions": [
        "data_management:read",
        "quality_analysis:write",
        "ai_chat:read"
    ],
    "rate_limits": {
        "requests_per_minute": 100,
        "requests_per_hour": 5000
    },
    "expires_at": "2025-09-20T10:30:00Z"  # 可选
}

# 响应数据
{
    "data": {
        "api_key_id": "uuid-string",
        "api_key": "dm_live_sk_***************",  # 仅创建时返回完整密钥
        "name": "数据分析工具集成",
        "permissions": ["data_management:read", "quality_analysis:write", "ai_chat:read"],
        "rate_limits": {
            "requests_per_minute": 100,
            "requests_per_hour": 5000
        },
        "status": "active",
        "created_at": "2024-09-20T10:30:00Z",
        "expires_at": "2025-09-20T10:30:00Z"
    }
}
```

## 📈 WebSocket实时更新接口

### 连接质量分析进度WebSocket

```javascript
// WebSocket连接
const ws = new WebSocket('ws://localhost:8000/ws/quality-analysis/{analysis_id}');

// 接收实时进度更新
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Progress update:', data);
    /*
    {
        "event": "progress_update",
        "analysis_id": "uuid-string",
        "progress": 75,
        "current_step": "分析数据准确性",
        "step_details": {
            "completeness": {"status": "completed", "score": 92.5},
            "consistency": {"status": "completed", "score": 78.0},
            "accuracy": {"status": "running", "progress": 50},
            "timeliness": {"status": "pending"}
        },
        "timestamp": "2024-09-20T10:30:15Z"
    }
    */
};

// 分析完成通知
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.event === 'analysis_completed') {
        console.log('Analysis completed:', data);
        /*
        {
            "event": "analysis_completed",
            "analysis_id": "uuid-string",
            "overall_score": 86.4,
            "quality_grade": "B",
            "duration_seconds": 28,
            "ai_insights_available": true,
            "result_url": "/api/v1/quality-analysis/results/{analysis_id}",
            "timestamp": "2024-09-20T10:30:28Z"
        }
        */
    }
};
```

## 🚀 API性能规范

### 响应时间目标

```python
API_PERFORMANCE_TARGETS = {
    # 实时交互接口
    "GET /api/v1/quality-analysis/progress/*": "< 100ms",
    "POST /api/v1/ai-chat/sessions/*/messages": "< 3000ms",
    "GET /api/v1/data-management/preview/*": "< 200ms",

    # 批量操作接口
    "POST /api/v1/quality-analysis/start": "< 500ms",
    "POST /api/v1/data-management/upload": "< 1000ms",
    "GET /api/v1/quality-analysis/results/*": "< 300ms",

    # 报告生成接口
    "POST /api/v1/reports/generate": "< 2000ms",
    "GET /api/v1/reports/*/download": "< 5000ms"
}
```

### 限流策略

```python
RATE_LIMITS = {
    # 用户级别限制
    "authenticated_user": {
        "requests_per_minute": 200,
        "requests_per_hour": 10000,
        "concurrent_analyses": 5,
        "concurrent_chat_sessions": 3
    },

    # 接口级别限制
    "quality_analysis_start": "10/minute",
    "ai_chat_messages": "30/minute",
    "file_upload": "5/minute",
    "report_generation": "3/minute"
}
```

这个API接口规范为数据管理功能提供了完整、标准化的后端接口设计，确保前后端的高效集成和优秀的用户体验。