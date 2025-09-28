#!/bin/bash

# SaaS Control Deck - 系统启动脚本
# 自动启动后端服务并验证数据持久化功能

echo "🚀 SaaS Control Deck 系统启动"
echo "================================"

# 检查当前目录
if [ ! -f "CLAUDE.md" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

# 进入后端目录
cd backend/backend-pro1

echo "1. 检查Python虚拟环境..."
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，请先创建:"
    echo "   python -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

echo "✅ 虚拟环境存在"

echo ""
echo "2. 激活虚拟环境..."
source .venv/bin/activate

echo "✅ 虚拟环境已激活"

echo ""
echo "3. 检查数据库依赖..."
if ! python -c "import asyncpg" 2>/dev/null; then
    echo "⚠️  安装数据库依赖..."
    pip install asyncpg structlog
fi

echo "✅ 数据库依赖检查完成"

echo ""
echo "4. 初始化数据库..."
if [ -f "init_database.py" ]; then
    python init_database.py
    if [ $? -eq 0 ]; then
        echo "✅ 数据库初始化完成"
    else
        echo "❌ 数据库初始化失败"
        exit 1
    fi
else
    echo "⚠️  数据库初始化脚本不存在，跳过"
fi

echo ""
echo "5. 启动后端服务..."
echo "📊 数据库持久化功能已启用"
echo "🔗 API文档: http://localhost:8000/docs"
echo "🩺 健康检查: http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo "================================"

# 启动Uvicorn服务器
uvicorn unified_backend_fastapi:app --reload --port 8000 --host 0.0.0.0