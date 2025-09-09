# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This is a Next.js SaaS dashboard application with AI integration using Firebase Studio. The project has a monorepo structure with the frontend code located in the `frontend/` directory.

**Key Architecture:**
- **Frontend Framework**: Next.js 15.3.3 with TypeScript
- **UI Components**: Radix UI primitives with custom components in `src/components/ui/`
- **Styling**: Tailwind CSS with custom theme configuration
- **AI Integration**: Google Genkit for AI flows with Gemini 2.5 Flash model
- **Layout**: Sidebar-based dashboard layout with responsive grid system

## Development Environment

### Firebase Studio Nix Architecture

**重要：本项目运行在Firebase Studio的Nix架构环境中**

- **开发环境端口**: 9000（由Firebase Studio的预览系统自动管理）
- **预览配置**: `.idx/dev.nix` 文件控制开发环境
- **自动预览**: Firebase Studio会自动占用9000端口作为预览窗口
- **无需手动启动**: 在开发环境中，不需要手动运行 `npm run dev`
- **Nix管理**: 开发服务器由Nix环境自动启动和管理

### 开发环境 vs 生产部署

**开发环境（Firebase Studio）:**
```bash
# 无需手动启动 - Firebase Studio自动管理
# 预览地址: http://localhost:9000（自动代理）
```

**生产部署（云服务器）:**
```bash
# 需要手动启动前端服务器
npm run build    # 构建生产版本
npm run start    # 启动生产服务器
# 或使用开发模式
npm run dev      # 手动启动开发服务器（端口9000）
```

### 端口配置说明

- **开发环境**: 9000端口（Firebase Studio预览系统管理）
- **package.json配置**: `"dev": "cd frontend && next dev --turbopack --port 9000 --hostname 0.0.0.0"`
- **`.idx/dev.nix`**: 预览配置指向 `npm run dev`

### 重要提醒

⚠️ **在Firebase Studio环境中，永远不要手动启动 `npm run dev`**
✅ **Firebase Studio会自动处理开发服务器的启动和端口管理**
✅ **直接访问预览窗口或 localhost:9000 即可**

## Development Commands

All development commands should be run from the root directory:

```bash
# 开发环境（Firebase Studio - 自动启动，无需手动运行）
# npm run dev  # 在Firebase Studio环境中会自动执行

# 生产构建
npm run build

# 生产服务器启动
npm start

# 代码检查和类型检查
npm run lint
npm run typecheck

# AI开发工具
npm run genkit:dev    # 启动Genkit开发服务器
npm run genkit:watch  # 启动Genkit文件监控模式
```

## Code Organization

### Directory Structure
- `frontend/src/app/` - Next.js App Router pages and layout
- `frontend/src/components/` - Reusable React components
  - `ui/` - Base UI components (buttons, dialogs, forms, etc.)
  - `dashboard/` - Dashboard-specific components (cards, widgets)
  - `layout/` - Layout components (header, sidebar)
  - `ai/` - AI-related components
- `frontend/src/ai/` - AI integration and flows
  - `genkit.ts` - Genkit configuration
  - `flows/` - AI flow definitions
- `frontend/src/lib/` - Utility functions
- `frontend/src/hooks/` - Custom React hooks

### AI Integration
The application includes AI-powered contextual help using Google Genkit:
- AI flows are defined in `src/ai/flows/`
- Main AI configuration in `src/ai/genkit.ts`
- AI Help component provides contextual assistance via floating button

### UI Component System
Built on Radix UI primitives with consistent styling:
- All UI components follow the same theming system using CSS variables
- Components use `clsx` and `tailwind-merge` for conditional styling
- Dark mode support with class-based theming

## Key Files and Patterns

### Main Application Entry Points
- `frontend/src/app/layout.tsx` - Root layout with sidebar provider
- `frontend/src/app/page.tsx` - Main dashboard page
- `frontend/src/app/globals.css` - Global styles and CSS variables

### Component Patterns
- Use TypeScript interfaces for prop definitions
- Follow the established component structure from existing UI components
- Utilize `forwardRef` pattern for components that need DOM refs
- Use `cva` (class-variance-authority) for component variants

### Styling Guidelines
- Custom theme defined in `tailwind.config.ts` with design tokens
- CSS variables for theming in `globals.css`
- Use semantic color names (primary, secondary, muted, etc.)
- Consistent spacing and typography scale

## Development Notes

### Firebase Studio特殊环境配置
- 项目运行在Google Firebase Studio的Nix架构环境
- 开发服务器由Firebase Studio自动管理，无需手动启动
- 预览系统自动占用9000端口并提供代理访问
- `.idx/dev.nix` 文件控制整个开发环境的行为

### 标准开发注意事项
- 项目使用monorepo结构，前端代码位于 `frontend/` 目录
- 所有package脚本配置为从frontend目录运行
- TypeScript配置严格 - 确保类型安全
- 应用使用React 18和Next.js App Router
- 客户端环境变量需要 `NEXT_PUBLIC_` 前缀

### 环境切换指南

**从Firebase Studio迁移到其他环境时：**
1. 确保 `npm run dev` 可以正常启动
2. 检查端口配置是否适合目标环境
3. 验证所有环境变量是否正确设置
4. 运行 `npm run build` 确保生产构建无误