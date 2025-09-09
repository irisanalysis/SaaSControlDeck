#!/bin/bash

# 停止开发环境脚本

set -e

echo "🛑 停止AI数据分析平台开发环境..."

stop_project() {
    local project_dir=$1
    local project_name=$2
    
    echo ""
    echo "🔄 停止$project_name..."
    
    cd "$project_dir"
    
    if docker-compose ps -q > /dev/null 2>&1; then
        echo "📦 停止容器..."
        docker-compose down
        echo "✅ $project_name 已停止"
    else
        echo "ℹ️  $project_name 未运行"
    fi
    
    cd ..
}

# 选择停止模式
echo ""
echo "请选择停止模式:"
echo "1) 停止项目1 (backend-pro1)"
echo "2) 停止项目2 (backend-pro2)"  
echo "3) 停止所有项目"
echo "4) 停止并清理数据卷"
echo "5) 退出"
echo ""

read -p "请输入选择 [1-5]: " choice

case $choice in
    1)
        stop_project "backend-pro1" "项目1"
        ;;
    2)
        stop_project "backend-pro2" "项目2"
        ;;
    3)
        stop_project "backend-pro1" "项目1"
        stop_project "backend-pro2" "项目2"
        ;;
    4)
        echo "⚠️  这将删除所有数据，包括数据库数据！"
        read -p "确认删除所有数据? [y/N]: " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            cd backend-pro1
            docker-compose down -v --remove-orphans
            cd ../backend-pro2
            docker-compose down -v --remove-orphans
            cd ..
            echo "🗑️  所有数据已清理"
        else
            echo "❌ 操作已取消"
        fi
        ;;
    5)
        echo "👋 退出"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "✅ 停止操作完成!"