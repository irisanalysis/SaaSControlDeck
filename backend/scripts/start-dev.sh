#!/bin/bash

# 开发环境启动脚本
# 启动所有后端服务的开发环境

set -e

echo "🚀 启动AI数据分析平台开发环境..."

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查是否存在.env文件
check_env_files() {
    local project_dir=$1
    local project_name=$2
    
    if [ ! -f "$project_dir/.env" ]; then
        echo "⚠️  $project_name 缺少.env文件，复制示例文件..."
        if [ -f "$project_dir/.env.example" ]; then
            cp "$project_dir/.env.example" "$project_dir/.env"
            echo "✅ 已复制.env.example到.env，请检查配置"
        else
            echo "❌ 缺少.env.example文件"
            exit 1
        fi
    fi
}

# 检查环境文件
check_env_files "backend-pro1" "项目1"
check_env_files "backend-pro2" "项目2"

# 选择启动模式
echo ""
echo "请选择启动模式:"
echo "1) 启动项目1 (backend-pro1) - 端口8000-8099"
echo "2) 启动项目2 (backend-pro2) - 端口8100-8199"
echo "3) 同时启动两个项目"
echo "4) 退出"
echo ""

read -p "请输入选择 [1-4]: " choice

start_project() {
    local project_dir=$1
    local project_name=$2
    
    echo ""
    echo "🔄 启动$project_name..."
    
    cd "$project_dir"
    
    # 构建并启动服务
    echo "📦 构建Docker镜像..."
    docker-compose build --parallel
    
    echo "🚀 启动服务..."
    docker-compose up -d
    
    echo "⏳ 等待服务启动..."
    sleep 15
    
    # 检查服务状态
    echo "📊 检查服务状态..."
    docker-compose ps
    
    # 显示服务URLs
    echo ""
    echo "✅ $project_name 启动完成!"
    
    if [ "$project_name" = "项目1" ]; then
        echo "🌐 服务地址:"
        echo "   - API网关: http://localhost:8000"
        echo "   - 数据服务: http://localhost:8001"
        echo "   - AI服务: http://localhost:8002"
        echo "   - API文档: http://localhost:8000/docs"
        echo "   - Prometheus: http://localhost:9090"
        echo "   - MinIO控制台: http://localhost:9001"
    else
        echo "🌐 服务地址:"
        echo "   - API网关: http://localhost:8100"
        echo "   - 数据服务: http://localhost:8101"
        echo "   - AI服务: http://localhost:8102"
        echo "   - API文档: http://localhost:8100/docs"
        echo "   - Prometheus: http://localhost:9091"
        echo "   - MinIO控制台: http://localhost:9003"
    fi
    
    cd ..
}

case $choice in
    1)
        start_project "backend-pro1" "项目1"
        ;;
    2)
        start_project "backend-pro2" "项目2"
        ;;
    3)
        start_project "backend-pro1" "项目1"
        start_project "backend-pro2" "项目2"
        ;;
    4)
        echo "👋 退出"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "🎉 开发环境启动完成!"
echo ""
echo "📝 常用命令:"
echo "   - 查看日志: docker-compose logs -f [service_name]"
echo "   - 停止服务: docker-compose down"
echo "   - 重启服务: docker-compose restart [service_name]"
echo "   - 进入容器: docker-compose exec [service_name] bash"
echo ""
echo "🔧 管理脚本:"
echo "   - 停止服务: ./scripts/stop-dev.sh"
echo "   - 查看状态: ./scripts/status.sh"
echo "   - 清理数据: ./scripts/cleanup.sh"