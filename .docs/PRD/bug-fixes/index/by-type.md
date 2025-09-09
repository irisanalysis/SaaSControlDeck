# 按Bug类型分类索引

## 渲染问题 (Render Issues)

### 服务端渲染 (SSR)
- `2025-09-09_render_nextjs_react-hooks-ssr-errors.md`: React Hooks在SSR中的兼容性问题
  - React.useState错误
  - "use client"指令缺失
  - 服务端/客户端不一致

### 客户端渲染 (CSR) 
- `2025-09-09_render_nextjs_react-hooks-ssr-errors.md`: 客户端组件架构问题
  - 服务器函数直接调用
  - 浏览器环境检查缺失

## 样式问题 (Style Issues)

### CSS语法错误
- `2025-09-09_render_nextjs_react-hooks-ssr-errors.md`: Tailwind CSS无效类名
  - `hover:shadow-primary/8`语法错误
  - `shadow-*/*`透明度语法问题
  - 自定义CSS类定义问题

### 响应式设计
- 暂无记录

## API问题 (API Issues)

### 接口架构
- `2025-09-09_render_nextjs_react-hooks-ssr-errors.md`: AI服务调用架构重构
  - 服务器端函数客户端调用问题
  - API路由缺失
  - 错误处理不完善

### 数据处理
- 暂无记录

## 逻辑问题 (Logic Issues)

### 业务逻辑
- 暂无记录

### 状态管理
- `2025-09-09_render_nextjs_react-hooks-ssr-errors.md`: React状态管理SSR兼容性
  - Toast状态管理
  - 组件状态初始化

## 性能问题 (Performance Issues)

### 加载性能
- 暂无记录

### 运行时性能
- 暂无记录

## 安全问题 (Security Issues)

### 数据安全
- 暂无记录

### API安全
- 暂无记录

## 配置问题 (Configuration Issues)

### 构建配置
- `2025-09-09_render_nextjs_react-hooks-ssr-errors.md`: Next.js构建配置
  - 静态生成配置
  - TypeScript配置

### 环境配置
- 暂无记录

## 部署问题 (Deployment Issues)

### 构建问题
- `2025-09-09_render_nextjs_react-hooks-ssr-errors.md`: Next.js构建失败
  - CSS语法导致构建失败
  - 静态页面生成错误

### 运行时问题
- 暂无记录

---

## 问题模式分析

### 高频问题类型
1. **渲染问题**: 占比最高，主要是SSR/CSR兼容性
2. **样式问题**: CSS框架语法和自定义样式冲突
3. **API架构**: 前后端分离架构设计问题

### 解决策略总结
1. **渲染问题**: 添加环境检查，正确使用客户端指令
2. **样式问题**: 验证CSS语法，使用标准语法替代
3. **API问题**: 合理设计API路由，避免架构混乱

## 检索说明
Claude可以通过bug类型快速定位相似问题：
```
"查找渲染相关的bug修复记录"
→ 查看 .docs/PRD/bug-fixes/index/by-type.md 渲染问题部分
```