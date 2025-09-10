# 项目配置文件索引

## 📋 概述

本文档提供SaaS Control Deck项目所有重要配置文件的快速访问和说明。

---

## 🔧 部署配置

### Vercel 部署
- **[vercel.json](../../vercel.json)** - Vercel 部署主配置
  - Framework: Next.js
  - Root Directory: `frontend`
  - 环境变量和构建设置
  - API 函数配置

### GitHub Actions (未来)
- **[.github/workflows/](../../.github/workflows/)** - CI/CD 工作流配置 (计划中)

---

## 📦 包管理配置

### 根目录
- **[package.json](../../package.json)** - 根目录包配置
  - 项目名称: `nextn`
  - Monorepo 脚本管理
  - 全局依赖

- **[package-lock.json](../../package-lock.json)** - 依赖锁定文件
  - 确定性依赖安装
  - 版本锁定

### 前端目录
- **[frontend/package.json](../../frontend/package.json)** - 前端包配置
  - 项目名称: `saas-control-deck-frontend`
  - Next.js 15.3.3 + React 18
  - Radix UI 组件库
  - Google Genkit AI 集成

---

## ⚙️ 框架配置

### Next.js
- **[frontend/next.config.ts](../../frontend/next.config.ts)** - Next.js 配置
  - 动态路径解析
  - Webpack 自定义配置
  - 环境适配

### TypeScript
- **[frontend/tsconfig.json](../../frontend/tsconfig.json)** - TypeScript 配置
  - 路径别名映射
  - 编译选项
  - 类型检查设置

### Tailwind CSS
- **[frontend/tailwind.config.ts](../../frontend/tailwind.config.ts)** - 样式配置
  - 自定义主题
  - 设计令牌
  - 组件样式

---

## 🔍 开发工具配置

### 代码质量
- **[.gitignore](../../.gitignore)** - Git 忽略规则
  - 依赖目录
  - 构建输出
  - 环境文件

### 组件库
- **[frontend/components.json](../../frontend/components.json)** - UI 组件配置
  - Shadcn/ui 配置
  - 组件样式设置

---

## 🌍 环境配置

### 开发环境
- **[.idx/dev.nix](../../.idx/dev.nix)** - Firebase Studio Nix 环境 (如果存在)
- **本地环境变量文件** (未跟踪):
  - `.env.local`
  - `.env.development`
  - `.env.production`

### 生产环境
- **Vercel 环境变量** (在 Vercel Dashboard 中配置):
  - `NODE_ENV=production`
  - `NEXT_PUBLIC_APP_NAME=SaaS Control Deck`
  - `NEXT_PUBLIC_ENVIRONMENT=vercel`

---

## 📊 配置文件状态

| 配置文件 | 状态 | 最后更新 | 备注 |
|----------|------|----------|------|
| vercel.json | ✅ 已验证 | 2024-12 | 成功部署配置 |
| package.json (root) | ✅ 稳定 | 2024-12 | Monorepo 管理 |
| frontend/package.json | ✅ 稳定 | 2024-12 | 前端依赖 |
| next.config.ts | ✅ 已调优 | 2024-12 | 路径解析优化 |
| tsconfig.json | ✅ 已调优 | 2024-12 | 路径别名配置 |
| tailwind.config.ts | ✅ 自定义 | 2024-12 | 主题配置 |

---

## 🔧 配置修改指南

### 添加新依赖
1. **前端依赖**: `cd frontend && npm install <package>`
2. **全局工具**: 在根目录 `npm install <package>`
3. **类型定义**: `npm install -D @types/<package>`

### 修改构建配置
1. **Next.js 配置**: 编辑 `frontend/next.config.ts`
2. **TypeScript**: 编辑 `frontend/tsconfig.json`
3. **样式配置**: 编辑 `frontend/tailwind.config.ts`

### 部署配置更新
1. **Vercel**: 编辑 `vercel.json`
2. **环境变量**: 在 Vercel Dashboard 中配置
3. **构建脚本**: 编辑对应的 `package.json`

---

## 📚 相关文档

- **[Vercel 部署文档](./vercel/README.md)** - 完整部署指南
- **[故障排除指南](./vercel/VERCEL_DEPLOYMENT_TROUBLESHOOTING.md)** - 问题解决方案
- **[版本管理](../versions/)** - 项目版本历史

---

**最后更新：** 2024年12月  
**维护者：** Claude Code AI Collaborative Workflow