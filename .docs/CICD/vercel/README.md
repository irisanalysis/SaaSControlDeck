# Vercel 部署文档

## 📋 概述

本目录包含SaaS Control Deck项目在Vercel平台的完整部署文档，包括故障排除指南、配置模板和最佳实践。

**当前成功部署：** https://saascontrol3.vercel.app

---

## 📚 文档目录

### 🔧 [故障排除指南](./VERCEL_DEPLOYMENT_TROUBLESHOOTING.md)
**状态：** ✅ 已验证生产环境  
**最后更新：** 2024年12月  
**涵盖问题：**
- npm ci 错误 - package-lock.json 缺失  
- Vercel配置语法错误 (`nodejs` 属性)
- 模块解析失败 - @/components 路径别名
- nodeVersion 属性错误
- Next.js 版本检测失败

### ⚙️ 项目配置文件

#### [vercel.json](../../../vercel.json) - 主配置文件
```json
{
  "version": 2,
  "framework": "nextjs",
  "functions": { "src/app/api/**/*.ts": { "runtime": "@vercel/node" } },
  "env": {
    "NODE_ENV": "production",
    "NEXT_PUBLIC_APP_NAME": "SaaS Control Deck",
    "NEXT_PUBLIC_ENVIRONMENT": "vercel"
  },
  "build": { "env": { "NODE_ENV": "production", "SKIP_TYPE_CHECK": "true" } },
  "regions": ["iad1"],
  "cleanUrls": true,
  "trailingSlash": false
}
```

#### [frontend/package.json](../../../frontend/package.json) - 前端依赖
- **Framework:** Next.js 15.3.3
- **UI Library:** Radix UI + Tailwind CSS
- **AI Integration:** Google Genkit

#### [package.json](../../../package.json) - 根目录配置
- **Monorepo Scripts:** 统一的构建和部署命令
- **Development Setup:** 本地开发环境配置

---

## 🚀 快速部署指南

### 1. Vercel项目设置
```
Root Directory: frontend
Framework: Next.js (自动检测)
Build Command: npm run build (自动检测)
Output Directory: .next (自动检测)
```

### 2. 环境变量
```
NODE_ENV=production
NEXT_PUBLIC_APP_NAME=SaaS Control Deck
NEXT_PUBLIC_ENVIRONMENT=vercel
```

### 3. 部署验证检查单
- [ ] 本地构建成功 (`cd frontend && npm run build`)
- [ ] 所有导入使用相对路径
- [ ] vercel.json 配置正确
- [ ] Root Directory 设置为 `frontend`
- [ ] 无冲突的配置文件

---

## 🔍 问题快速查找

| 错误信息关键词 | 文档章节 |
|---------------|----------|
| `npm ci` | 故障排除 → 问题1 |
| `nodejs property` | 故障排除 → 问题2 |
| `Module not found @/components` | 故障排除 → 问题3 |
| `nodeVersion property` | 故障排除 → 问题4 |
| `No Next.js version detected` | 故障排除 → 问题5 |

---

## 📈 部署历史

### 成功部署记录
| 日期 | 版本 | Git Commit | 部署URL | 备注 |
|------|------|------------|---------|------|
| 2024-12 | v1.0.0 | a306547 | https://saascontrol3.vercel.app | 初次成功部署 |

### 关键修复历程
1. **npm ci 错误修复** - 调整 .gitignore 配置
2. **模块解析修复** - 转换为相对路径导入
3. **配置冲突解决** - 删除多余的 vercel.json
4. **Next.js 检测修复** - 设置正确的 Root Directory

---

## 🛠️ 维护指南

### 添加新功能时
1. 确保使用相对路径导入
2. 本地测试构建成功
3. 检查无新的路径别名依赖

### 遇到新问题时
1. 更新故障排除文档
2. 记录完整的错误信息和解决步骤
3. 更新快速查找表

### 配置更新时
1. 备份当前工作配置
2. 逐步测试配置更改
3. 更新文档中的配置示例

---

**文档维护者：** Claude Code AI Collaborative Workflow  
**技术栈：** Next.js 15.3.3 + TypeScript + Vercel  
**项目结构：** Monorepo (前端在 frontend/ 目录)