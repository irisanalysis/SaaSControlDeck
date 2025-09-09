#!/bin/bash

# 查看服务状态脚本

set -e

echo "📊 AI数据分析平台服务状态"
echo "================================="

check_project_status() {
    local project_dir=$1
    local project_name=$2
    local port_range=$3
    
    echo ""
    echo "🔍 检查$project_name ($port_range)..."
    
    cd "$project_dir"
    
    if [ -f "docker-compose.yml" ]; then
        echo "📦 Docker容器状态:"
        if docker-compose ps -q > /dev/null 2>&1; then
            docker-compose ps
        else
            echo "   ❌ 无运行中的容器"
        fi
        
        echo ""
        echo "🌐 服务健康检查:"
        
        # 检查各服务的健康状态
        if [ "$project_name" = "项目1" ]; then
            ports=(8000 8001 8002)
            services=("API网关" "数据服务" "AI服务")
        else
            ports=(8100 8101 8102)
            services=("API网关" "数据服务" "AI服务")
        fi
        
        for i in "${!ports[@]}"; do
            port=${ports[$i]}
            service=${services[$i]}
            
            if curl -s --connect-timeout 3 "http://localhost:$port/health" > /dev/null 2>&1; then
                echo "   ✅ $service (端口$port): 运行中"
            else
                echo "   ❌ $service (端口$port): 不可访问"
            fi
        done
    else
        echo "   ❌ 未找到docker-compose.yml文件"
    fi
    
    cd ..
}

# 检查两个项目的状态
check_project_status "backend-pro1" "项目1" "8000-8099"
check_project_status "backend-pro2" "项目2" "8100-8199"

echo ""
echo "🖥️  系统资源使用情况:"
echo "================================="

# 显示Docker资源使用情况
if command -v docker &> /dev/null; then
    echo "📊 Docker容器资源使用:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
    
    echo ""
    echo "💾 Docker磁盘使用:"
    docker system df
else
    echo "❌ Docker未安装或不可访问"
fi

echo ""
echo "🔗 服务端点:"
echo "================================="
echo "项目1:"
echo "  - API网关: http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs" 
echo "  - 数据服务: http://localhost:8001/docs"
echo "  - AI服务: http://localhost:8002/docs"
echo "  - Prometheus: http://localhost:9090"
echo "  - MinIO: http://localhost:9001"
echo ""
echo "项目2:"
echo "  - API网关: http://localhost:8100"
echo "  - API文档: http://localhost:8100/docs"
echo "  - 数据服务: http://localhost:8101/docs" 
echo "  - AI服务: http://localhost:8102/docs"
echo "  - Prometheus: http://localhost:9091"
echo "  - MinIO: http://localhost:9003"