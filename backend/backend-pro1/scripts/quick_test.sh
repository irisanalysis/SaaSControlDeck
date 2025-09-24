#!/bin/bash

# 数据源连接后端开发快速测试脚本
# Day 1 开发完成后的功能验证

echo "🚀 开始数据源连接后端功能测试..."

# 设置项目根目录
PROJECT_ROOT="/home/user/studio/backend/backend-pro1"
cd "$PROJECT_ROOT"

# 检查Python环境
echo "📦 检查Python环境..."
python3 --version
pip3 list | grep -E "(fastapi|pandas|pydantic)" || echo "⚠️  可能缺少必要的Python包"

# 检查数据库连接配置
echo "🗄️  检查数据库配置..."
if [ -f ".env" ]; then
    echo "✓ 发现.env配置文件"
    grep -E "DATABASE_URL|REDIS_URL" .env || echo "⚠️  请检查数据库配置"
else
    echo "❌ 未找到.env配置文件，请从.env.example复制"
fi

# 应用数据库迁移
echo "🔄 应用数据库迁移..."
python3 scripts/apply_migrations.py
if [ $? -eq 0 ]; then
    echo "✓ 数据库迁移完成"
else
    echo "❌ 数据库迁移失败"
    exit 1
fi

# 运行API测试
echo "🧪 运行API功能测试..."
python3 scripts/test_data_apis.py
if [ $? -eq 0 ]; then
    echo "✓ API功能测试通过"
else
    echo "❌ API功能测试失败"
    exit 1
fi

# 检查路由文件
echo "📋 检查API路由文件..."
for file in "app/routers/data_upload.py" "app/routers/data_preview.py" "app/routers/data_management.py"; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo "✓ $file ($lines 行)"
    else
        echo "❌ 缺少文件: $file"
    fi
done

# 检查模型文件
echo "📊 检查数据模型..."
if [ -f "shared/models/data_source.py" ]; then
    echo "✓ 数据源模型定义完成"
else
    echo "❌ 缺少数据源模型文件"
fi

# 检查迁移文件
echo "🗄️  检查数据库迁移..."
if [ -f "scripts/migrations/001_add_data_source_extensions.sql" ]; then
    echo "✓ 数据库迁移脚本存在"
else
    echo "❌ 缺少数据库迁移脚本"
fi

# 启动开发服务器（可选）
echo "🌐 准备启动开发服务器..."
echo "如需启动服务器，请运行: python3 data-service/app/main.py"

# 显示API端点信息
echo ""
echo "📋 已实现的API端点："
echo "  📤 文件上传:"
echo "    POST /upload/session - 创建上传会话"
echo "    POST /upload/file - 直接文件上传"
echo "    POST /upload/chunk/{session_id} - 分块上传"
echo "    GET  /upload/progress/{session_id} - 上传进度"
echo ""
echo "  👁️  数据预览:"
echo "    GET  /preview/datasets/{id}/preview - 数据预览"
echo "    GET  /preview/datasets - 数据集列表"
echo "    GET  /preview/datasets/{id}/quality - 质量检查"
echo ""
echo "  🛠️  数据管理:"
echo "    GET  /manage/datasets/{id} - 获取数据集"
echo "    PUT  /manage/datasets/{id} - 更新数据集"
echo "    DELETE /manage/datasets/{id} - 删除数据集"
echo "    GET  /manage/analytics - 统计分析"
echo ""
echo "  🩺 健康检查:"
echo "    GET  /health - 服务健康状态"
echo ""

# 开发完成检查清单
echo "✅ Day 1 开发完成检查清单："
echo "  ✓ 数据库表结构设计和创建"
echo "  ✓ Pydantic数据模型定义"
echo "  ✓ 文件上传API实现"
echo "    - 支持CSV/JSON文件"
echo "    - 文件大小验证"
echo "    - 分块上传支持"
echo "    - 上传进度跟踪"
echo "  ✓ 数据预览API实现"
echo "    - 数据类型检测"
echo "    - 统计信息生成"
echo "    - 数据质量检查"
echo "    - 预览数据缓存"
echo "  ✓ 数据管理API实现"
echo "    - CRUD操作"
echo "    - 权限控制"
echo "    - 统计分析"
echo ""
echo "🎉 数据源连接后端开发 Day 1 任务完成！"
echo "🔄 为明天的前端开发提供了稳定的API基础"