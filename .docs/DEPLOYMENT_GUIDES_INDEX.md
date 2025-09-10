# 部署指南索引

## 📚 可用部署文档

### 🔧 故障排除指南

#### [Vercel部署故障排除完整指南](./VERCEL_DEPLOYMENT_TROUBLESHOOTING.md)
- **状态：** ✅ 已验证 (2024年12月)
- **成功部署：** https://saascontrol3.vercel.app
- **覆盖问题：**
  - npm ci 错误 - package-lock.json 缺失
  - Vercel配置语法错误 (`nodejs` 属性)
  - 模块解析失败 - @/components 路径别名
  - nodeVersion 属性错误
  - Next.js 版本检测失败
- **适用于：** Next.js 15.3.3, Monorepo结构, TypeScript项目

### 🚀 成功配置模板

#### Vercel配置 (已验证)
- **Root Directory：** `frontend`
- **Framework：** Next.js (自动检测)
- **导入方式：** 相对路径导入
- **配置文件：** 简化的vercel.json

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