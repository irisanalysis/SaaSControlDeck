# 分布式Python后端架构

## 项目概述

这是一个可扩展的分布式Python后端系统，支持多项目隔离部署，专为AI数据分析平台设计。

## 架构特点

- **多项目隔离**: backend-pro1 (端口8000-8099), backend-pro2 (端口8100-8199)
- **微服务架构**: API网关、数据服务、AI服务独立部署
- **容器化部署**: Docker + Kubernetes 支持
- **AI集成**: OpenAI API、Ray分布式计算集成
- **可观测性**: 完整的监控、日志和告警体系

## 目录结构

```
backend/
├── backend-pro1/          # 项目1 (端口8000-8099)
│   ├── api-gateway/       # API网关服务
│   ├── data-service/      # 数据处理服务
│   ├── ai-service/        # AI分析服务
│   └── shared/            # 共享组件
├── backend-pro2/          # 项目2 (端口8100-8199)
│   ├── api-gateway/       # API网关服务
│   ├── data-service/      # 数据处理服务
│   ├── ai-service/        # AI分析服务
│   └── shared/            # 共享组件
├── config/                # 全局配置
├── scripts/               # 部署和维护脚本
├── deployments/           # Kubernetes部署文件
└── monitoring/            # 监控配置
```

## 快速开始

### 开发环境启动

```bash
# 启动项目1服务
cd backend-pro1
docker-compose up -d

# 启动项目2服务
cd ../backend-pro2
docker-compose up -d
```

### 生产部署

```bash
# Kubernetes部署
kubectl apply -f deployments/
```

## API端点

### 项目1 (backend-pro1)
- API Gateway: http://localhost:8000
- Data Service: http://localhost:8001
- AI Service: http://localhost:8002

### 项目2 (backend-pro2)
- API Gateway: http://localhost:8100
- Data Service: http://localhost:8101
- AI Service: http://localhost:8102

## 技术栈

- **Web框架**: FastAPI 0.104.1
- **异步处理**: Celery + Redis
- **数据库**: PostgreSQL 15 + SQLAlchemy 2.0
- **AI计算**: Ray 2.8.0 + OpenAI API
- **容器化**: Docker + Kubernetes
- **监控**: Prometheus + Grafana + ELK

## 开发指南

请参考各服务目录下的README.md文件获取详细开发指南。