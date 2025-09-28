# CLAUDE.md - Full-Stack AI Platform

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture Overview

This is a full-stack AI data analysis platform with a modern monorepo structure:

- **Frontend**: Next.js SaaS dashboard with AI integration using Firebase Studio (`frontend/`)
- **Backend**: Distributed Python microservices architecture (`backend/`)

### Architecture Components

**Frontend Stack:**
- Next.js 15.3.3 with TypeScript and Tailwind CSS
- Radix UI components with custom theming
- Google Genkit for AI flows (Gemini 2.5 Flash)
- Firebase Studio Nix environment (Port 9000)

**Backend Stack:**
- **✅ FastAPI + uvicorn** (2025-09-24 升级完成)
- Multi-project isolation (backend-pro1: 8000-8099, backend-pro2: 8100-8199)
- PostgreSQL, Redis, MinIO, Ray distributed computing
- Docker containerization with Prometheus monitoring

**🚀 最新后端启动命令 (FastAPI)**:
```bash
cd /home/user/studio/backend/backend-pro1
source .venv/bin/activate
uvicorn unified_backend_fastapi:app --reload --port 8000 --host 0.0.0.0
```

**🗄️ Production Database Architecture**:
- **Cloud PostgreSQL**: 47.79.87.199:5432 (Deployed 2025-09-16)
- **Three-Environment Setup**: Development/Staging/Production isolation
- **Six Databases**: 2 per environment (pro1/pro2 microservices)
- **External Integration**: Firebase Studio → Cloud PostgreSQL
- **Documentation**: `docs/DATABASE_DEPLOYMENT_REPORT.md`

## Detailed Documentation

📖 **For specific development guidance, refer to:**

- **Frontend Development**: See existing sections below for Next.js/React patterns
- **Backend Development**: See `backend/CLAUDE.md` for comprehensive microservices architecture guide

The backend documentation covers:
- Distributed Python architecture with port allocation
- FastAPI microservices setup and configuration  
- Docker containerization and deployment
- Database schema and API design patterns
- Shared components, middleware, and authentication
- Monitoring, logging, and debugging practices

## Project Structure

**Key Architecture:**
- **Frontend Framework**: Next.js 15.3.3 with TypeScript
- **UI Components**: Radix UI primitives with custom components in `src/components/ui/`
- **Styling**: Tailwind CSS with custom theme configuration
- **AI Integration**: Google Genkit for AI flows with Gemini 2.5 Flash model
- **Layout**: Sidebar-based dashboard layout with responsive grid system

## Development Environment

### ⚠️ **重要：UV虚拟环境管理规则**

**🔧 Python开发环境要求：**
- **包管理工具**: 使用 UV (Unified Python Virtual Environment) 管理所有Python依赖
- **虚拟环境**: 所有Python项目必须在UV虚拟环境中运行
- **依赖安装**: 使用 `uv add <package>` 或 `uv pip install <package>` 安装依赖
- **环境激活**: 使用 `uv shell` 激活虚拟环境

**📋 UV命令规范：**
```bash
# 创建新虚拟环境
uv venv

# 激活虚拟环境
uv shell

# 安装依赖包
uv add fastapi uvicorn
uv pip install <package>

# 运行Python应用
uv run python main.py

# 同步依赖（类似npm install）
uv sync
```

**🚫 禁止使用的命令：**
- ❌ `pip install` - 直接使用pip
- ❌ `python -m venv` - 使用标准venv
- ❌ `conda` - 使用Conda环境

**✅ 强制要求：**
- 所有Python开发必须在UV虚拟环境中进行
- 所有依赖管理使用UV命令
- 后端微服务启动前必须激活UV环境
- **所有FastAPI服务必须使用Uvicorn启动** (`uv run uvicorn`)
- 禁止直接使用 `python main.py` 启动FastAPI应用

### Firebase Studio Nix Architecture

**重要：本项目运行在Firebase Studio的Nix架构环境中**

- **开发环境端口**: 9000（由Firebase Studio的预览系统自动管理）
- **预览配置**: `.idx/dev.nix` 文件控制开发环境
- **自动预览**: Firebase Studio会自动占用9000端口作为预览窗口
- **无需手动启动**: 在开发环境中，不需要手动运行 `npm run dev`
- **Nix管理**: 开发服务器由Nix环境自动启动和管理

### 开发环境 vs 生产部署

**开发环境（Firebase Studio）:**
```bash
# 无需手动启动 - Firebase Studio自动管理
# 预览地址: http://localhost:9000（自动代理）
```

**生产部署（云服务器）:**
```bash
# 需要手动启动前端服务器
npm run build    # 构建生产版本
npm run start    # 启动生产服务器
# 或使用开发模式
npm run dev      # 手动启动开发服务器（端口9000）
```

### 端口配置说明

- **开发环境**: 9000端口（Firebase Studio预览系统管理）
- **package.json配置**: `"dev": "cd frontend && next dev --turbopack --port 9000 --hostname 0.0.0.0"`
- **`.idx/dev.nix`**: 预览配置指向 `npm run dev`

### 重要提醒

⚠️ **在Firebase Studio环境中，永远不要手动启动 `npm run dev`**
✅ **Firebase Studio会自动处理开发服务器的启动和端口管理**
✅ **直接访问预览窗口或 localhost:9000 即可**

## Development Commands

All development commands should be run from the root directory:

### 🎯 **前端开发命令**
```bash
# 开发环境（Firebase Studio - 自动启动，无需手动运行）
# npm run dev  # 在Firebase Studio环境中会自动执行

# 生产构建
npm run build

# 生产服务器启动
npm start

# 代码检查和类型检查
npm run lint
npm run typecheck

# AI开发工具
npm run genkit:dev    # 启动Genkit开发服务器
npm run genkit:watch  # 启动Genkit文件监控模式
```

### 🐍 **后端开发命令 (FastAPI + uvicorn)**
```bash
# ✅ FastAPI统一后端服务 (2025-09-24升级)

# 启动主后端服务
cd backend/backend-pro1
source .venv/bin/activate
uvicorn unified_backend_fastapi:app --reload --port 8000 --host 0.0.0.0

# 验证服务状态
curl http://localhost:8000/health    # 健康检查
curl http://localhost:8000/docs      # API文档

# Legacy: UV虚拟环境命令（用于其他微服务）
uv sync                    # 同步pyproject.toml中的依赖
uv add fastapi uvicorn    # 添加新的依赖包

# 数据库操作
uv run python scripts/apply_base_schema.py    # 应用数据库架构
uv run python scripts/apply_migrations.py    # 运行数据库迁移

# 测试命令
uv run pytest tests/                          # 运行测试套件
```

### ⚡ **快速启动流程**
```bash
# ✅ 完整系统启动 (FastAPI升级后)
cd /home/user/studio

# 1. FastAPI后端启动
cd backend/backend-pro1
source .venv/bin/activate
uvicorn unified_backend_fastapi:app --reload --port 8000 --host 0.0.0.0 &

# 2. 前端自动启动（Firebase Studio管理）
# 无需手动操作 - 访问 http://localhost:9000

# 3. 验证服务状态
curl http://localhost:8000/health    # FastAPI健康检查
curl http://localhost:9000/api/ready # 前端API检查
```

## Code Organization

### Directory Structure
- `frontend/src/app/` - Next.js App Router pages and layout
- `frontend/src/components/` - Reusable React components
  - `ui/` - Base UI components (buttons, dialogs, forms, etc.)
  - `dashboard/` - Dashboard-specific components (cards, widgets)
  - `layout/` - Layout components (header, sidebar)
  - `ai/` - AI-related components
- `frontend/src/ai/` - AI integration and flows
  - `genkit.ts` - Genkit configuration
  - `flows/` - AI flow definitions
- `frontend/src/lib/` - Utility functions
- `frontend/src/hooks/` - Custom React hooks

### AI Integration
The application includes AI-powered contextual help using Google Genkit:
- AI flows are defined in `src/ai/flows/`
- Main AI configuration in `src/ai/genkit.ts`
- AI Help component provides contextual assistance via floating button

### UI Component System
Built on Radix UI primitives with consistent styling:
- All UI components follow the same theming system using CSS variables
- Components use `clsx` and `tailwind-merge` for conditional styling
- Dark mode support with class-based theming

### Multi-UI Library Architecture (Technical Extension)

**🔧 Current UI Libraries:**
- **Primary**: Radix UI (Production Ready)
  - Version: Various @radix-ui/* packages
  - Components: 18+ components (buttons, dialogs, forms, etc.)
  - Status: ✅ Stable, fully integrated with custom theming

**🚀 Future UI Library Extensions:**
- **Secondary**: HeroUI (Evaluation Phase)
  - Repository: https://github.com/heroui-inc/heroui
  - Documentation: https://www.heroui.com/docs/guide/installation
  - Status: ⚠️ Version Conflict - Requires Tailwind CSS v4 (Current: v3.4.1)
  - Installation: `npm install @heroui/react framer-motion`
  - Integration Strategy: Selective component adoption for new features only

**🔄 Technical Requirements for HeroUI:**
- **Tailwind CSS Upgrade**: v3.4.1 → v4.0.0+ (Breaking Change)
- **Framer Motion**: v11.9+ (Animation library dependency)
- **React Version**: v18+ (Already compatible)
- **Installation Method**: CLI recommended (`heroui init`) or manual NPM

**📋 Multi-Library Strategy:**
1. **Phase 1 (Current)**: Continue with Radix UI for existing components
2. **Phase 2 (Future)**: Evaluate HeroUI for new feature components
3. **Phase 3 (Long-term)**: Gradual migration assessment based on component needs

**⚠️ Version Conflict Resolution:**
```bash
# Current blocked installation due to Tailwind CSS version:
# npm install @heroui/react framer-motion
# Error: peer tailwindcss@">=4.0.0" required, found 3.4.17

# Potential solutions:
# Option 1: Force install (risky)
npm install @heroui/react framer-motion --force

# Option 2: Legacy peer deps (temporary)
npm install @heroui/react framer-motion --legacy-peer-deps

# Option 3: Tailwind CSS v4 upgrade (requires full testing)
npm install tailwindcss@latest
```

**🎯 Implementation Guidelines:**
- **New Features**: Consider HeroUI components for modern design patterns
- **Existing Code**: Maintain Radix UI components until migration plan
- **Styling Consistency**: Ensure both libraries work with our CSS variables theme
- **Performance**: Monitor bundle size impact when adding HeroUI components
- **Documentation**: Update component documentation when mixing libraries

**📝 Future Evaluation Criteria:**
- Component feature completeness vs Radix UI
- Bundle size and performance impact
- Maintenance overhead of multiple UI libraries
- Team learning curve and development velocity
- Long-term migration feasibility within 6-day cycles

## Key Files and Patterns

### Main Application Entry Points
- `frontend/src/app/layout.tsx` - Root layout with sidebar provider
- `frontend/src/app/page.tsx` - Main dashboard page
- `frontend/src/app/globals.css` - Global styles and CSS variables

### Component Patterns
- Use TypeScript interfaces for prop definitions
- Follow the established component structure from existing UI components
- Utilize `forwardRef` pattern for components that need DOM refs
- Use `cva` (class-variance-authority) for component variants

### Styling Guidelines
- Custom theme defined in `tailwind.config.ts` with design tokens
- CSS variables for theming in `globals.css`
- Use semantic color names (primary, secondary, muted, etc.)
- Consistent spacing and typography scale

## Development Notes

### Firebase Studio特殊环境配置
- 项目运行在Google Firebase Studio的Nix架构环境
- 开发服务器由Firebase Studio自动管理，无需手动启动
- 预览系统自动占用9000端口并提供代理访问
- `.idx/dev.nix` 文件控制整个开发环境的行为

### 标准开发注意事项
- 项目使用monorepo结构，前端代码位于 `frontend/` 目录
- 所有package脚本配置为从frontend目录运行
- TypeScript配置严格 - 确保类型安全
- 应用使用React 18和Next.js App Router
- 客户端环境变量需要 `NEXT_PUBLIC_` 前缀

### 环境切换指南

**从Firebase Studio迁移到其他环境时：**
1. 确保 `npm run dev` 可以正常启动
2. 检查端口配置是否适合目标环境
3. 验证所有环境变量是否正确设置
4. 运行 `npm run build` 确保生产构建无误

### 🗄️ 数据库连接配置

**Firebase Studio开发环境**:
```bash
# 主数据库连接
DATABASE_URL="postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1"

# 扩展数据库连接
SECONDARY_DATABASE_URL="postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro2"
```

**数据库架构**:
- **开发环境**: saascontrol_dev_pro1/pro2 (CREATEDB权限)
- **测试环境**: saascontrol_stage_pro1/pro2 (受限权限)
- **生产环境**: saascontrol_prod_pro1/pro2 (严格权限)

**快速验证命令**:
```bash
# 在云服务器上验证数据库部署
./scripts/database/comprehensive-verification.sh

# 测试开发环境连接
PGPASSWORD="dev_pass_2024_secure" psql -h 47.79.87.199 -p 5432 -U saascontrol_dev_user -d saascontrol_dev_pro1 -c "SELECT version();"
```

## 🔗 PostgreSQL MCP Integration

**Model Context Protocol (MCP) 数据库服务器配置** - 已集成 2025-09-16

Claude Code现在可以通过MCP服务器直接与PostgreSQL数据库通信，提供强大的数据分析、查询和管理功能。

### 可用的MCP数据库服务器

**✅ 已配置并连接的数据库：**
- `postgres-docker` - 开发环境 Pro1 数据库
- `postgres-dev-pro2` - 开发环境 Pro2 数据库
- `postgres-staging-pro1` - 测试环境 Pro1 数据库
- `postgres-staging-pro2` - 测试环境 Pro2 数据库

**⚠️ 生产环境数据库** (安全限制，仅在必要时使用):
- `postgres-production-pro1` - 生产环境 Pro1 数据库 (需要特殊权限)
- `postgres-production-pro2` - 生产环境 Pro2 数据库 (需要特殊权限)

### MCP工具功能详解

**📋 架构分析工具:**
- `list_schemas()` - 列出数据库中所有模式
- `list_objects(schema_name, object_type)` - 列出指定模式中的对象（表、视图、序列等）
- `get_object_details(schema_name, object_name, object_type)` - 获取数据库对象的详细信息

**🔍 查询执行工具:**
- `execute_sql(sql)` - 执行SQL查询语句（支持SELECT、INSERT、UPDATE、DELETE等）
- `explain_query(sql, analyze=False, hypothetical_indexes=[])` - 分析查询执行计划和性能

**🛠️ 性能优化工具:**
- `analyze_workload_indexes(method="dta", max_index_size_mb=10000)` - 分析工作负载并推荐索引优化
- `analyze_query_indexes(queries, method="dta", max_index_size_mb=10000)` - 针对特定查询推荐索引
- `get_top_queries(sort_by="resources", limit=10)` - 获取最慢或最消耗资源的查询

**📊 健康监控工具:**
- `analyze_db_health(health_type="all")` - 全面的数据库健康检查
  - 支持的检查类型: `all`, `buffer`, `connection`, `constraint`, `index`, `replication`, `sequence`, `vacuum`

### 使用场景与工具选择指南

**🔍 当需要了解数据库结构时：**
```python
# 使用架构分析工具
schemas = list_schemas()
tables = list_objects("public", "table")
table_details = get_object_details("public", "users", "table")
```

**💾 当需要执行数据操作时：**
```python
# 使用查询执行工具
results = execute_sql("SELECT * FROM users WHERE active = true")
user_count = execute_sql("SELECT COUNT(*) as total FROM users")
```

**⚡ 当需要性能优化时：**
```python
# 使用性能优化工具
slow_queries = get_top_queries("total_time", 5)
query_plan = explain_query("SELECT * FROM users WHERE email = ?", analyze=True)
index_recommendations = analyze_query_indexes(["SELECT * FROM users WHERE email = ?"])
```

**🩺 当需要监控数据库健康时：**
```python
# 使用健康监控工具
health_report = analyze_db_health("all")
index_health = analyze_db_health("index")
connection_status = analyze_db_health("connection")
```

**📈 当需要工作负载分析时：**
```python
# 使用工作负载分析工具
workload_indexes = analyze_workload_indexes("dta")
buffer_analysis = analyze_db_health("buffer")
```

### 最佳实践与安全注意事项

**🔒 数据库访问安全:**
- 开发和测试环境可以自由使用所有MCP工具
- 生产环境访问受限，仅在必要时使用
- 所有查询操作都会被记录和监控

**⚡ 性能考虑:**
- 使用 `explain_query()` 验证查询性能后再执行
- 定期运行 `analyze_db_health()` 监控数据库状态
- 利用 `analyze_workload_indexes()` 优化索引策略

**🛡️ 错误处理:**
- MCP工具会返回详细的错误信息
- 权限不足时会给出明确的错误提示
- 连接失败时会自动重试机制

### 快速MCP命令参考

```bash
# 检查所有MCP服务器状态
claude mcp list

# 查看PostgreSQL MCP服务器配置
cat ~/.claude.json | grep -A 5 "postgres-"
```

---

## Full-Stack Development Context

### Frontend-Backend Integration

The platform follows a decoupled architecture where:
- **Frontend (Port 9000)**: Handles UI, user interactions, and client-side AI flows
- **Backend (Ports 8000-8199)**: Provides APIs, data processing, and server-side AI analysis

### Cross-System Communication

**API Integration:**
- Frontend communicates with backend APIs via HTTP/REST
- JWT tokens for authentication between frontend and backend
- WebSocket connections for real-time data updates
- Shared data models and response formats

**Development Workflow:**
- Frontend development: Firebase Studio environment (auto-managed)
- Backend development: Docker Compose environment (manual setup)
- Both systems can run independently for development
- Integration testing requires both systems running

### Context Switching Guide

When working on **frontend** tasks:
- Focus on `frontend/` directory structure
- Use Firebase Studio Nix environment
- Reference React/Next.js patterns above
- API calls should target `http://localhost:8000` (backend-pro1) or `http://localhost:8100` (backend-pro2)

When working on **backend** tasks:
- Focus on `backend/` directory structure  
- Reference `backend/CLAUDE.md` for detailed architecture
- Use Docker Compose for service orchestration
- APIs should be accessible from `http://localhost:9000` (frontend)

### Quick Reference Links

- **Backend Architecture Details**: [`backend/CLAUDE.md`](backend/CLAUDE.md)
- **Frontend Development**: See sections below
- **API Documentation**: Available at backend service `/docs` endpoints
- **Deployment Guide**: [`backend/DEPLOYMENT_GUIDE.md`](backend/DEPLOYMENT_GUIDE.md)
- **Archive System Guide**: [`.archive/CLAUDE.md`](.archive/CLAUDE.md) - Project archival and historical reference system

---

## 📁 Archive System (.archive/)

### Project Historical Repository

The `.archive/` directory is a comprehensive archival system designed for the SaaS Control Deck Full-Stack AI Platform, supporting rapid 6-day development cycles while maintaining complete project history.

#### Core Purpose
- **🏗️ Preserve Technical Evolution**: Document architectural decisions, deprecated features, and technology stack changes
- **🔍 Enable Historical Research**: Quick access to past implementations, solutions, and lessons learned  
- **📋 Support Decision Making**: Reference previous approaches and outcomes for informed development choices
- **⚡ Accelerate Development**: Avoid reimplementing existing solutions by learning from archived patterns

#### Directory Structure Overview
```
.archive/
├── systems/          # Technical component archives (Frontend, Backend, AI, Infrastructure)
├── timeline/         # Chronological project milestones and evolution
├── experiments/      # POCs, A/B tests, and research outcomes
├── releases/         # Version artifacts, deployment configs, and release notes
├── decisions/        # Architecture Decision Records (ADRs) and technical debt tracking
├── team/            # Multi-agent collaboration patterns and workflow evolution
├── security/        # Security audits, incident responses, and vulnerability tracking
├── recovery/        # Disaster recovery procedures and incident post-mortems
└── compliance/      # Legal, regulatory, and policy change documentation
```

#### When Claude Should Use Archives

**🔍 Before Implementation**: Always check archives first
```bash
# Search for similar features
grep -r "authentication" .archive/systems/backend/
grep -r "dashboard" .archive/systems/frontend/

# Check deprecated approaches to avoid
ls .archive/systems/*/deprecated-*/
```

**🔧 During Development**: Reference proven patterns
- Frontend: Check `.archive/systems/frontend/ui-experiments/` for UI patterns
- Backend: Review `.archive/systems/backend/performance-optimizations/` for proven solutions
- AI Systems: Reference `.archive/systems/ai/prompt-engineering/` for effective approaches

**📋 After Implementation**: Document new patterns
- Archive deprecated code to appropriate `systems/*/legacy-*/` directories
- Record architectural decisions in `decisions/architecture/`
- Save experiment results in `experiments/ab-tests/` or `experiments/performance-tests/`

#### Key Integration Points

**Technology Stack Archives**:
- **Next.js 15.3.3**: Component evolution in `systems/frontend/legacy-components/`
- **FastAPI Microservices**: API versioning in `systems/backend/api-versions/`
- **Google Genkit AI**: Model versions in `systems/ai/model-versions/`
- **Docker/CI/CD**: Pipeline evolution in `systems/infrastructure/ci-cd-pipelines/`

**Multi-Agent Collaboration**:
- **Agent Configurations**: Team coordination patterns in `team/agent-configurations/`
- **Workflow Evolution**: 6-day sprint optimizations in `team/workflow-evolution/`
- **Decision History**: Cross-agent architectural decisions in `decisions/architecture/`

#### Archive Management Guidelines

**✅ What to Archive**:
- Deprecated features and components (>30 days unused)
- Completed experiments (success or failure)
- Major architectural changes and refactors
- Security incidents and their resolutions
- Performance optimization attempts and results

**❌ What NOT to Archive**:
- Current working code
- Sensitive credentials or API keys
- Large binary files (without compression)
- Temporary development artifacts

#### Quick Archive Commands
```bash
# Search archives for solutions
find .archive/ -name "*authentication*" -o -name "*user*"
grep -r "performance issue" .archive/systems/backend/

# Check recent archives
find .archive/ -type f -mtime -30 | sort

# Review architectural decisions
cat .archive/decisions/architecture/001-microservices-adoption.md
```

**📖 Complete Archive Guide**: See [`.archive/CLAUDE.md`](.archive/CLAUDE.md) for detailed usage instructions, search patterns, and project-specific archival strategies.

---

## CI/CD & DevOps Automation

### SaaSControl-Pro Specialized Agents

**Agent Directory**: `.claude/agents/SaaSControl-Pro/`

This project includes specialized Claude Code agents designed specifically for the SaaS Control Deck platform. These agents have deep knowledge of our unique architecture and can perform automated tasks with project-specific optimizations.

#### CI/CD Workflow Specialist Agent

**Location**: `.claude/agents/SaaSControl-Pro/cicd-workflow-specialist.md`

**专家级CI/CD自动化代理 - 针对SaaS Control Deck项目优化**

The `cicd-workflow-specialist` agent is a specialized CI/CD automation expert with comprehensive knowledge of our platform's specific architecture and deployment requirements. This agent should be used for ALL CI/CD related tasks.

**Key Capabilities:**
- **Multi-Environment Deployment**: Automated staging and production deployments via Vercel
- **Microservices Orchestration**: Handles backend-pro1 (8000-8099) and backend-pro2 (8100-8199) port allocations
- **GitHub Actions Optimization**: SaaS Control Deck specific workflow configurations
- **Docker Container Management**: Multi-service containerization with health checks
- **Security & Monitoring**: Integrated Prometheus metrics, security scanning, and alerting

**Architecture Knowledge:**
- Next.js 15.3.3 frontend with Firebase Studio Nix environment
- Python FastAPI microservices (API Gateway, Data Service, AI Service)
- Vercel deployment integration (Team: `team_5qxA92e7EhxCquOBE7DO3lrP`)
- Docker registry management and image optimization
- Health check APIs for 6 microservices monitoring

**When to Use This Agent:**
- Setting up or modifying CI/CD pipelines
- Troubleshooting deployment issues
- Optimizing build and deployment performance  
- Implementing new deployment environments
- Configuring monitoring and alerting systems
- Any DevOps automation tasks

**Usage Example:**
```markdown
# To launch the CI/CD specialist agent
Use Task tool with subagent_type: "cicd-workflow-specialist"

# Example tasks:
- "Optimize our GitHub Actions workflow for faster builds"
- "Set up monitoring for our microservices deployment"
- "Troubleshoot Vercel deployment configuration issues"
- "Implement blue-green deployment strategy"
- "Add security scanning to our CI pipeline"
```

**⚠️ Important Usage Notes:**
- This agent has **complete CI/CD implementation authority** for the SaaS Control Deck project
- It understands our specific port allocations, service dependencies, and deployment constraints
- Always prefer this agent over generic DevOps tools for project-specific tasks
- The agent can perform automated setup, configuration, and troubleshooting

**Project-Specific Configurations:**
- **Vercel Integration**: Pre-configured with project credentials and team settings
- **Health Check Endpoints**: Automated monitoring for all 6 microservices  
- **Security Scanning**: Trivy container scanning and dependency vulnerability checks
- **Performance Optimization**: AI platform specific caching and build optimizations
- **Multi-Stage Builds**: Optimized Docker configurations for Python FastAPI services

### CI/CD Pipeline Architecture

**Current Implementation Status**: ✅ **Production Ready**

Our CI/CD pipeline follows the validated flow:
```
Firebase Studio (Dev) → GitHub (Version Control) → Vercel (Staging/Production) → Docker (Cloud Deployment)
```

**Automated Workflows:**
1. **Code Quality Assurance** - TypeScript checks, ESLint, security audits
2. **Multi-Environment Testing** - Automated build verification for development and production
3. **Vercel Deployment** - Automated staging and production deployments
4. **Docker Containerization** - Multi-service container builds with security scanning
5. **Health Monitoring** - Automated health checks and deployment verification

**Monitoring & Alerting:**
- Prometheus metrics collection across all services
- Automated deployment status notifications
- Health check verification post-deployment
- Security vulnerability scanning and reporting

### Quick CI/CD Commands

```bash
# Trigger full CI/CD pipeline
git push origin main

# Test staging deployment
git push origin develop

# Manual health check
curl -f "https://[your-vercel-domain]/api/health"

# Validate CI/CD configuration
./scripts/ci/validate-saascontrol-setup.sh
```