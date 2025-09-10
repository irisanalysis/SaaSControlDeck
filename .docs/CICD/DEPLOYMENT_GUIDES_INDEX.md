# CI/CD 部署指南索引

## 📚 可用部署文档

### 🔧 [项目配置文件索引](./PROJECT_CONFIG_INDEX.md)
快速访问所有重要的项目配置文件和说明
- **vercel.json** - Vercel 部署配置
- **package.json** - 依赖和脚本管理  
- **next.config.ts** - Next.js 框架配置
- **tsconfig.json** - TypeScript 配置
- **tailwind.config.ts** - 样式配置

---

### 🔧 Vercel 部署

#### [📁 Vercel 部署文档目录](./vercel/)
- **主文档：** [Vercel 部署完整指南](./vercel/README.md)
- **故障排除：** [部署问题解决方案](./vercel/VERCEL_DEPLOYMENT_TROUBLESHOOTING.md)
- **状态：** ✅ 已验证 (2024年12月)
- **成功部署：** https://saascontrol3.vercel.app
- **技术栈：** Next.js 15.3.3, Monorepo结构, TypeScript

### 🐳 Docker 容器部署
- **状态：** ✅ 已配置完成
- **主文档：** [Docker 部署指南](../../docker/README.md)
- **生产环境：** [生产级Docker配置](../../docker/environments/docker-compose.production.yml)
- **测试环境：** [测试环境配置](../../docker/environments/docker-compose.staging.yml)
- **CI/CD环境：** [持续集成配置](../../docker/environments/docker-compose.ci.yml)

### 📊 部署文档集合
- **[CI/CD 设置指南](./CI_CD_SETUP_GUIDE.md)** - 完整的CI/CD管道设置
- **[部署修复总结](./DEPLOYMENT_FIX_SUMMARY.md)** - 已解决的部署问题汇总
- **[部署指南](./DEPLOYMENT_GUIDE.md)** - 通用部署指南
- **[Vercel部署指南](./VERCEL_DEPLOYMENT_GUIDE.md)** - Vercel特定部署说明

### ☁️ 云服务器部署
- **状态：** ✅ 已配置完成
- **主文档：** [云服务器部署指南](./CLOUD_SERVER_DEPLOYMENT_GUIDE.md)
- **用途：** AWS、阿里云、腾讯云等云服务器完整部署方案
- **包含内容：** 服务器配置、Docker部署、Nginx代理、SSL证书、监控维护

### 📝 项目管理文档
- **[项目重组总结](../PROJECT_RESTRUCTURE_SUMMARY.md)** - 最新的目录结构重组详情

### ⚙️ GitHub Actions
- **状态：** ✅ 已配置完成
- **工作流：** [GitHub Actions配置](./github/workflows/.github/)
- **用途：** 自动化测试、构建和部署流程

### 🧪 测试和验证
- **[测试工具](./testing/)** - 部署验证脚本和测试工具
- **[部署脚本](./scripts/)** - 自动化部署和管理脚本

---

## 🔍 快速问题查找

| 错误关键词 | 对应文档章节 |
|-----------|-------------|
| `npm ci` | Vercel故障排除 → 问题1 |
| `nodejs property` | Vercel故障排除 → 问题2 |
| `Module not found @/components` | Vercel故障排除 → 问题3 |
| `nodeVersion property` | Vercel故障排除 → 问题4 |
| `No Next.js version detected` | Vercel故障排除 → 问题5 |
| `monorepo` | Vercel故障排除 → 经验总结 |

---

## 📋 使用建议

1. **遇到部署问题时**
   - 首先查找对应的故障排除文档
   - 按照文档中的步骤逐一验证
   - 使用成功配置作为参考基准

2. **新增部署问题时**
   - 在对应文档中添加新发现的问题
   - 记录完整的错误信息和解决步骤
   - 更新索引文件以便后续查找

3. **配置新项目时**
   - 参考成功配置模板
   - 避免已知的配置陷阱
   - 优先使用验证过的解决方案

---

**索引最后更新：** 2024年12月
**维护者：** Claude Code AI Collaborative Workflow