#!/bin/bash

# ===========================================
# SaaS Control Deck - 云服务器环境初始化脚本
# ===========================================
# 适用于 Ubuntu 20.04/22.04, CentOS 8+, RHEL 8+
# 功能：完整的云服务器环境准备和依赖安装

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INSTALL_DIR="/opt/saascontroldeck"
SERVICE_USER="saascontrol"
LOG_FILE="/var/log/saascontroldeck-setup.log"

# 默认参数
ENVIRONMENT="production"
INSTALL_DOCKER=true
INSTALL_NGINX=true
INSTALL_CERTBOT=true
SETUP_FIREWALL=true
AUTO_CONFIRM=false
SKIP_USER_CREATION=false

# 日志函数
log_info() { 
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}
log_success() { 
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}
log_warning() { 
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}
log_error() { 
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# 显示帮助信息
show_help() {
    cat << EOF
SaaS Control Deck 云服务器环境初始化脚本

用法: $0 [选项]

选项:
    -e, --environment ENV     环境类型: production, staging (默认: production)
    --skip-docker            跳过Docker安装
    --skip-nginx             跳过Nginx安装
    --skip-certbot           跳过Let's Encrypt Certbot安装
    --skip-firewall          跳过防火墙配置
    --skip-user              跳过服务用户创建
    -y, --yes                自动确认所有选项
    -h, --help               显示此帮助

部署后操作指南:
1. 配置域名DNS指向服务器IP
2. 运行 ./deploy.sh -e production 执行应用部署
3. 访问 https://your-domain.com 验证部署

环境要求:
- Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- 最小 4GB RAM, 2 CPU核心
- 至少 20GB 可用磁盘空间
- 推荐 8GB RAM, 4 CPU核心用于生产环境
EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --skip-docker)
                INSTALL_DOCKER=false
                shift
                ;;
            --skip-nginx)
                INSTALL_NGINX=false
                shift
                ;;
            --skip-certbot)
                INSTALL_CERTBOT=false
                shift
                ;;
            --skip-firewall)
                SETUP_FIREWALL=false
                shift
                ;;
            --skip-user)
                SKIP_USER_CREATION=true
                shift
                ;;
            -y|--yes)
                AUTO_CONFIRM=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 系统检查
check_system() {
    log_info "检查系统环境..."

    # 检查Root权限
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi

    # 检测操作系统
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
        log_info "检测到系统: $OS $VER"
    else
        log_error "无法检测操作系统版本"
        exit 1
    fi

    # 检查系统资源
    local mem_gb=$(free -g | awk 'NR==2{printf "%.1f", $2}')
    local cpu_cores=$(nproc)
    local disk_gb=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')

    log_info "系统资源:"
    log_info "  内存: ${mem_gb}GB"
    log_info "  CPU核心: $cpu_cores"
    log_info "  可用磁盘: ${disk_gb}GB"

    # 资源检查警告
    if (( $(echo "$mem_gb < 4.0" | bc -l) )); then
        log_warning "内存不足4GB，可能影响性能"
    fi

    if [[ $cpu_cores -lt 2 ]]; then
        log_warning "CPU核心数少于2，可能影响性能"
    fi

    if [[ $disk_gb -lt 20 ]]; then
        log_error "可用磁盘空间不足20GB，请释放空间后重试"
        exit 1
    fi

    log_success "系统检查完成"
}

# 更新系统
update_system() {
    log_info "更新系统软件包..."

    case "$OS" in
        *Ubuntu*|*Debian*)
            apt-get update -y
            apt-get upgrade -y
            apt-get install -y curl wget git vim htop unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release bc
            ;;
        *CentOS*|*Red\ Hat*|*Rocky*|*AlmaLinux*)
            yum update -y
            yum install -y curl wget git vim htop unzip yum-utils device-mapper-persistent-data lvm2 bc
            ;;
        *)
            log_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac

    log_success "系统更新完成"
}

# 创建服务用户
create_service_user() {
    if [[ "$SKIP_USER_CREATION" == "true" ]]; then
        log_info "跳过服务用户创建"
        return 0
    fi

    log_info "创建服务用户: $SERVICE_USER"

    # 检查用户是否已存在
    if id "$SERVICE_USER" &>/dev/null; then
        log_info "用户 $SERVICE_USER 已存在"
    else
        # 创建系统用户
        useradd -r -m -s /bin/bash "$SERVICE_USER"
        usermod -aG docker "$SERVICE_USER" 2>/dev/null || true
        
        log_success "服务用户 $SERVICE_USER 创建完成"
    fi

    # 创建项目目录
    mkdir -p "$INSTALL_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod 755 "$INSTALL_DIR"

    # 创建日志目录
    mkdir -p /var/log/saascontroldeck
    chown -R "$SERVICE_USER:$SERVICE_USER" /var/log/saascontroldeck

    # 创建数据目录
    mkdir -p /opt/saascontroldeck/data/{postgres,redis,minio,elasticsearch}
    chown -R "$SERVICE_USER:$SERVICE_USER" /opt/saascontroldeck/data

    log_success "目录结构创建完成"
}

# 安装Docker
install_docker() {
    if [[ "$INSTALL_DOCKER" != "true" ]]; then
        log_info "跳过Docker安装"
        return 0
    fi

    log_info "安装Docker..."

    # 检查Docker是否已安装
    if command -v docker &> /dev/null; then
        log_info "Docker已安装，版本: $(docker --version)"
        return 0
    fi

    case "$OS" in
        *Ubuntu*|*Debian*)
            # 添加Docker官方GPG密钥
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

            # 添加Docker仓库
            echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

            # 安装Docker
            apt-get update -y
            apt-get install -y docker-ce docker-ce-cli containerd.io
            ;;
        *CentOS*|*Red\ Hat*|*Rocky*|*AlmaLinux*)
            # 添加Docker仓库
            yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

            # 安装Docker
            yum install -y docker-ce docker-ce-cli containerd.io
            ;;
    esac

    # 启动并启用Docker服务
    systemctl start docker
    systemctl enable docker

    # 验证Docker安装
    if docker --version; then
        log_success "Docker安装完成: $(docker --version)"
    else
        log_error "Docker安装失败"
        exit 1
    fi
}

# 安装Docker Compose
install_docker_compose() {
    if [[ "$INSTALL_DOCKER" != "true" ]]; then
        return 0
    fi

    log_info "安装Docker Compose..."

    # 检查是否已安装
    if command -v docker-compose &> /dev/null; then
        log_info "Docker Compose已安装，版本: $(docker-compose --version)"
        return 0
    fi

    # 下载并安装Docker Compose
    local compose_version="2.24.1"
    curl -L "https://github.com/docker/compose/releases/download/v${compose_version}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose

    # 创建符号链接
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

    # 验证安装
    if docker-compose --version; then
        log_success "Docker Compose安装完成: $(docker-compose --version)"
    else
        log_error "Docker Compose安装失败"
        exit 1
    fi
}

# 安装Nginx
install_nginx() {
    if [[ "$INSTALL_NGINX" != "true" ]]; then
        log_info "跳过Nginx安装"
        return 0
    fi

    log_info "安装Nginx..."

    # 检查是否已安装
    if command -v nginx &> /dev/null; then
        log_info "Nginx已安装，版本: $(nginx -v 2>&1)"
        return 0
    fi

    case "$OS" in
        *Ubuntu*|*Debian*)
            apt-get install -y nginx
            ;;
        *CentOS*|*Red\ Hat*|*Rocky*|*AlmaLinux*)
            yum install -y nginx
            ;;
    esac

    # 启动并启用Nginx
    systemctl start nginx
    systemctl enable nginx

    # 验证安装
    if nginx -v 2>&1; then
        log_success "Nginx安装完成"
    else
        log_error "Nginx安装失败"
        exit 1
    fi
}

# 安装SSL证书工具
install_certbot() {
    if [[ "$INSTALL_CERTBOT" != "true" ]]; then
        log_info "跳过Certbot安装"
        return 0
    fi

    log_info "安装Let's Encrypt Certbot..."

    case "$OS" in
        *Ubuntu*|*Debian*)
            apt-get install -y certbot python3-certbot-nginx
            ;;
        *CentOS*|*Red\ Hat*|*Rocky*|*AlmaLinux*)
            yum install -y certbot python3-certbot-nginx
            ;;
    esac

    log_success "Certbot安装完成"
}

# 配置防火墙
setup_firewall() {
    if [[ "$SETUP_FIREWALL" != "true" ]]; then
        log_info "跳过防火墙配置"
        return 0
    fi

    log_info "配置防火墙..."

    case "$OS" in
        *Ubuntu*|*Debian*)
            # 使用UFW
            if ! command -v ufw &> /dev/null; then
                apt-get install -y ufw
            fi

            # 基础规则
            ufw --force reset
            ufw default deny incoming
            ufw default allow outgoing

            # 允许SSH
            ufw allow ssh
            ufw allow 22/tcp

            # 允许HTTP/HTTPS
            ufw allow 80/tcp
            ufw allow 443/tcp

            # 允许应用端口
            ufw allow 9000/tcp    # Frontend
            ufw allow 8000/tcp    # Backend Pro1 API Gateway
            ufw allow 8100/tcp    # Backend Pro2 API Gateway
            
            # 监控端口（仅本地访问）
            ufw allow from 127.0.0.1 to any port 9090  # Prometheus
            ufw allow from 127.0.0.1 to any port 3000  # Grafana
            ufw allow from 127.0.0.1 to any port 5601  # Kibana

            # 启用防火墙
            ufw --force enable
            ;;
        *CentOS*|*Red\ Hat*|*Rocky*|*AlmaLinux*)
            # 使用Firewalld
            systemctl start firewalld
            systemctl enable firewalld

            # 基础规则
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --permanent --add-service=http
            firewall-cmd --permanent --add-service=https

            # 应用端口
            firewall-cmd --permanent --add-port=9000/tcp
            firewall-cmd --permanent --add-port=8000/tcp
            firewall-cmd --permanent --add-port=8100/tcp

            # 重载配置
            firewall-cmd --reload
            ;;
    esac

    log_success "防火墙配置完成"
}

# 优化系统参数
optimize_system() {
    log_info "优化系统参数..."

    # 内核参数优化
    cat > /etc/sysctl.d/99-saascontroldeck.conf << 'EOF'
# SaaS Control Deck 系统优化参数

# 网络优化
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_tw_buckets = 5000

# 文件句柄限制
fs.file-max = 65535
fs.nr_open = 65535

# 虚拟内存优化
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# Docker优化
vm.max_map_count = 262144
EOF

    # 应用内核参数
    sysctl -p /etc/sysctl.d/99-saascontroldeck.conf

    # 用户限制优化
    cat > /etc/security/limits.d/99-saascontroldeck.conf << 'EOF'
# SaaS Control Deck 用户限制优化

* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535

saascontrol soft nofile 65535
saascontrol hard nofile 65535
saascontrol soft nproc 65535
saascontrol hard nproc 65535
EOF

    log_success "系统参数优化完成"
}

# 安装监控工具
install_monitoring_tools() {
    log_info "安装系统监控工具..."

    case "$OS" in
        *Ubuntu*|*Debian*)
            apt-get install -y htop iotop nethogs ncdu tree jq
            ;;
        *CentOS*|*Red\ Hat*|*Rocky*|*AlmaLinux*)
            yum install -y htop iotop nethogs ncdu tree jq
            ;;
    esac

    log_success "监控工具安装完成"
}

# 配置日志轮转
setup_log_rotation() {
    log_info "配置日志轮转..."

    cat > /etc/logrotate.d/saascontroldeck << 'EOF'
/var/log/saascontroldeck/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 saascontrol saascontrol
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
        docker kill --signal="USR1" $(docker ps -q --filter "label=com.saascontroldeck.service") > /dev/null 2>&1 || true
    endscript
}
EOF

    log_success "日志轮转配置完成"
}

# 创建部署脚本
create_deployment_scripts() {
    log_info "创建部署脚本..."

    # 创建快速启动脚本
    cat > "$INSTALL_DIR/quick-start.sh" << 'EOF'
#!/bin/bash

# SaaS Control Deck 快速启动脚本

set -e

# 检查Docker服务
if ! systemctl is-active --quiet docker; then
    echo "启动Docker服务..."
    sudo systemctl start docker
fi

# 进入项目目录
cd /opt/saascontroldeck

# 启动所有服务
echo "启动SaaS Control Deck服务..."
docker-compose -f docker/environments/docker-compose.production.yml up -d

# 等待服务启动
echo "等待服务启动..."
sleep 30

# 健康检查
echo "执行健康检查..."
if curl -f -s http://localhost:9000/api/health > /dev/null; then
    echo "✅ 前端服务正常"
else
    echo "❌ 前端服务异常"
fi

if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend Pro1服务正常"
else
    echo "❌ Backend Pro1服务异常"
fi

if curl -f -s http://localhost:8100/health > /dev/null; then
    echo "✅ Backend Pro2服务正常"
else
    echo "❌ Backend Pro2服务异常"
fi

echo ""
echo "🚀 SaaS Control Deck 启动完成！"
echo "访问地址: http://$(curl -s ifconfig.me):9000"
echo ""
EOF

    chmod +x "$INSTALL_DIR/quick-start.sh"

    # 创建停止脚本
    cat > "$INSTALL_DIR/quick-stop.sh" << 'EOF'
#!/bin/bash

# SaaS Control Deck 快速停止脚本

set -e

echo "停止SaaS Control Deck服务..."

# 进入项目目录
cd /opt/saascontroldeck

# 停止所有服务
docker-compose -f docker/environments/docker-compose.production.yml down

echo "🛑 SaaS Control Deck 服务已停止"
EOF

    chmod +x "$INSTALL_DIR/quick-stop.sh"

    # 创建系统服务文件
    cat > /etc/systemd/system/saascontroldeck.service << 'EOF'
[Unit]
Description=SaaS Control Deck Application
Requires=docker.service
After=docker.service

[Service]
Type=forking
RemainAfterExit=yes
User=saascontrol
Group=saascontrol
WorkingDirectory=/opt/saascontroldeck
ExecStart=/opt/saascontroldeck/quick-start.sh
ExecStop=/opt/saascontroldeck/quick-stop.sh
TimeoutStartSec=300
TimeoutStopSec=120

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload

    log_success "部署脚本创建完成"
}

# 显示安装摘要
show_installation_summary() {
    echo ""
    echo "================================================"
    echo "         SaaS Control Deck 云服务器环境就绪"
    echo "================================================"
    echo ""
    echo "✅ 系统环境检查完成"
    echo "✅ 系统软件包更新完成"
    echo "✅ 服务用户创建完成: $SERVICE_USER"
    echo "✅ Docker安装完成: $(docker --version | cut -d' ' -f3)"
    echo "✅ Docker Compose安装完成: $(docker-compose --version | cut -d' ' -f4)"
    [[ "$INSTALL_NGINX" == "true" ]] && echo "✅ Nginx安装完成"
    [[ "$INSTALL_CERTBOT" == "true" ]] && echo "✅ Let's Encrypt Certbot安装完成"
    [[ "$SETUP_FIREWALL" == "true" ]] && echo "✅ 防火墙配置完成"
    echo "✅ 系统参数优化完成"
    echo "✅ 监控工具安装完成"
    echo "✅ 日志轮转配置完成"
    echo "✅ 部署脚本创建完成"
    echo ""
    echo "📁 安装目录: $INSTALL_DIR"
    echo "👤 服务用户: $SERVICE_USER"
    echo "📋 日志目录: /var/log/saascontroldeck"
    echo ""
    echo "下一步操作："
    echo "1. 将项目代码上传到 $INSTALL_DIR"
    echo "2. 配置环境变量 (.env.production)"
    echo "3. 运行部署脚本: ./scripts/deploy/deploy.sh -e production"
    echo "4. 配置域名和SSL证书 (如需要)"
    echo ""
    echo "快速启动命令："
    echo "  sudo -u $SERVICE_USER $INSTALL_DIR/quick-start.sh"
    echo ""
    echo "系统服务管理："
    echo "  systemctl start saascontroldeck"
    echo "  systemctl enable saascontroldeck"
    echo ""
    echo "================================================"
}

# 确认安装
confirm_installation() {
    if [[ "$AUTO_CONFIRM" == "true" ]]; then
        return 0
    fi

    echo ""
    echo "================================================"
    echo "        SaaS Control Deck 云服务器环境初始化"
    echo "================================================"
    echo ""
    echo "即将执行以下操作："
    echo "• 更新系统软件包"
    echo "• 创建服务用户: $SERVICE_USER"
    [[ "$INSTALL_DOCKER" == "true" ]] && echo "• 安装Docker和Docker Compose"
    [[ "$INSTALL_NGINX" == "true" ]] && echo "• 安装Nginx Web服务器"
    [[ "$INSTALL_CERTBOT" == "true" ]] && echo "• 安装Let's Encrypt SSL证书工具"
    [[ "$SETUP_FIREWALL" == "true" ]] && echo "• 配置防火墙安全规则"
    echo "• 优化系统参数"
    echo "• 安装监控工具"
    echo "• 配置日志管理"
    echo "• 创建部署脚本"
    echo ""
    echo "环境类型: $ENVIRONMENT"
    echo "安装目录: $INSTALL_DIR"
    echo ""

    read -p "确认执行安装? (y/N): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "安装已取消"
        exit 0
    fi
}

# 主函数
main() {
    # 创建日志文件
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"

    echo "================================================"
    echo "    SaaS Control Deck 云服务器环境初始化"
    echo "================================================"

    parse_args "$@"
    confirm_installation

    log_info "开始云服务器环境初始化..."
    log_info "日志文件: $LOG_FILE"

    # 执行安装步骤
    check_system
    update_system
    create_service_user
    install_docker
    install_docker_compose
    install_nginx
    install_certbot
    setup_firewall
    optimize_system
    install_monitoring_tools
    setup_log_rotation
    create_deployment_scripts

    show_installation_summary

    log_success "云服务器环境初始化完成！"
}

# 错误处理
trap 'log_error "环境初始化过程中发生错误，详细信息请查看: $LOG_FILE"; exit 1' ERR

# 执行主函数
main "$@"