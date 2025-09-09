# Bug修复记录系统

本目录用于记录所有bug修复过程，便于Claude和团队成员快速检索和学习。

## 目录结构

```
bug-fixes/
├── README.md                    # 本文档
├── index/                       # 索引目录
│   ├── by-component.md         # 按组件分类索引
│   ├── by-type.md              # 按bug类型分类索引
│   ├── by-severity.md          # 按严重程度分类索引
│   └── chronological.md        # 按时间顺序索引
├── templates/                   # 模板目录
│   ├── bug-report-template.md  # bug报告模板
│   └── fix-record-template.md  # 修复记录模板
├── YYYY-MM/                     # 按年月分组的修复记录
│   └── YYYY-MM-DD_bug-name.md  # 具体的修复记录文件
└── archived/                    # 归档目录（过期或不再相关的修复记录）
```

## 文件命名规范

### 修复记录文件命名
格式：`YYYY-MM-DD_类型_组件_简短描述.md`

示例：
- `2025-09-09_render_nextjs_react-hooks-ssr-errors.md`
- `2025-09-09_style_tailwind_css-syntax-errors.md`
- `2025-09-08_api_ai-component_server-client-mismatch.md`

### 类型标识
- `render`: 渲染相关bug (SSR/CSR, React组件等)
- `style`: 样式相关bug (CSS, Tailwind等)
- `api`: API相关bug (接口调用、数据处理等)
- `logic`: 业务逻辑bug
- `perf`: 性能问题
- `security`: 安全问题
- `config`: 配置问题
- `deploy`: 部署相关问题

## 使用方法

1. **记录新bug修复**：
   - 使用 `templates/fix-record-template.md` 创建新的修复记录
   - 按命名规范保存到对应月份目录
   - 更新相关索引文件

2. **检索bug记录**：
   - 按组件检索：查看 `index/by-component.md`
   - 按类型检索：查看 `index/by-type.md`
   - 按时间检索：查看 `index/chronological.md`
   - 按严重程度检索：查看 `index/by-severity.md`

3. **Claude检索指令**：
   ```
   查找相关bug修复记录：
   - "检查 .docs/PRD/bug-fixes/index/ 目录中的相关索引"
   - "搜索关键词：组件名/错误类型/技术栈"
   ```

## 标签系统

每个修复记录都应包含以下标签便于检索：
- **Frontend/Backend**: 前端或后端
- **Framework**: Next.js, React, FastAPI等
- **Component**: 具体组件名称
- **Severity**: Critical, High, Medium, Low
- **Status**: Fixed, Ongoing, Deferred
- **Related-Files**: 涉及的具体文件路径
- **Functions**: 涉及的具体函数名

## 自动化集成

建议集成到开发流程中：
1. 每次修复bug后自动创建记录
2. 定期更新索引文件
3. 与git commit关联，便于代码追溯