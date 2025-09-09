# 分布式Python后端部署指南

## 🏗️ 项目架构概览

这是一个可扩展的分布式Python后端系统，支持多项目隔离部署，专为AI数据分析平台设计。

### 核心特性

- **多项目隔离**: 支持独立的项目实例，避免资源冲突
- **微服务架构**: API网关、数据服务、AI服务独立部署
- **容器化部署**: 完整的Docker + Docker Compose支持
- **AI集成**: OpenAI API、Ray分布式计算集成
- **可观测性**: Prometheus监控、结构化日志、健康检查
- **生产就绪**: 完整的安全、限流、错误处理机制

### 端口分配策略

- **项目1 (backend-pro1)**: 端口8000-8099
  - API网关: 8000
  - 数据服务: 8001
  - AI服务: 8002
  - PostgreSQL: 5432
  - Redis: 6379
  - MinIO: 9000/9001
  - Prometheus: 9090

- **项目2 (backend-pro2)**: 端口8100-8199
  - API网关: 8100
  - 数据服务: 8101
  - AI服务: 8102
  - PostgreSQL: 5433
  - Redis: 6380
  - MinIO: 9002/9003
  - Prometheus: 9091

## 🚀 快速开始

### 1. 环境准备

```bash
# 确保已安装Docker和Docker Compose
docker --version
docker-compose --version

# 初始化开发环境
cd backend
chmod +x scripts/*.sh
./scripts/setup.sh
```

### 2. 配置环境变量

编辑项目的`.env`文件：

```bash
# 项目1
vim backend-pro1/.env

# 项目2  
vim backend-pro2/.env
```

**重要配置项**：
- `OPENAI_API_KEY`: OpenAI API密钥
- `SECRET_KEY`: JWT加密密钥（已自动生成）
- `DATABASE_URL`: 数据库连接字符串

### 3. 启动服务

```bash
# 启动开发环境（交互式选择）
./scripts/start-dev.sh

# 或直接启动特定项目
cd backend-pro1
docker-compose up -d

cd ../backend-pro2
docker-compose up -d
```

### 4. 验证部署

```bash
# 查看服务状态
./scripts/status.sh

# 检查API网关健康状态
curl http://localhost:8000/health
curl http://localhost:8100/health
```

## 📋 服务端点

### 项目1 (backend-pro1)
- **API网关**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **数据服务**: http://localhost:8001/docs
- **AI服务**: http://localhost:8002/docs
- **Prometheus**: http://localhost:9090
- **MinIO控制台**: http://localhost:9001

### 项目2 (backend-pro2)
- **API网关**: http://localhost:8100
- **API文档**: http://localhost:8100/docs
- **数据服务**: http://localhost:8101/docs
- **AI服务**: http://localhost:8102/docs
- **Prometheus**: http://localhost:9091
- **MinIO控制台**: http://localhost:9003

## 🔧 管理命令

```bash
# 查看服务状态
./scripts/status.sh

# 停止服务
./scripts/stop-dev.sh

# 查看日志
docker-compose logs -f [service_name]

# 进入容器
docker-compose exec api-gateway bash

# 重启特定服务
docker-compose restart ai-service

# 完全清理（包括数据卷）
./scripts/stop-dev.sh  # 选择选项4
```

## 📊 监控和日志

### Prometheus监控
- 项目1: http://localhost:9090
- 项目2: http://localhost:9091

### 日志查看
```bash
# API网关日志
docker-compose logs -f api-gateway

# 数据服务日志
docker-compose logs -f data-service

# AI服务日志
docker-compose logs -f ai-service

# 所有服务日志
docker-compose logs -f
```

### 健康检查
```bash
# 基本健康检查
curl http://localhost:8000/health

# 详细健康检查
curl http://localhost:8000/health/detailed

# 就绪检查（Kubernetes使用）
curl http://localhost:8000/ready
```

## 🧪 API测试

### 用户注册
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 用户登录
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

### 获取用户信息
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🔒 安全配置

### JWT令牌配置
- 访问令牌过期时间: 30分钟
- 刷新令牌过期时间: 7天
- 算法: HS256

### 限流配置
- 默认限制: 100请求/分钟
- 基于IP地址或用户ID
- Redis分布式限流

### CORS配置
- 开发环境: 允许所有来源
- 生产环境: 严格的域名白名单

## 📈 扩展和优化

### 水平扩展
```bash
# 扩展API网关实例
docker-compose up -d --scale api-gateway=3

# 扩展AI服务实例
docker-compose up -d --scale ai-service=2
```

### 性能优化
1. **数据库连接池**: 已配置最优的连接池大小
2. **Redis缓存**: 用户会话和频繁查询缓存
3. **异步处理**: 所有IO操作使用异步模式
4. **资源监控**: Prometheus指标收集

### 生产环境配置
1. 修改`.env`中的`DEBUG=false`
2. 设置强密码和密钥
3. 配置HTTPS和域名
4. 启用备份和监控告警
5. 配置日志轮转

## 🐛 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   lsof -i :8000
   # 或使用不同端口
   ```

2. **数据库连接失败**
   ```bash
   # 检查PostgreSQL服务状态
   docker-compose ps postgres
   # 查看数据库日志
   docker-compose logs postgres
   ```

3. **Redis连接超时**
   ```bash
   # 检查Redis服务
   docker-compose exec redis redis-cli ping
   ```

4. **服务启动慢**
   ```bash
   # 增加健康检查超时时间
   # 或查看具体服务日志
   docker-compose logs -f [service_name]
   ```

### 重置环境
```bash
# 完全重置（删除所有数据）
./scripts/stop-dev.sh  # 选择选项4
./scripts/setup.sh     # 重新初始化
```

## 📚 开发指南

### 添加新的API端点
1. 在对应服务的`routers/`目录下创建路由文件
2. 在`main.py`中注册路由
3. 添加相应的数据模型和业务逻辑
4. 编写单元测试

### 添加新的中间件
1. 在`shared/middleware/`中创建中间件文件
2. 在`main.py`中注册中间件
3. 确保中间件顺序正确

### 数据库迁移
1. 修改`scripts/init-db.sql`
2. 重启数据库服务应用更改
3. 或使用Alembic进行版本管理

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 编写测试
4. 确保代码风格一致
5. 提交PR

---

🎉 **恭喜！你的分布式Python后端架构已经构建完成并可以投入使用了！**