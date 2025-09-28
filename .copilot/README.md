# .copilot 目录说明

> **GitHub Copilot CLI 非交互式使用资源中心**

## 📁 目录结构

```
.copilot/
├── README.md                    # 本说明文件
├── NON_INTERACTIVE_TUTORIAL.md  # 完整使用教程
├── QUICK_REFERENCE.md           # 快速参考卡片
└── common-tasks.sh              # 常用任务自动化脚本
```

## 🚀 快速开始

### 1. 查看快速参考
```bash
cat .copilot/QUICK_REFERENCE.md
```

### 2. 阅读完整教程
```bash
less .copilot/NON_INTERACTIVE_TUTORIAL.md
```

### 3. 使用自动化脚本
```bash
# 查看可用任务
./.copilot/common-tasks.sh help

# 执行项目健康检查
./.copilot/common-tasks.sh health

# 检查Git状态
./.copilot/common-tasks.sh git

# SaaS Control Deck专项检查
./.copilot/common-tasks.sh saas
```

## 📚 文档说明

### 📖 NON_INTERACTIVE_TUTORIAL.md
- **内容**: GitHub Copilot CLI 非交互式使用的完整教程
- **包含**: 基础语法、参数详解、使用场景、最佳实践、故障排除
- **适用**: 初学者和高级用户的完整参考

### ⚡ QUICK_REFERENCE.md  
- **内容**: 常用命令的快速参考卡片
- **包含**: 核心命令格式、常用场景一键命令、安全模板
- **适用**: 日常快速查询和复制粘贴使用

### 🤖 common-tasks.sh
- **内容**: 预定义的常用任务自动化脚本
- **包含**: 项目检查、代码质量、安全扫描、部署验证等
- **适用**: 一键执行复杂的 Copilot 工作流

## 🎯 使用场景

### 日常开发工作流
```bash
# 晨检 - 项目状态总览
./.copilot/common-tasks.sh health

# 代码提交前检查  
./.copilot/common-tasks.sh quality

# 部署前完整验证
./.copilot/common-tasks.sh pre-deploy
```

### 问题诊断
```bash
# 性能问题分析
./.copilot/common-tasks.sh performance

# 安全漏洞扫描
./.copilot/common-tasks.sh security

# 依赖问题检查
./.copilot/common-tasks.sh deps
```

### SaaS Control Deck 专用
```bash
# 全栈平台检查
./.copilot/common-tasks.sh saas

# 前端专项检查
./.copilot/common-tasks.sh frontend

# 后端微服务检查
./.copilot/common-tasks.sh backend
```

## 🛠️ 自定义扩展

### 添加新的自动化任务
编辑 `common-tasks.sh`，按照现有模式添加新函数：

```bash
# 自定义任务示例
my_custom_task() {
    log_info "执行自定义任务..."
    execute_copilot "你的自定义任务描述"
}
```

### 创建项目特定脚本
在 `.copilot/` 目录下创建专用脚本：

```bash
# 创建数据库相关任务脚本
touch .copilot/database-tasks.sh
chmod +x .copilot/database-tasks.sh
```

## 🔧 配置说明

### 环境要求
- ✅ GitHub Copilot CLI v0.0.327+
- ✅ Bash 4.0+ 
- ✅ 当前工作目录: `/home/user/studio`

### 权限配置
脚本默认使用 `--allow-all-tools`，如需限制权限，修改 `execute_copilot` 函数的默认参数。

### 日志配置
- 默认日志级别: `info`
- 调试模式: 在脚本中设置 `--log-level debug`
- 日志目录: `./copilot-logs` 或 `~/.copilot/logs/`

## 📋 更新维护

### 版本更新
当 GitHub Copilot CLI 版本更新时，请检查并更新：
1. `NON_INTERACTIVE_TUTORIAL.md` 中的版本信息
2. `common-tasks.sh` 中的命令兼容性
3. 新功能和参数的文档说明

### 贡献指南
1. 发现有用的命令模式，添加到快速参考中
2. 常用的复杂工作流，添加到自动化脚本中
3. 遇到的问题和解决方案，更新到教程中

## 🔗 相关链接

- [GitHub Copilot CLI 官方文档](https://docs.github.com/en/copilot/github-copilot-in-the-cli)
- [SaaS Control Deck 项目文档](../CLAUDE.md)
- [项目后端架构文档](../backend/CLAUDE.md)

---

> 💡 **提示**: 这个目录是你使用 GitHub Copilot CLI 的工具箱，经常查阅和使用能大大提高开发效率！