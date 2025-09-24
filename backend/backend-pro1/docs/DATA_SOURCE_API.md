# 数据源连接API文档

## 概述

数据源连接后端API提供完整的文件上传、数据预览、数据管理功能，支持CSV、JSON、Excel、Parquet等多种数据格式。

## 认证

所有API端点都需要JWT Bearer Token认证：

```
Authorization: Bearer <your_jwt_token>
```

## API端点

### 1. 文件上传 (`/upload`)

#### 1.1 创建上传会话
```http
POST /upload/session
Content-Type: application/json

{
  "filename": "data.csv",
  "file_size": 1024000,
  "project_id": 1,
  "chunk_size": 1048576
}
```

**响应:**
```json
{
  "id": "uuid-session-id",
  "user_id": 1,
  "project_id": 1,
  "filename": "data.csv",
  "file_size": 1024000,
  "uploaded_size": 0,
  "chunk_size": 1048576,
  "total_chunks": 1,
  "uploaded_chunks": 0,
  "status": "uploading",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-01-02T00:00:00Z"
}
```

#### 1.2 直接文件上传（小文件）
```http
POST /upload/file
Content-Type: multipart/form-data

file: <file_content>
project_id: 1
```

**响应:**
```json
{
  "success": true,
  "session_id": "uuid-session-id",
  "message": "文件上传成功，正在处理中"
}
```

#### 1.3 分块上传
```http
POST /upload/chunk/{session_id}
Content-Type: multipart/form-data

chunk_index: 0
chunk: <chunk_content>
```

**响应:**
```json
{
  "success": true,
  "chunk_index": 0,
  "uploaded_chunks": 1,
  "total_chunks": 5,
  "progress_percentage": 20.0,
  "is_complete": false,
  "message": "分块上传成功"
}
```

#### 1.4 查询上传进度
```http
GET /upload/progress/{session_id}
```

**响应:**
```json
{
  "id": "uuid-session-id",
  "status": "uploading",
  "uploaded_chunks": 3,
  "total_chunks": 5,
  "progress_percentage": 60.0,
  "error_message": null
}
```

#### 1.5 取消上传
```http
DELETE /upload/session/{session_id}
```

**响应:**
```json
{
  "message": "上传已取消"
}
```

### 2. 数据预览 (`/preview`)

#### 2.1 获取数据集预览
```http
GET /preview/datasets/{dataset_id}/preview
```

**响应:**
```json
{
  "dataset_id": 1,
  "rows_count": 1000,
  "columns_count": 8,
  "columns": [
    {
      "column_name": "id",
      "column_index": 0,
      "data_type": "number",
      "is_nullable": false,
      "unique_count": 1000,
      "missing_count": 0,
      "min_value": "1",
      "max_value": "1000",
      "avg_value": 500.5,
      "sample_values": ["1", "2", "3"]
    }
  ],
  "sample_data": [
    {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
    {"id": 2, "name": "李四", "email": "lisi@example.com"}
  ],
  "data_types": {
    "id": "number",
    "name": "string",
    "email": "string"
  },
  "missing_values_summary": {
    "id": 0,
    "name": 0,
    "email": 1
  },
  "memory_usage": 1024000
}
```

#### 2.2 获取数据集列表
```http
GET /preview/datasets?project_id=1&status=ready&page=1&size=20
```

**响应:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "用户数据",
      "type": "csv",
      "project_id": 1,
      "file_size": 1024000,
      "rows_count": 1000,
      "columns_count": 8,
      "status": "ready",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

#### 2.3 获取数据质量检查结果
```http
GET /preview/datasets/{dataset_id}/quality
```

**响应:**
```json
[
  {
    "id": 1,
    "dataset_id": 1,
    "check_type": "missing_values",
    "column_name": "email",
    "severity": "warning",
    "message": "列 \"email\" 有 10 个缺失值 (1.0%)",
    "details": {
      "missing_count": 10,
      "total_count": 1000,
      "percentage": 1.0
    },
    "affected_rows": 10,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

#### 2.4 触发数据重新分析
```http
POST /preview/datasets/{dataset_id}/analyze
```

**响应:**
```json
{
  "message": "数据分析任务已启动",
  "dataset_id": 1
}
```

### 3. 数据管理 (`/manage`)

#### 3.1 获取单个数据集
```http
GET /manage/datasets/{dataset_id}
```

**响应:**
```json
{
  "id": 1,
  "name": "用户数据",
  "type": "csv",
  "project_id": 1,
  "file_path": "/tmp/uploads/data.csv",
  "file_size": 1024000,
  "rows_count": 1000,
  "columns_count": 8,
  "status": "ready",
  "original_filename": "users.csv",
  "file_hash": "sha256hash",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### 3.2 更新数据集
```http
PUT /manage/datasets/{dataset_id}
Content-Type: application/json

{
  "name": "新的数据集名称",
  "description": "更新的描述",
  "status": "ready"
}
```

#### 3.3 删除数据集
```http
DELETE /manage/datasets/{dataset_id}
```

**响应:**
```json
{
  "message": "数据集删除成功",
  "dataset_id": 1
}
```

#### 3.4 获取数据分析统计
```http
GET /manage/analytics?project_id=1
```

**响应:**
```json
{
  "total_datasets": 10,
  "datasets_by_type": {
    "csv": 6,
    "json": 3,
    "excel": 1
  },
  "datasets_by_status": {
    "ready": 8,
    "processing": 1,
    "error": 1
  },
  "total_size": 10485760,
  "total_rows": 50000,
  "recent_uploads": [...],
  "quality_issues": 5
}
```

#### 3.5 获取项目数据集摘要
```http
GET /manage/projects/{project_id}/datasets/summary
```

**响应:**
```json
{
  "project_id": 1,
  "datasets_summary": {
    "total_count": 10,
    "ready_count": 8,
    "processing_count": 1,
    "error_count": 1,
    "total_size": 10485760,
    "total_rows": 50000
  }
}
```

## 错误处理

所有API端点都使用标准HTTP状态码：

- `200 OK` - 请求成功
- `201 Created` - 资源创建成功
- `400 Bad Request` - 请求参数错误
- `401 Unauthorized` - 未授权访问
- `403 Forbidden` - 权限不足
- `404 Not Found` - 资源不存在
- `413 Payload Too Large` - 文件过大
- `422 Unprocessable Entity` - 数据验证错误
- `500 Internal Server Error` - 服务器内部错误

**错误响应格式:**
```json
{
  "detail": "错误描述信息"
}
```

## 支持的文件格式

| 格式 | 扩展名 | MIME类型 | 最大大小 |
|------|--------|----------|----------|
| CSV | .csv | text/csv | 100MB |
| JSON | .json | application/json | 100MB |
| Excel | .xlsx, .xls | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | 100MB |
| Parquet | .parquet | application/octet-stream | 100MB |

## 使用示例

### Python客户端示例

```python
import requests
import json

# 配置
API_BASE = "http://localhost:8001"
headers = {"Authorization": "Bearer your_jwt_token"}

# 1. 创建上传会话
session_data = {
    "filename": "data.csv",
    "file_size": 1024000,
    "project_id": 1
}

response = requests.post(
    f"{API_BASE}/upload/session",
    json=session_data,
    headers=headers
)
session = response.json()

# 2. 上传文件
with open("data.csv", "rb") as f:
    files = {"file": f}
    data = {"project_id": 1}

    response = requests.post(
        f"{API_BASE}/upload/file",
        files=files,
        data=data,
        headers=headers
    )

upload_result = response.json()
print(f"上传结果: {upload_result}")

# 3. 获取数据预览
dataset_id = 1
response = requests.get(
    f"{API_BASE}/preview/datasets/{dataset_id}/preview",
    headers=headers
)
preview = response.json()
print(f"数据预览: {preview}")
```

### JavaScript客户端示例

```javascript
const API_BASE = "http://localhost:8001";
const token = "your_jwt_token";

// 上传文件
async function uploadFile(file, projectId) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', projectId);

    const response = await fetch(`${API_BASE}/upload/file`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });

    return await response.json();
}

// 获取数据预览
async function getDataPreview(datasetId) {
    const response = await fetch(`${API_BASE}/preview/datasets/${datasetId}/preview`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    return await response.json();
}
```

## 性能考虑

1. **文件大小限制**: 单个文件最大100MB
2. **分块上传**: 大文件自动分块，默认1MB每块
3. **预览数据缓存**: 预览结果缓存到数据库，避免重复计算
4. **异步处理**: 文件处理在后台异步执行
5. **连接池**: 数据库连接池优化并发性能

## 安全特性

1. **JWT认证**: 所有端点都需要有效的JWT token
2. **权限控制**: 用户只能访问自己的项目和数据集
3. **文件验证**: 严格的文件类型和大小验证
4. **SQL注入防护**: 使用参数化查询
5. **上传限制**: 防止恶意文件上传

## 监控和日志

所有API调用都会记录详细的结构化日志，包括：

- 请求ID
- 用户ID
- 操作类型
- 执行时间
- 错误信息

可通过Prometheus指标监控API性能。