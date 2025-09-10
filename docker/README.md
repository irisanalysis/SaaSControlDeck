# Docker 部署配置

## 📋 概述

本目录包含SaaS Control Deck项目的所有Docker部署相关文件，支持多环境部署和服务编排。

## 📁 目录结构

```
docker/
├── README.md                          # 本文档
├── environments/                      # 环境配置文件
│   ├── docker-compose.ci.yml        # CI/CD 环境
│   ├── docker-compose.production.yml # 生产环境
│   ├── docker-compose.staging.yml   # 测试环境
│   ├── .env.production              # 生产环境变量
│   └── .env.staging                 # 测试环境变量
├── services/                         # 服务特定配置 (链接到backend)
│   ├── backend-pro1/                # -> ../backend/backend-pro1/
│   └── backend-pro2/                # -> ../backend/backend-pro2/
└── monitoring/                       # 监控配置
    ├── prometheus.yml               # Prometheus配置
    └── grafana/                     # Grafana仪表板
```

## 🚀 快速部署

### 生产环境部署

```bash
# 启动生产环境
cd docker/environments
docker-compose -f docker-compose.production.yml --env-file .env.production up -d

# 查看服务状态
docker-compose -f docker-compose.production.yml ps

# 查看日志
docker-compose -f docker-compose.production.yml logs -f
```

### 测试环境部署

```bash
# 启动测试环境
cd docker/environments
docker-compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

### CI/CD 环境

```bash
# 用于自动化测试和集成
cd docker/environments
docker-compose -f docker-compose.ci.yml up --build --abort-on-container-exit
```

## ⚙️ 环境配置

### 生产环境 (.env.production)
- 优化的资源配置
- 生产级数据库设置
- 完整的监控和日志记录

### 测试环境 (.env.staging)
- 开发友好的配置
- 快速启动和重建
- 调试模式启用

## 🔧 服务编排

### 微服务架构
- **API Gateway**: 统一入口和路由
- **Data Service**: 数据处理服务
- **AI Service**: AI分析服务
- **Database**: PostgreSQL数据存储
- **Cache**: Redis缓存服务
- **Storage**: MinIO对象存储

### 端口分配
- **Project 1**: 8000-8099 端口范围
- **Project 2**: 8100-8199 端口范围
- **监控服务**: 3000-3099 端口范围

## 📊 监控和日志

### Prometheus 监控
```bash
# 访问监控界面
open http://localhost:9090
```

### Grafana 仪表板
```bash
# 访问仪表板
open http://localhost:3000
```

## 🔍 故障排除

### 常见问题

**容器启动失败**:
```bash
# 检查容器状态
docker-compose ps

# 查看详细日志
docker-compose logs <service_name>
```

**端口冲突**:
```bash
# 检查端口占用
netstat -tulpn | grep :8000
```

**资源不足**:
```bash
# 检查系统资源
docker system df
docker system prune  # 清理无用资源
```

## 🔧 开发工具

### 数据库管理
```bash
# 连接PostgreSQL
docker exec -it <postgres_container> psql -U postgres -d saascontroldb
```

### Redis管理
```bash
# 连接Redis
docker exec -it <redis_container> redis-cli
```

## 🔐 安全配置

### 生产环境安全
- 所有敏感信息使用环境变量
- 网络隔离配置
- 健康检查和自动重启
- 日志轮转和清理

## 📚 相关文档

- **[后端架构指南](../backend/CLAUDE.md)** - 微服务详细说明
- **[CI/CD部署指南](../.docs/CICD/)** - 自动化部署流程
- **[系统监控](../backend/DEPLOYMENT_GUIDE.md)** - 生产环境监控

---

**维护者**: Claude Code AI Collaborative Workflow
**最后更新**: 2024年12月