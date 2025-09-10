# Documentation & Version Management

This directory contains project documentation and version management files for the SaaSControlDeck platform.

## Structure

```
.docs/
├── README.md                                    # This file
├── CICD/                                       # 🚀 CI/CD 部署文档中心
│   ├── DEPLOYMENT_GUIDES_INDEX.md             #   📋 部署指南总索引
│   ├── PROJECT_CONFIG_INDEX.md                #   🔧 项目配置文件索引
│   ├── vercel/                                #   🔧 Vercel 部署专区
│   │   ├── README.md                          #     Vercel 文档主页
│   │   ├── VERCEL_DEPLOYMENT_TROUBLESHOOTING.md #  完整故障排除指南
│   │   └── .vercelignore                      #     Vercel 忽略配置
│   ├── github/                                #   ⚡ GitHub Actions
│   │   └── workflows/                         #     工作流配置文件
│   ├── testing/                               #   🧪 测试和验证工具
│   │   ├── test-imports.mjs                   #     导入测试脚本
│   │   └── verify-deployment.mjs              #     部署验证脚本
│   ├── scripts/                               #   📜 部署管理脚本
│   ├── CI_CD_SETUP_GUIDE.md                   #   CI/CD 设置指南
│   ├── DEPLOYMENT_FIX_SUMMARY.md              #   部署问题修复汇总
│   ├── DEPLOYMENT_GUIDE.md                    #   通用部署指南
│   ├── VERCEL_DEPLOYMENT_GUIDE.md             #   Vercel 专用部署指南
│   ├── .lighthouserc.json                     #   性能测试配置
│   └── .markdownlint.json                     #   文档规范配置
├── versions/                                   # 📦 Version management directory
│   ├── v1.0.0/                                # Version-specific documentation
│   │   ├── CHANGELOG.md                       # Changes in this version
│   │   ├── RELEASE_NOTES.md                   # Release notes
│   │   ├── MIGRATION.md                       # Migration guide
│   │   └── docs/                              # Version-specific docs
│   └── latest/                                # Symlink to latest version
├── architecture/                              # 🏗️ System architecture docs
├── api/                                       # 🔗 API documentation
└── user-guides/                               # 📖 User documentation
```

## Version Management Guidelines

- Each version gets its own directory under `versions/`
- Version directories follow semantic versioning (e.g., v1.0.0, v1.1.0, v2.0.0)
- The `latest/` directory always points to the most recent version
- Critical files for each version:
  - `CHANGELOG.md`: Detailed changes
  - `RELEASE_NOTES.md`: User-facing notes
  - `MIGRATION.md`: Upgrade instructions (if needed)

## Documentation Types

- **Architecture**: System design and technical architecture
- **API**: REST API documentation and examples
- **Deployment**: Installation and deployment guides
- **User Guides**: End-user documentation
- **Developer Guides**: Development setup and contribution guides

## 🚀 快速导航

### CI/CD 部署相关
- **[📋 CI/CD 部署指南总索引](./CICD/DEPLOYMENT_GUIDES_INDEX.md)** - 所有部署平台的导航中心
- **[🔧 Vercel 部署专区](./CICD/vercel/)** - Vercel 平台完整部署文档
  - [主文档](./CICD/vercel/README.md) - Vercel 部署概览和快速开始
  - [故障排除](./CICD/vercel/VERCEL_DEPLOYMENT_TROUBLESHOOTING.md) - 完整的问题解决方案
  - **成功部署：** https://saascontrol3.vercel.app ✅

### 版本管理
- **[📦 v1.0.0 版本文档](./versions/v1.0.0/)** - 初始平台发布版本
- **[📦 最新版本](./versions/latest/)** - 当前最新版本文档

### 其他文档分类
- **[🏗️ 系统架构](./architecture/)** - 系统设计和技术架构 (计划中)
- **[🔗 API 文档](./api/)** - REST API 文档和示例 (计划中)  
- **[📖 用户指南](./user-guides/)** - 最终用户文档 (计划中)

---

## 📝 文档维护

当遇到新的部署问题或解决方案时：
1. 更新对应的故障排除文档
2. 在索引文档中添加新的问题分类
3. 确保解决方案包含完整的步骤和验证方法