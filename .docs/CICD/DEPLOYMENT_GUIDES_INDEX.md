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

### 🚀 其他平台部署

#### GitHub Actions (计划中)
- **状态：** 📋 规划中
- **用途：** 自动化测试和构建流程

#### Docker 容器部署 (计划中)  
- **状态：** 📋 规划中
- **用途：** 生产环境容器化部署

#### 云服务器部署 (计划中)
- **状态：** 📋 规划中  
- **用途：** 生产环境直接部署

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