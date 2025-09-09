#!/bin/bash

# 初始化开发环境脚本

set -e

echo "🔧 初始化AI数据分析平台开发环境..."

# 检查必要的工具
check_dependencies() {
    echo "📋 检查依赖工具..."
    
    local missing_tools=()
    
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        missing_tools+=("docker-compose")
    fi
    
    if ! command -v curl &> /dev/null; then
        missing_tools+=("curl")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        echo "❌ 缺少以下工具: ${missing_tools[*]}"
        echo "请先安装这些工具后再运行此脚本"
        exit 1
    fi
    
    echo "✅ 所有依赖工具已安装"
}

# 设置环境文件
setup_env_files() {
    echo ""
    echo "📝 设置环境配置文件..."
    
    for project in "backend-pro1" "backend-pro2"; do
        if [ ! -f "$project/.env" ]; then
            if [ -f "$project/.env.example" ]; then
                cp "$project/.env.example" "$project/.env"
                echo "✅ 已创建 $project/.env"
            else
                echo "❌ 未找到 $project/.env.example"
                exit 1
            fi
        else
            echo "ℹ️  $project/.env 已存在"
        fi
    done
}

# 创建必要的目录
create_directories() {
    echo ""
    echo "📁 创建必要的目录结构..."
    
    directories=(
        "backend-pro1/logs"
        "backend-pro2/logs"
        "backend-pro1/data"
        "backend-pro2/data"
        "monitoring"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            echo "✅ 创建目录: $dir"
        fi
    done
}

# 设置权限
setup_permissions() {
    echo ""
    echo "🔒 设置文件权限..."
    
    # 给脚本文件执行权限
    chmod +x scripts/*.sh
    echo "✅ 脚本文件权限已设置"
    
    # 确保日志目录可写
    chmod 755 backend-pro1/logs backend-pro2/logs 2>/dev/null || true
    echo "✅ 日志目录权限已设置"
}

# 生成密钥
generate_secrets() {
    echo ""
    echo "🔐 生成安全密钥..."
    
    # 为每个项目生成独特的SECRET_KEY
    for project in "backend-pro1" "backend-pro2"; do
        env_file="$project/.env"
        
        if grep -q "your-super-secret-key" "$env_file"; then
            # 生成32字符随机密钥
            secret_key=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
            
            # 替换默认密钥
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/your-super-secret-key-change-in-production.*/$secret_key/" "$env_file"
            else
                # Linux
                sed -i "s/your-super-secret-key-change-in-production.*/$secret_key/" "$env_file"
            fi
            
            echo "✅ 已为 $project 生成安全密钥"
        else
            echo "ℹ️  $project 已有自定义密钥"
        fi
    done
}

# 验证配置
validate_config() {
    echo ""
    echo "✅ 验证配置..."
    
    for project in "backend-pro1" "backend-pro2"; do
        env_file="$project/.env"
        
        # 检查必要的环境变量
        required_vars=("PROJECT_ID" "SECRET_KEY" "DATABASE_URL")
        missing_vars=()
        
        for var in "${required_vars[@]}"; do
            if ! grep -q "^$var=" "$env_file"; then
                missing_vars+=("$var")
            fi
        done
        
        if [ ${#missing_vars[@]} -ne 0 ]; then
            echo "❌ $project 缺少环境变量: ${missing_vars[*]}"
            exit 1
        fi
        
        echo "✅ $project 配置验证通过"
    done
}

# 创建监控配置
setup_monitoring() {
    echo ""
    echo "📊 设置监控配置..."
    
    # 创建Prometheus配置
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'api-gateway-pro1'
    static_configs:
      - targets: ['api-gateway:8000']
  
  - job_name: 'data-service-pro1'
    static_configs:
      - targets: ['data-service:8001']
      
  - job_name: 'ai-service-pro1'
    static_configs:
      - targets: ['ai-service:8002']
EOF
    
    echo "✅ Prometheus配置已创建"
}

# 主执行流程
main() {
    echo "🚀 开始初始化..."
    
    check_dependencies
    setup_env_files
    create_directories
    setup_permissions
    generate_secrets
    validate_config
    setup_monitoring
    
    echo ""
    echo "🎉 开发环境初始化完成!"
    echo ""
    echo "📋 后续步骤:"
    echo "   1. 检查并修改 .env 配置文件"
    echo "   2. 设置 OPENAI_API_KEY 环境变量"
    echo "   3. 运行 ./scripts/start-dev.sh 启动服务"
    echo ""
    echo "📚 文档和资源:"
    echo "   - README.md: 项目说明"
    echo "   - API文档: http://localhost:8000/docs"
    echo "   - 监控面板: http://localhost:9090"
    echo ""
}

# 运行主函数
main "$@"