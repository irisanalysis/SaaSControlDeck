# 综合测试套件文档
数据源连接功能的完整测试覆盖指南
包含单元测试、集成测试、端到端测试和性能测试
RELEVANT FILES: comprehensive-test-suite.yml, vitest.config.ts, playwright.config.ts, .env.test

## 📚 目录

- [概述](#概述)
- [测试架构](#测试架构)
- [测试类型](#测试类型)
- [快速开始](#快速开始)
- [本地开发测试](#本地开发测试)
- [CI/CD自动化测试](#cicd自动化测试)
- [测试覆盖率要求](#测试覆盖率要求)
- [故障排除](#故障排除)
- [最佳实践](#最佳实践)

## 🎯 概述

本测试套件为数据源连接功能提供了全面的测试覆盖，确保从文件上传到数据分析的完整用户流程的质量和可靠性。

### 核心功能测试覆盖

- **文件上传流程**：支持CSV、JSON等格式，包含拖拽上传、分块上传
- **数据预览**：列信息显示、数据类型检测、样本数据展示
- **数据质量分析**：缺失值检测、重复项检查、数据统计
- **错误处理**：文件格式验证、大小限制、网络错误处理
- **用户体验**：进度指示、可访问性支持、响应式设计

## 🏗️ 测试架构

### 后端测试 (Python + FastAPI)

```
backend/backend-pro1/tests/
├── unit/                     # 单元测试
│   ├── test_data_preview_utils.py      # 数据预览工具测试
│   └── test_file_validation.py         # 文件验证逻辑测试
├── integration/              # 集成测试
│   ├── test_data_preview_api.py        # API集成测试
│   └── test_database_operations.py     # 数据库操作测试
└── conftest.py              # 测试配置和Fixtures
```

### 前端测试 (React + TypeScript)

```
frontend/tests/
├── components/              # 组件测试
│   ├── data-management/
│   │   └── data-source-connection.test.tsx
│   └── ui/
│       ├── data-preview-table.test.tsx
│       ├── file-dropzone.test.tsx
│       └── upload-progress.test.tsx
├── hooks/                   # Hook测试
│   ├── use-data-preview.test.ts
│   └── use-data-source-upload.test.ts
├── api/                     # API客户端测试
│   └── data-sources.test.ts
├── integration/             # 集成测试
│   └── data-management-workflow.test.tsx
├── e2e/                     # 端到端测试
│   ├── data-source-connection.e2e.ts
│   ├── global-setup.ts
│   └── global-teardown.ts
└── setup.ts                # 测试环境设置
```

## 🧪 测试类型

### 1. 单元测试 (Unit Tests)

**后端单元测试**
- 数据类型检测算法
- 列统计计算逻辑
- 质量分析算法
- 文件验证规则

**前端单元测试**
- React组件渲染
- Hook状态管理
- 工具函数逻辑
- API客户端封装

### 2. 集成测试 (Integration Tests)

**API集成测试**
- 数据上传API端点
- 预览生成API
- 数据分析API
- 错误响应处理

**数据库集成测试**
- CRUD操作验证
- 事务处理测试
- 数据完整性检查
- 并发访问测试

**组件集成测试**
- 多组件协作工作流
- 状态管理集成
- API调用集成
- 错误边界测试

### 3. 端到端测试 (E2E Tests)

**完整用户流程**
- 文件选择和上传
- 数据预览查看
- 质量分析执行
- 错误情况处理

**浏览器兼容性**
- Chrome、Firefox、Safari
- 桌面和移动设备
- 不同屏幕分辨率

**可访问性测试**
- 键盘导航支持
- 屏幕阅读器兼容
- ARIA标签验证
- 焦点管理检查

### 4. 性能测试 (Performance Tests)

**文件上传性能**
- 小文件上传速度
- 大文件分块上传
- 并发上传处理
- 内存使用监控

**数据处理性能**
- 大数据集预览
- 复杂分析算法
- 响应时间基准
- 吞吐量测试

## 🚀 快速开始

### 环境要求

- **Node.js**: 18+
- **Python**: 3.11+
- **PostgreSQL**: 15+
- **Redis**: 7+

### 安装依赖

```bash
# 前端依赖
cd frontend
npm install

# 后端依赖
cd ../backend/backend-pro1
pip install -r requirements.txt

# 安装Playwright浏览器
cd ../../frontend
npx playwright install
```

### 环境配置

```bash
# 复制测试环境配置
cp .env.test .env.local

# 启动测试数据库
docker-compose up -d postgres redis
```

## 🛠️ 本地开发测试

### 前端测试

```bash
cd frontend

# 运行所有测试
npm test

# 运行特定类型的测试
npm run test:unit          # 单元测试
npm run test:components    # 组件测试
npm run test:hooks         # Hook测试
npm run test:api           # API客户端测试
npm run test:integration   # 集成测试

# 端到端测试
npm run test:e2e           # 无界面模式
npm run test:e2e:ui        # 可视化界面

# 测试覆盖率
npm run test:coverage

# 监视模式
npm run test:watch
```

### 后端测试

```bash
cd backend/backend-pro1

# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_data_preview_utils.py
pytest tests/integration/test_data_preview_api.py

# 生成覆盖率报告
pytest --cov=app --cov-report=html

# 并行测试
pytest -n auto

# 详细输出
pytest -v --tb=short
```

### 完整流程测试

```bash
# 启动后端服务
cd backend/backend-pro1
uvicorn data_service.app.main:app --port 8000 &

# 启动前端服务
cd ../../frontend
npm run dev &

# 运行完整E2E测试
npm run test:e2e
```

## 🔄 CI/CD自动化测试

### GitHub Actions工作流

我们的CI/CD流水线包含以下测试阶段：

1. **环境准备** - 验证测试环境和依赖
2. **后端单元测试** - 核心逻辑验证
3. **后端集成测试** - API和数据库测试
4. **前端单元测试** - 组件和Hook测试
5. **前端集成测试** - 工作流集成验证
6. **端到端测试** - 完整用户流程
7. **性能测试** - 性能基准验证
8. **测试汇总** - 结果分析和报告

### 触发条件

- **自动触发**：`main`和`develop`分支的推送
- **PR触发**：针对`main`分支的拉取请求
- **手动触发**：支持选择测试级别（unit/integration/e2e/performance/full）

### 工作流配置

```yaml
# 手动触发测试
workflow_dispatch:
  inputs:
    test_level:
      description: '测试级别选择'
      required: true
      default: 'full'
      type: choice
      options:
        - unit           # 仅单元测试
        - integration    # 仅集成测试
        - e2e           # 仅端到端测试
        - performance   # 仅性能测试
        - full          # 完整测试套件
```

### 测试报告

- **覆盖率报告**：通过Codecov自动生成
- **E2E测试结果**：Playwright HTML报告
- **性能测试数据**：Apache Bench基准报告
- **测试汇总**：自动生成的Markdown报告

## 📊 测试覆盖率要求

### 覆盖率目标

| 测试类型 | 最低要求 | 推荐目标 | 关键路径 |
|---------|---------|---------|----------|
| 后端单元测试 | 85% | 90%+ | 数据处理逻辑 |
| 前端单元测试 | 80% | 85%+ | 核心组件 |
| 集成测试 | 70% | 80%+ | API端点 |
| E2E测试 | - | 100% | 关键用户流程 |

### 关键路径覆盖

**必须覆盖的功能路径：**
- ✅ 文件上传完整流程
- ✅ 数据预览生成流程
- ✅ 错误处理和恢复
- ✅ 用户交互响应
- ✅ 数据质量分析

### 覆盖率检查

```bash
# 前端覆盖率检查
cd frontend
npm run test:coverage

# 后端覆盖率检查
cd ../backend/backend-pro1
pytest --cov=app --cov-fail-under=85
```

## 🔧 故障排除

### 常见问题

#### 1. 测试环境启动失败

```bash
# 检查端口占用
lsof -i :8000
lsof -i :9000

# 重置数据库
docker-compose down -v
docker-compose up -d postgres redis
```

#### 2. Playwright浏览器问题

```bash
# 重新安装浏览器
npx playwright install --force

# 检查浏览器依赖
npx playwright install-deps
```

#### 3. 测试数据库连接失败

```bash
# 验证数据库连接
PGPASSWORD=postgres123 psql -h localhost -p 5432 -U postgres -d test_db -c "SELECT 1;"

# 检查环境变量
echo $TEST_DATABASE_URL
```

#### 4. 依赖版本冲突

```bash
# 清理并重新安装
rm -rf node_modules package-lock.json
npm install

# Python依赖重置
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### 测试调试

#### 前端测试调试

```bash
# Vitest调试模式
npm run test:watch

# 特定组件调试
npx vitest run tests/components/data-management --reporter=verbose

# Playwright调试
npx playwright test --debug
npx playwright test --headed
```

#### 后端测试调试

```bash
# pytest详细输出
pytest -v -s tests/unit/test_data_preview_utils.py

# 单个测试函数
pytest tests/unit/test_data_preview_utils.py::test_detect_data_types -v

# 调试模式
pytest --pdb
```

## 📋 最佳实践

### 测试编写原则

1. **测试隔离**：每个测试应该独立运行
2. **数据清理**：使用适当的setup/teardown
3. **模拟外部依赖**：避免依赖外部服务
4. **描述性命名**：测试名称应清楚说明测试目的
5. **边界条件**：测试正常和异常情况

### 代码覆盖率最佳实践

```typescript
// ✅ 好的测试：覆盖多种情况
describe('file validation', () => {
  it('should accept valid CSV files', () => { /* */ });
  it('should reject invalid file types', () => { /* */ });
  it('should handle file size limits', () => { /* */ });
  it('should validate file content', () => { /* */ });
});

// ❌ 避免：只测试快乐路径
describe('file validation', () => {
  it('should work with valid files', () => { /* */ });
});
```

### 性能测试注意事项

1. **基准设定**：建立性能基准线
2. **环境一致性**：确保测试环境一致
3. **资源监控**：监控CPU、内存使用
4. **渐进式测试**：从小数据集开始

### E2E测试最佳实践

1. **等待策略**：使用智能等待而非固定延迟
2. **数据独立性**：每个测试使用独立的测试数据
3. **失败重试**：设置合理的重试策略
4. **截图和视频**：失败时自动保存调试信息

## 🎯 测试策略路线图

### 第一阶段：核心功能覆盖 ✅
- 基础单元测试
- 关键API集成测试
- 主要用户流程E2E测试

### 第二阶段：全面测试覆盖
- 边界条件测试
- 错误恢复测试
- 性能回归测试
- 安全性测试

### 第三阶段：高级测试自动化
- 视觉回归测试
- 接口契约测试
- 混沌工程测试
- 用户行为模拟

## 📞 支持和贡献

### 获取帮助

- **文档问题**：查看项目README和API文档
- **测试失败**：检查CI/CD工作流日志
- **性能问题**：参考性能基准数据

### 贡献指南

1. **添加新测试**：遵循现有测试结构和命名约定
2. **更新测试**：确保向后兼容性
3. **文档更新**：同步更新相关文档
4. **覆盖率要求**：确保新功能达到覆盖率要求

---

## 🚀 开始测试

现在您已经了解了完整的测试套件，可以开始使用：

```bash
# 克隆项目并安装依赖
git clone <repository>
cd saas-control-deck

# 安装依赖
npm install
cd frontend && npm install
cd ../backend/backend-pro1 && pip install -r requirements.txt

# 运行快速测试验证
cd ../../frontend && npm run test:unit
cd ../backend/backend-pro1 && pytest tests/unit/ -v

# 运行完整测试套件
cd ../../
.github/workflows/comprehensive-test-suite.yml # 通过GitHub Actions触发
```

🎉 **恭喜！您的数据源连接功能现在拥有了生产级别的测试覆盖！**