# SaaS Control Deck - DockerHub部署指南

本指南提供了完整的SaaS Control Deck项目Docker镜像构建、推送和部署解决方案。

## 🚀 快速开始

### 1. 自动化部署（推荐）

使用GitHub Actions自动构建和推送镜像：

```bash
# 触发GitHub Actions构建
git push origin main

# 构建完成后，使用一键部署脚本
./deploy-from-dockerhub.sh -u irisanalysis -t latest
```

### 2. 手动构建部署

如果GitHub Actions失败，使用手动构建脚本：

```bash
# 构建并推送镜像
./scripts/manual-docker-build.sh --push

# 部署镜像
./deploy-from-dockerhub.sh -u irisanalysis -t latest
```

### 3. 验证部署

部署完成后验证服务状态：

```bash
# 基础健康检查
./scripts/verify-deployment.sh

# 详细健康检查
./scripts/verify-deployment.sh --detailed
```

## 📋 问题解决方案

### GitHub Actions构建失败

**已修复的问题：**

1. **前端端口配置错误** ✅
   - 修复：Dockerfile端口从9000改为3000
   - docker-compose.dockerhub.yml正确映射9000:3000

2. **多阶段构建优化** ✅
   - 添加：GitHub Actions缓存机制
   - 支持：linux/amd64和linux/arm64多架构

3. **健康检查完善** ✅
   - 后端：`/health` API端点已存在
   - 前端：`/api/health` API端点已完善

4. **Docker镜像验证** ✅
   - 添加：镜像拉取验证步骤
   - 添加：运行时验证测试

## 🛠️ 详细使用说明

### GitHub Actions工作流

**文件：** `.github/workflows/dockerhub-build.yml`

**触发条件：**
- `git push origin main`
- 手动触发：GitHub Actions页面

**构建流程：**
1. 前端构建（Next.js + TypeScript）
2. 后端构建（Python FastAPI）
3. 多架构支持（AMD64 + ARM64）
4. DockerHub推送
5. 镜像验证

**环境要求：**
- GitHub Secrets配置：
  - `DOCKERHUB_USERNAME`: irisanalysis
  - `DOCKERHUB_TOKEN`: 您的DockerHub访问令牌

### 手动构建脚本

**文件：** `scripts/manual-docker-build.sh`

**基本用法：**
```bash
# 本地构建（不推送）
./scripts/manual-docker-build.sh

# 构建并推送到DockerHub
./scripts/manual-docker-build.sh --push

# 仅构建前端
./scripts/manual-docker-build.sh --frontend-only --push

# 仅构建后端
./scripts/manual-docker-build.sh --backend-only --push

# 自定义用户名和标签
./scripts/manual-docker-build.sh -u myusername -t v1.0.0 --push

# 单平台构建（更快）
./scripts/manual-docker-build.sh --platform linux/amd64 --push
```

**支持的参数：**
- `-u, --username`: DockerHub用户名
- `-t, --tag`: 镜像标签
- `-p, --push`: 推送到DockerHub
- `--platform`: 构建平台
- `--frontend-only`: 仅构建前端
- `--backend-only`: 仅构建后端

### 一键部署脚本

**文件：** `deploy-from-dockerhub.sh`

**基本用法：**
```bash
# 使用默认配置部署
./deploy-from-dockerhub.sh

# 指定用户名和标签
./deploy-from-dockerhub.sh -u irisanalysis -t latest

# 使用自定义环境文件
./deploy-from-dockerhub.sh -e .env.production
```

**部署内容：**
- 前端服务 (端口9000)
- 后端Pro1服务 (端口8000-8002)
- 后端Pro2服务 (端口8100-8102)
- Redis缓存 (端口6379)
- MinIO对象存储 (端口9001-9002)

### 部署验证脚本

**文件：** `scripts/verify-deployment.sh`

**基本用法：**
```bash
# 基础健康检查
./scripts/verify-deployment.sh

# 详细健康检查
./scripts/verify-deployment.sh --detailed

# 自定义端点检查
./scripts/verify-deployment.sh --frontend-url http://mydomain.com:9000
```

**检查内容：**
- Docker容器状态
- 服务健康检查端点
- API文档可访问性
- 系统资源使用情况

## 🔧 配置详情

### Docker镜像配置

**前端镜像：** `irisanalysis/saascontrol-frontend`
- 基础镜像：node:20-alpine
- 端口：3000（内部），9000（外部映射）
- 健康检查：`/api/health`
- 多阶段构建优化

**后端镜像：** `irisanalysis/saascontrol-backend`
- 基础镜像：python:3.11-slim
- 端口：8000-8002, 8100-8102
- 健康检查：`/health`
- 支持多项目隔离

### 环境变量配置

**必需配置（.env.dockerhub）：**
```bash
# DockerHub配置
DOCKERHUB_USERNAME=irisanalysis
IMAGE_TAG=latest

# 数据库配置
DATABASE_URL=postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1
SECONDARY_DATABASE_URL=postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro2

# API密钥
GOOGLE_GENAI_API_KEY=your_google_genai_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your-super-secret-key-32-chars-minimum
```

## 🎯 服务访问地址

部署成功后，您可以访问以下服务：

- **前端应用：** http://localhost:9000
- **API文档Pro1：** http://localhost:8000/docs
- **API文档Pro2：** http://localhost:8100/docs
- **健康检查：** http://localhost:9000/api/health?detailed=true
- **MinIO控制台：** http://localhost:9002 (admin/minio123456)

## 📊 监控和管理

### 查看服务状态
```bash
# 查看所有容器状态
docker-compose -f docker-compose.dockerhub.yml ps

# 查看服务日志
docker-compose -f docker-compose.dockerhub.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.dockerhub.yml logs -f frontend-app
```

### 重启和管理
```bash
# 重启所有服务
docker-compose -f docker-compose.dockerhub.yml restart

# 重启特定服务
docker-compose -f docker-compose.dockerhub.yml restart frontend-app

# 停止所有服务
docker-compose -f docker-compose.dockerhub.yml down

# 停止并清理卷
docker-compose -f docker-compose.dockerhub.yml down -v
```

## 🐛 故障排除

### 常见问题

**1. 镜像拉取失败**
```bash
# 检查镜像是否存在
docker pull irisanalysis/saascontrol-frontend:latest
docker pull irisanalysis/saascontrol-backend:latest

# 如果失败，手动构建
./scripts/manual-docker-build.sh --push
```

**2. 容器启动失败**
```bash
# 查看容器日志
docker logs saascontrol-frontend
docker logs saascontrol-backend-pro1

# 检查环境变量
cat .env.dockerhub
```

**3. 健康检查失败**
```bash
# 手动测试健康检查端点
curl http://localhost:9000/api/health
curl http://localhost:8000/health
curl http://localhost:8100/health

# 运行详细验证
./scripts/verify-deployment.sh --detailed
```

**4. 端口冲突**
```bash
# 检查端口占用
lsof -i :9000
lsof -i :8000
lsof -i :8100

# 停止冲突服务
docker-compose -f docker-compose.dockerhub.yml down
```

### 性能优化

**1. 镜像缓存优化**
- GitHub Actions使用构建缓存
- 本地构建使用BuildKit缓存

**2. 多架构支持**
- 支持AMD64和ARM64
- 自动选择最优架构

**3. 健康检查优化**
- 智能重试机制
- 分层健康检查

## 🔄 更新和维护

### 更新镜像
```bash
# 拉取最新镜像
docker-compose -f docker-compose.dockerhub.yml pull

# 重新创建容器
docker-compose -f docker-compose.dockerhub.yml up -d --force-recreate
```

### 备份和恢复
```bash
# 备份数据卷
docker run --rm -v saascontrol_redis-data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz -C /data .

# 恢复数据卷
docker run --rm -v saascontrol_redis-data:/data -v $(pwd):/backup alpine tar xzf /backup/redis-backup.tar.gz -C /data
```

## 📞 技术支持

如果遇到问题，请：

1. 检查本指南的故障排除部分
2. 运行验证脚本获取详细信息：`./scripts/verify-deployment.sh --detailed`
3. 查看GitHub Actions构建日志
4. 检查DockerHub镜像状态：
   - https://hub.docker.com/r/irisanalysis/saascontrol-frontend
   - https://hub.docker.com/r/irisanalysis/saascontrol-backend

---

**最后更新：** 2025-09-19
**版本：** 1.0.0
**维护者：** SaaS Control Deck Team