# SaaS Control Deck - 测试脚本组织系统

## 📁 目录结构说明

本测试目录包含从根目录迁移而来的所有测试脚本，按功能分类组织。

### 🗂️ 主要分类

#### `backend/` - 后端相关测试
- `api/` - API端点功能测试
- `health/` - 服务健康检查测试
- `validation/` - 后端验证和状态检查

#### `infrastructure/` - 基础设施测试
- `docker/` - Docker构建和部署测试
- `deployment/` - 部署流程验证测试

#### `migration/` - 迁移相关测试
- `fastapi_migration/` - FastAPI迁移验证脚本
- `legacy_backend/` - 旧系统兼容性测试

#### `integration/` - 集成测试
- 端到端测试和服务间集成验证

#### `utils/` - 测试工具和配置
- 通用测试工具、配置和辅助函数

## 📋 迁移映射表

详细的文件迁移映射关系请参考 `migration_index.md`

## 🔄 迁移执行记录

- 迁移时间: {{ migration_timestamp }}
- 迁移的文件总数: {{ total_files }}
- 迁移状态: {{ migration_status }}

## 🛠️ 使用说明

所有测试脚本保持原有功能，仅调整了路径引用以适配新的目录结构。

### 快速测试命令

```bash
# 后端健康检查
python tests/backend/health/quick_health_check.py

# FastAPI迁移验证
python tests/backend/api/fastapi_migration_test.py

# Docker构建测试
bash tests/infrastructure/docker/build_tests/simple_docker_build.sh

# 完整验证流程
python tests/backend/validation/producer_validation.py
```

## 🔒 恢复机制

如需要回滚到原目录结构，请运行：
```bash
python tests/utils/rollback_migration.py
```