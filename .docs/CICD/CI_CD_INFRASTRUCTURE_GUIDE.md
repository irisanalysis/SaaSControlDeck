# CI/CD 基础设施完整指南

## 📋 概述

本文档提供了 SaaS Control Deck 项目的完整 CI/CD 基础设施设置指南，包括从基础配置到高级部署策略的所有内容。

## 🏗️ 架构概览

### CI/CD 流程架构

```mermaid
graph TB
    A[开发者推送代码] --> B[GitHub Actions 触发]
    B --> C[代码质量检查]
    C --> D[自动化测试]
    D --> E[构建 Docker 镜像]
    E --> F{环境选择}
    
    F -->|develop 分支| G[Staging 环境]
    F -->|main 分支| H[Production 环境]
    
    G --> I[Vercel 预览部署]
    H --> J[Docker 生产部署]
    
    I --> K[健康检查]
    J --> K
    K --> L[监控告警]
```

### 技术栈

- **CI/CD 平台**: GitHub Actions
- **容器化**: Docker + Docker Compose
- **前端部署**: Vercel (测试) + Docker (生产)
- **后端部署**: Docker 容器编排
- **监控**: Prometheus + 自定义健康检查
- **密钥管理**: GitHub Secrets + 环境变量

## 🚀 快速开始

### 1. 初始化 CI/CD 环境

```bash
# 克隆项目
git clone <your-repo-url>
cd SaaSControlDeck

# 设置 GitHub Secrets
./scripts/ci/setup-secrets.sh

# 运行本地测试
./scripts/ci/run-tests.sh

# 执行健康检查
./scripts/ci/health-check.sh
```

### 2. 配置必需的 GitHub Secrets

运行密钥设置脚本后，在 GitHub 仓库设置中配置以下密钥：

#### 核心密钥
```bash
# 基础认证
SECRET_KEY="your-super-secret-key-32-chars-minimum"
DATABASE_URL="postgresql+asyncpg://user:pass@host:port/db"
REDIS_URL="redis://:password@host:port/0"

# AI 服务
OPENAI_API_KEY="sk-your-openai-key"
GOOGLE_GENAI_API_KEY="your-google-ai-key"
```

#### Vercel 部署密钥
```bash
VERCEL_TOKEN="your_vercel_token"
VERCEL_ORG_ID="team_xxx"
VERCEL_PROJECT_ID="prj_xxx"
```

#### Docker 注册表密钥
```bash
DOCKER_REGISTRY="docker.io"  # 或私有注册表
DOCKER_USERNAME="your_username"
DOCKER_PASSWORD="your_password"
```

## 📁 项目结构

### CI/CD 相关文件

```
.
├── .github/
│   ├── workflows/
│   │   ├── frontend-ci.yml       # 前端 CI/CD 流程
│   │   └── backend-ci.yml        # 后端 CI/CD 流程
│   └── environments/
│       ├── development.yml       # 开发环境配置
│       ├── staging.yml           # 预生产环境配置
│       └── production.yml        # 生产环境配置
├── scripts/
│   ├── ci/
│   │   ├── setup-secrets.sh      # 密钥设置脚本
│   │   ├── run-tests.sh          # 测试执行脚本
│   │   └── health-check.sh       # 健康检查脚本
│   └── deploy/
│       └── deploy.sh             # 部署脚本
├── docker/                       # Docker 配置
└── .env.example                  # 环境变量模板
```

## ⚙️ 详细配置

### GitHub Actions 工作流

#### 前端 CI/CD (.github/workflows/frontend-ci.yml)

```yaml
# 主要特性:
# ✅ TypeScript 类型检查
# ✅ ESLint 代码质量检查
# ✅ 自动化测试
# ✅ 构建验证
# ✅ Vercel 部署
# ✅ Docker 镜像构建
# ✅ 安全扫描
```

**触发条件:**
- `main` 和 `develop` 分支的推送
- 影响前端代码的 Pull Request
- 手动触发

**关键作业:**
1. **代码质量检查** - TypeScript, ESLint, 安全审计
2. **测试** - 单元测试, 构建验证
3. **部署** - Vercel 预览部署
4. **Docker** - 生产镜像构建和推送

#### 后端 CI/CD (.github/workflows/backend-ci.yml)

```yaml
# 主要特性:
# ✅ Python 代码质量检查 (Black, isort, flake8, mypy)
# ✅ 单元测试和覆盖率
# ✅ 集成测试
# ✅ 多服务构建 (backend-pro1, backend-pro2)
# ✅ 安全扫描
# ✅ 性能测试
```

**关键作业:**
1. **代码质量** - 格式化、导入排序、Linting、类型检查
2. **测试** - pytest 单元测试，覆盖率报告
3. **集成测试** - Docker Compose 环境测试
4. **构建** - 多架构 Docker 镜像
5. **安全** - Trivy 容器扫描

### 环境配置

#### 开发环境 (Development)
- **自动部署**: ✅ 所有分支
- **审查要求**: ❌ 无需审查
- **测试要求**: ✅ 基础测试
- **监控级别**: 基础

#### 预生产环境 (Staging)
- **自动部署**: ✅ develop, release/* 分支
- **审查要求**: ✅ 1个审查者
- **测试要求**: ✅ 完整测试套件
- **监控级别**: 完整

#### 生产环境 (Production)
- **自动部署**: ✅ 仅 main 分支
- **审查要求**: ✅ 必需审查 + 5分钟等待
- **测试要求**: ✅ 完整测试 + 安全扫描
- **监控级别**: 企业级

## 🔧 脚本工具详解

### 1. 密钥设置脚本 (scripts/ci/setup-secrets.sh)

**功能:**
- 自动生成强密钥
- GitHub CLI 集成
- 批量密钥设置
- 配置验证

**使用方法:**
```bash
# 安装 GitHub CLI
gh auth login

# 运行密钥设置
./scripts/ci/setup-secrets.sh

# 查看生成的报告
cat secrets-setup-report.md
```

### 2. 测试执行脚本 (scripts/ci/run-tests.sh)

**功能:**
- 前端和后端统一测试
- 覆盖率报告
- 并行测试支持
- CI/CD 集成

**使用方法:**
```bash
# 运行所有测试
./scripts/ci/run-tests.sh

# 运行前端测试并生成覆盖率
./scripts/ci/run-tests.sh -t frontend -c

# 并行运行后端测试
./scripts/ci/run-tests.sh -t backend -p -v

# CI 模式
./scripts/ci/run-tests.sh -ci
```

### 3. 健康检查脚本 (scripts/ci/health-check.sh)

**功能:**
- 多服务健康监控
- JSON 输出格式
- 持续监控模式
- 响应时间统计

**使用方法:**
```bash
# 检查所有服务
./scripts/ci/health-check.sh

# 检查特定服务
./scripts/ci/health-check.sh -t frontend

# JSON 输出
./scripts/ci/health-check.sh -j

# 持续监控
./scripts/ci/health-check.sh -c -i 30
```

### 4. 部署脚本 (scripts/deploy/deploy.sh)

**功能:**
- 多环境部署支持
- 多种部署策略
- 自动备份和回滚
- 部署验证

**使用方法:**
```bash
# 预览部署
./scripts/deploy/deploy.sh -d

# 部署到 staging
./scripts/deploy/deploy.sh -e staging

# 生产部署
./scripts/deploy/deploy.sh -e production -s all

# 蓝绿部署
./scripts/deploy/deploy.sh -S blue-green
```

## 🏥 健康检查和监控

### API 端点

#### 前端健康检查
```bash
# 基础健康检查
curl http://localhost:9000/api/health

# 详细健康检查
curl http://localhost:9000/api/health?detailed=true

# 就绪检查
curl http://localhost:9000/api/ready

# Prometheus 指标
curl http://localhost:9000/api/metrics
```

#### 后端健康检查
```bash
# Backend Pro1
curl http://localhost:8000/health
curl http://localhost:8000/ready

# Backend Pro2
curl http://localhost:8100/health
curl http://localhost:8100/ready
```

### 监控指标

**前端指标:**
- `http_requests_total` - 总请求数
- `http_request_duration_seconds` - 请求响应时间
- `http_active_connections` - 活跃连接数
- `process_memory_usage_bytes` - 内存使用量

**后端指标:**
- 服务健康状态
- 数据库连接池状态
- Redis 连接状态
- AI 服务响应时间

## 🚢 部署策略

### 1. 滚动更新 (Rolling Update)
- **优点**: 零停机时间，资源效率高
- **缺点**: 部署过程中版本混合
- **适用**: 日常更新，向后兼容的变更

### 2. 蓝绿部署 (Blue-Green)
- **优点**: 快速切换，即时回滚
- **缺点**: 资源需求翻倍
- **适用**: 重要功能发布，数据库变更

### 3. 金丝雀发布 (Canary)
- **优点**: 风险控制，渐进式验证
- **缺点**: 复杂度高，监控要求高
- **适用**: 高风险变更，用户体验实验

## 🔒 安全最佳实践

### 密钥管理
- ✅ 使用 GitHub Secrets 存储敏感信息
- ✅ 定期轮换密钥
- ✅ 最小权限原则
- ✅ 环境隔离

### 容器安全
- ✅ 使用最小化基础镜像
- ✅ 非 root 用户运行
- ✅ 定期安全扫描
- ✅ 签名验证

### 网络安全
- ✅ HTTPS/TLS 加密
- ✅ 防火墙配置
- ✅ 速率限制
- ✅ CORS 配置

## 📊 监控和告警

### Prometheus 集成

```yaml
# prometheus.yml 示例
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'frontend'
    static_configs:
      - targets: ['localhost:9000']
    metrics_path: '/api/metrics'

  - job_name: 'backend-pro1'
    static_configs:
      - targets: ['localhost:8000']

  - job_name: 'backend-pro2'
    static_configs:
      - targets: ['localhost:8100']
```

### 告警规则

```yaml
# alerts.yml 示例
groups:
  - name: health_checks
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"

      - alert: HighResponseTime
        expr: http_request_duration_seconds > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time on {{ $labels.instance }}"
```

## 🎯 最佳实践

### 开发流程
1. **功能分支**: 从 `develop` 创建功能分支
2. **代码审查**: 所有变更必须经过 Pull Request
3. **自动测试**: 提交前运行本地测试
4. **持续集成**: 依赖 CI 流程验证

### 部署流程
1. **测试优先**: 确保所有测试通过
2. **渐进部署**: staging → production
3. **监控验证**: 部署后验证服务健康
4. **回滚准备**: 保持快速回滚能力

### 监控策略
1. **多层监控**: 应用层 + 基础设施层
2. **主动告警**: 问题发生前预警
3. **日志聚合**: 集中式日志管理
4. **性能基线**: 建立性能基准

## 🆘 故障排除

### 常见问题

#### CI/CD 流程失败
```bash
# 检查 GitHub Actions 日志
# 验证 Secrets 配置
gh secret list

# 本地复现问题
./scripts/ci/run-tests.sh -v
```

#### 部署失败
```bash
# 检查服务状态
./scripts/ci/health-check.sh -v

# 查看容器日志
docker-compose logs -f

# 回滚到上一版本
./scripts/deploy/rollback.sh
```

#### 健康检查失败
```bash
# 检查端口占用
lsof -i :8000

# 验证环境变量
env | grep -E "(DATABASE|REDIS|API)"

# 重启服务
docker-compose restart
```

## 📚 参考资源

### 文档链接
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Docker Compose 参考](https://docs.docker.com/compose/)
- [Prometheus 监控指南](https://prometheus.io/docs/)
- [Vercel 部署文档](https://vercel.com/docs)

### 相关文件
- [`frontend/README.md`](../../frontend/README.md) - 前端开发指南
- [`backend/CLAUDE.md`](../../backend/CLAUDE.md) - 后端架构文档
- [`docker/README.md`](../../docker/README.md) - Docker 部署指南
- [`DEPLOYMENT_GUIDE.md`](./DEPLOYMENT_GUIDE.md) - 云服务器部署指南

---

**📝 文档维护**: 本文档应随 CI/CD 流程的更新而更新。如有疑问或建议，请提交 Issue 或 Pull Request。