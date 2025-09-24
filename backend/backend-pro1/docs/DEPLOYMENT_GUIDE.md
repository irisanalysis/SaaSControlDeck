# 数据源连接后端部署指南

## Day 1 开发完成 - 部署准备

### 环境要求

- Python 3.11+
- PostgreSQL 15+ (已配置云数据库)
- Redis 7+ (缓存和会话管理)
- 存储空间: 最少10GB (文件上传临时存储)

### 1. 环境配置

#### 1.1 创建环境配置文件

```bash
cd /home/user/studio/backend/backend-pro1
cp .env.example .env
```

#### 1.2 配置环境变量

```bash
# 项目配置
PROJECT_ID=pro1
PROJECT_NAME="SaaS Control Deck"
DEBUG=true

# 服务端口配置
API_GATEWAY_PORT=8000
DATA_SERVICE_PORT=8001
AI_SERVICE_PORT=8002

# 数据库配置 (云数据库)
DATABASE_URL=postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 安全配置
SECRET_KEY=your-super-secret-key-32-chars-minimum
JWT_SECRET_KEY=your-jwt-secret-key-32-chars-minimum
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 文件上传配置
MAX_FILE_SIZE=104857600  # 100MB
UPLOAD_DIR=/tmp/data_uploads
ALLOWED_FILE_TYPES=csv,json,xlsx,xls,parquet

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json

# 开发环境特殊配置
CORS_ORIGINS=["http://localhost:9000", "http://localhost:3000"]
```

### 2. 依赖安装

#### 2.1 安装Python依赖

```bash
# 创建虚拟环境 (可选)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 2.2 验证依赖安装

```bash
python3 -c "
import fastapi
import pandas
import asyncpg
import redis
print('所有依赖安装成功!')
"
```

### 3. 数据库设置

#### 3.1 应用迁移

```bash
# 应用数据源扩展迁移
python3 scripts/apply_migrations.py
```

#### 3.2 验证数据库表

```bash
# 连接数据库验证表结构
PGPASSWORD="dev_pass_2024_secure" psql -h 47.79.87.199 -p 5432 -U saascontrol_dev_user -d saascontrol_dev_pro1 -c "
\dt
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%dataset%';
"
```

#### 3.3 手动验证表结构 (可选)

```sql
-- 检查新增的表
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name IN ('datasets', 'dataset_columns', 'upload_sessions', 'data_quality_checks')
ORDER BY table_name, ordinal_position;
```

### 4. 服务启动

#### 4.1 开发环境启动

```bash
# 启动数据服务
cd data-service
python3 app/main.py

# 或使用uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### 4.2 生产环境启动

```bash
# 使用gunicorn启动
gunicorn app.main:app \
  --bind 0.0.0.0:8001 \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

#### 4.3 Docker启动 (推荐)

```bash
# 构建镜像
docker build -t saas-data-service .

# 启动容器
docker run -d \
  --name saas-data-service \
  --env-file .env \
  -p 8001:8001 \
  -v /tmp/data_uploads:/tmp/data_uploads \
  saas-data-service
```

### 5. 功能验证

#### 5.1 健康检查

```bash
curl http://localhost:8001/health
# 预期响应: {"status": "healthy", "service": "data-service"}
```

#### 5.2 API文档访问

访问自动生成的API文档：
```
http://localhost:8001/docs
```

#### 5.3 运行集成测试

```bash
# 运行API测试脚本
python3 scripts/test_data_apis.py

# 或运行完整测试
bash scripts/quick_test.sh
```

### 6. 性能优化

#### 6.1 数据库连接池

```python
# 在shared/database.py中已配置
pool_size = 10
max_overflow = 20
```

#### 6.2 文件上传优化

```bash
# 创建上传目录并设置权限
mkdir -p /tmp/data_uploads
chmod 755 /tmp/data_uploads
```

#### 6.3 Redis缓存配置

```bash
# 启动Redis (如果未启动)
redis-server

# 验证Redis连接
redis-cli ping
```

### 7. 监控和日志

#### 7.1 日志配置

```python
# 日志输出到控制台和文件
import structlog
logger = structlog.get_logger()
```

#### 7.2 性能监控

```bash
# 检查服务状态
curl http://localhost:8001/health

# 检查数据库连接
curl http://localhost:8001/docs
```

### 8. 安全配置

#### 8.1 JWT配置

确保在生产环境中使用强密钥：

```bash
# 生成安全的JWT密钥
python3 -c "
import secrets
print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))
print('SECRET_KEY=' + secrets.token_urlsafe(32))
"
```

#### 8.2 CORS配置

生产环境中限制CORS来源：

```python
CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]
```

### 9. 容器化部署

#### 9.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8001

CMD ["uvicorn", "data-service.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

#### 9.2 Docker Compose

```yaml
version: '3.8'
services:
  data-service:
    build: .
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./uploads:/tmp/data_uploads
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### 10. 前端集成准备

#### 10.1 API Base URL配置

前端需要配置数据服务API地址：

```javascript
// 开发环境
const DATA_API_BASE = "http://localhost:8001";

// 生产环境
const DATA_API_BASE = "https://api.yourdomain.com/data";
```

#### 10.2 TypeScript类型

```bash
# 复制TypeScript类型定义到前端项目
cp docs/typescript-types.ts ../frontend/src/types/data-source.ts
```

#### 10.3 API客户端示例

```javascript
// 前端API客户端配置
const apiClient = axios.create({
  baseURL: 'http://localhost:8001',
  headers: {
    'Authorization': `Bearer ${authToken}`
  }
});
```

### 11. 故障排除

#### 11.1 常见问题

**问题1: 数据库连接失败**
```bash
# 检查数据库连接
PGPASSWORD="dev_pass_2024_secure" psql -h 47.79.87.199 -p 5432 -U saascontrol_dev_user -d saascontrol_dev_pro1 -c "SELECT 1;"
```

**问题2: 文件上传失败**
```bash
# 检查上传目录权限
ls -la /tmp/data_uploads
chmod 755 /tmp/data_uploads
```

**问题3: Redis连接失败**
```bash
# 启动Redis
sudo systemctl start redis
# 或
redis-server
```

#### 11.2 调试模式

```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python3 data-service/app/main.py
```

### 12. 部署检查清单

- [ ] 环境变量配置完成
- [ ] 数据库迁移应用成功
- [ ] 依赖包安装完成
- [ ] 服务正常启动 (端口8001)
- [ ] 健康检查通过
- [ ] API文档可访问
- [ ] 文件上传目录创建
- [ ] Redis缓存连接正常
- [ ] 集成测试通过
- [ ] TypeScript类型定义复制到前端
- [ ] CORS配置正确
- [ ] 日志输出正常

### 13. 下一步 (Day 2 前端开发)

前端开发团队可以开始工作，已提供：

1. **完整的API文档**: `/docs/DATA_SOURCE_API.md`
2. **TypeScript类型定义**: `/docs/typescript-types.ts`
3. **API端点**: 运行在 `http://localhost:8001`
4. **测试数据**: 通过 `scripts/test_data_apis.py` 创建

### 14. 生产环境额外配置

#### 14.1 负载均衡

```nginx
upstream data_service {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    location /data/ {
        proxy_pass http://data_service/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 14.2 SSL证书

```bash
# 使用Let's Encrypt
certbot --nginx -d api.yourdomain.com
```

#### 14.3 监控配置

```yaml
# Prometheus监控
- job_name: 'data-service'
  static_configs:
    - targets: ['localhost:8001']
```

🎉 **数据源连接后端 Day 1 部署完成！**

现在已经为前端开发提供了稳定、完整的API基础设施。