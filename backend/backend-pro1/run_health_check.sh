#!/bin/bash

# FastAPI服务健康检查执行脚本
# 在UV虚拟环境中运行健康检查

echo "🚀 启动FastAPI健康检查..."
echo "📍 工作目录: $(pwd)"

# 检查Python可用性
if command -v python3 >/dev/null 2>&1; then
    echo "✅ Python3 可用: $(python3 --version)"
else
    echo "❌ Python3 未找到"
    exit 1
fi

# 检查FastAPI服务是否运行
echo "🔍 检查端口8000是否被占用..."
if lsof -i :8000 >/dev/null 2>&1; then
    echo "✅ 端口8000已被占用，FastAPI服务疑似运行中"
else
    echo "❌ 端口8000未被占用，FastAPI服务可能未启动"
    echo "💡 请先启动FastAPI服务: uv run uvicorn unified_backend_fastapi:app --reload --port 8000"
    # 继续执行检查，但可能会失败
fi

echo ""
echo "🔬 执行健康检查..."
python3 quick_health_check.py

echo ""
echo "📊 检查完成，查看上方结果"
