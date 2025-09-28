# GitHub Copilot CLI 快速参考卡

> **快速访问**: `cat .copilot/QUICK_REFERENCE.md`

## 🚀 核心命令

```bash
# 基本格式
copilot -p "你的问题" --allow-all-tools

# 带权限控制
copilot -p "任务" --allow-tool 'read' --deny-tool 'write'

# 带日志
copilot -p "任务" --allow-all-tools --log-level debug
```

## ⚡ 常用场景一键命令

### Git & 项目管理
```bash
# Git状态检查
copilot -p "显示Git状态和最近提交" --allow-all-tools

# 项目健康检查
copilot -p "检查项目整体状态和健康度" --allow-all-tools

# 依赖更新
copilot -p "检查并更新过期依赖" --allow-all-tools
```

### 代码质量
```bash
# 代码质量分析
copilot -p "分析代码质量并提供改进建议" --allow-all-tools

# 安全扫描
copilot -p "执行安全漏洞扫描" --allow-all-tools

# 性能分析
copilot -p "分析应用性能瓶颈" --allow-all-tools
```

### SaaS Control Deck 专用
```bash
# 前端状态
copilot -p "检查Next.js应用和Firebase Studio环境" --allow-all-tools

# 后端服务
copilot -p "检查FastAPI微服务(8000-8199端口)状态" --allow-all-tools

# 数据库连接
copilot -p "测试PostgreSQL数据库连接" --allow-all-tools

# 全栈集成测试
copilot -p "执行前后端集成验证" --allow-all-tools
```

## 🛡️ 安全命令模板

```bash
# 只读分析
copilot -p "分析项目结构" --allow-tool 'read' --deny-tool 'write'

# 受限修改
copilot -p "优化配置文件" --allow-all-tools --deny-tool 'shell(rm)'

# 带备份的操作
copilot -p "备份后清理临时文件" --allow-all-tools --log-dir ./backup-logs
```

## 📋 日常工作流

```bash
# 晨检
copilot -p "执行晨检：Git状态、依赖、服务健康" --allow-all-tools

# 提交前检查
copilot -p "提交前检查：代码质量、测试、构建" --allow-all-tools

# 部署前验证
copilot -p "部署前验证：安全、性能、配置" --allow-all-tools
```

## 🔧 调试命令

```bash
# 详细日志调试
copilot -p "你的任务" --allow-all-tools --log-level debug --log-dir ./debug

# 查看日志
tail -f ./debug/copilot.log

# 权限测试
copilot -p "测试文件访问" --allow-all-tools --add-dir $(pwd)
```

---
📖 **完整教程**: `.copilot/NON_INTERACTIVE_TUTORIAL.md`