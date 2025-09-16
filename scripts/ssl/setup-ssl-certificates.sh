#!/bin/bash

# ===========================================
# SaaS Control Deck - SSL证书自动化配置脚本
# ===========================================
# 使用 Let's Encrypt 为云服务器自动配置SSL证书

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

# 默认域名配置（需要根据实际情况修改）
PRIMARY_DOMAIN=""
SUBDOMAINS="www api grafana kibana minio-console"
EMAIL=""
WEBROOT_PATH="/var/www/certbot"
NGINX_CONF_PATH="/etc/nginx"
SSL_RENEWAL_SCRIPT="/usr/local/bin/renew-ssl-certificates.sh"

# 参数配置
DRY_RUN=false
FORCE_RENEWAL=false
STAGING=false
AUTO_CONFIRM=false
SETUP_CRON=true

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 显示帮助
show_help() {
    cat << EOF
SaaS Control Deck SSL证书自动化配置脚本

用法: $0 [选项]

选项:
    -d, --domain DOMAIN       主域名 (必需)
    -e, --email EMAIL         邮箱地址 (必需)
    -s, --subdomains LIST     子域名列表，用逗号分隔 (默认: www,api,grafana,kibana,minio-console)
    --staging                 使用Let's Encrypt测试环境
    --dry-run                 预览模式，不实际申请证书
    --force                   强制重新申请证书
    --skip-cron               跳过自动续期定时任务设置
    -y, --yes                 自动确认所有选项
    -h, --help                显示此帮助

示例:
    $0 -d yourdomain.com -e admin@yourdomain.com
    $0 -d example.com -e admin@example.com -s "www,api,admin" --staging
    $0 -d mydomain.com -e user@mydomain.com --force

注意事项:
1. 运行前请确保域名DNS已正确指向服务器IP
2. 确保80端口可以从外网访问（用于域名验证）
3. 建议先使用 --staging 测试，避免触发Let's Encrypt速率限制
4. 脚本会自动配置Nginx以支持SSL

域名配置要求:
- 主域名: yourdomain.com
- 子域名: www.yourdomain.com, api.yourdomain.com 等
- 所有域名都必须指向当前服务器的公网IP
EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--domain)
                PRIMARY_DOMAIN="$2"
                shift 2
                ;;
            -e|--email)
                EMAIL="$2"
                shift 2
                ;;
            -s|--subdomains)
                SUBDOMAINS="$2"
                shift 2
                ;;
            --staging)
                STAGING=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE_RENEWAL=true
                shift
                ;;
            --skip-cron)
                SETUP_CRON=false
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

# 验证参数
validate_args() {
    if [[ -z "$PRIMARY_DOMAIN" ]]; then
        log_error "必须指定主域名"
        log_error "使用 -d yourdomain.com 指定域名"
        exit 1
    fi

    if [[ -z "$EMAIL" ]]; then
        log_error "必须指定邮箱地址"
        log_error "使用 -e admin@yourdomain.com 指定邮箱"
        exit 1
    fi

    # 验证邮箱格式
    if ! echo "$EMAIL" | grep -E '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' > /dev/null; then
        log_error "邮箱格式无效: $EMAIL"
        exit 1
    fi

    # 验证域名格式
    if ! echo "$PRIMARY_DOMAIN" | grep -E '^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$' > /dev/null; then
        log_error "域名格式无效: $PRIMARY_DOMAIN"
        exit 1
    fi
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."

    # 检查root权限
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi

    # 检查Certbot
    if ! command -v certbot &> /dev/null; then
        log_error "Certbot未安装"
        log_info "请先运行云服务器环境初始化脚本"
        exit 1
    fi

    # 检查Nginx
    if ! command -v nginx &> /dev/null; then
        log_error "Nginx未安装"
        log_info "请先运行云服务器环境初始化脚本"
        exit 1
    fi

    # 检查80端口
    if ! netstat -tuln | grep ':80 ' > /dev/null; then
        log_warning "80端口未监听，这可能影响域名验证"
    fi

    # 检查443端口
    if netstat -tuln | grep ':443 ' > /dev/null; then
        log_info "检测到443端口已占用，将在证书申请后重启Nginx"
    fi

    log_success "系统要求检查完成"
}

# 创建证书验证目录
setup_webroot() {
    log_info "设置证书验证目录..."

    mkdir -p "$WEBROOT_PATH"
    chown -R nginx:nginx "$WEBROOT_PATH" 2>/dev/null || chown -R www-data:www-data "$WEBROOT_PATH" 2>/dev/null || true
    chmod 755 "$WEBROOT_PATH"

    # 创建测试文件
    echo "SSL certificate verification" > "$WEBROOT_PATH/test.txt"

    log_success "证书验证目录设置完成: $WEBROOT_PATH"
}

# 配置临时Nginx配置（用于证书申请）
setup_temp_nginx_config() {
    log_info "配置临时Nginx配置..."

    # 备份当前配置
    if [[ -f "$NGINX_CONF_PATH/nginx.conf" ]]; then
        cp "$NGINX_CONF_PATH/nginx.conf" "$NGINX_CONF_PATH/nginx.conf.backup.$(date +%Y%m%d_%H%M%S)"
    fi

    # 创建临时配置
    cat > "$NGINX_CONF_PATH/conf.d/temp-ssl-setup.conf" << EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name $PRIMARY_DOMAIN $(echo "$SUBDOMAINS" | sed "s/,/ /g" | sed "s/\([^ ]*\)/\1.$PRIMARY_DOMAIN/g");
    
    root $WEBROOT_PATH;
    index index.html;
    
    # Let's Encrypt验证
    location ^~ /.well-known/acme-challenge/ {
        root $WEBROOT_PATH;
        try_files \$uri =404;
    }
    
    # 测试页面
    location / {
        return 200 'SSL Certificate Setup in Progress';
        add_header Content-Type text/plain;
    }
}
EOF

    # 测试Nginx配置
    if nginx -t; then
        systemctl reload nginx
        log_success "临时Nginx配置设置完成"
    else
        log_error "Nginx配置测试失败"
        exit 1
    fi
}

# 验证域名解析
verify_dns_resolution() {
    log_info "验证域名解析..."

    local server_ip=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "unknown")
    
    if [[ "$server_ip" == "unknown" ]]; then
        log_warning "无法获取服务器公网IP，跳过DNS验证"
        return 0
    fi

    log_info "服务器公网IP: $server_ip"

    # 检查主域名
    local domain_ip=$(dig +short "$PRIMARY_DOMAIN" 2>/dev/null | tail -1)
    if [[ "$domain_ip" != "$server_ip" ]]; then
        log_warning "域名 $PRIMARY_DOMAIN 解析IP ($domain_ip) 与服务器IP ($server_ip) 不匹配"
        if [[ "$AUTO_CONFIRM" != "true" ]]; then
            read -p "是否继续? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "操作已取消"
                exit 0
            fi
        fi
    else
        log_success "主域名解析正确: $PRIMARY_DOMAIN -> $server_ip"
    fi

    # 检查子域名
    IFS=',' read -ra SUBDOMAIN_ARRAY <<< "$SUBDOMAINS"
    for subdomain in "${SUBDOMAIN_ARRAY[@]}"; do
        local full_domain="${subdomain}.${PRIMARY_DOMAIN}"
        local sub_ip=$(dig +short "$full_domain" 2>/dev/null | tail -1)
        
        if [[ "$sub_ip" != "$server_ip" ]]; then
            log_warning "子域名 $full_domain 解析异常"
        else
            log_success "子域名解析正确: $full_domain -> $server_ip"
        fi
    done
}

# 申请SSL证书
request_ssl_certificate() {
    log_info "申请SSL证书..."

    # 构建域名列表
    local domain_list="-d $PRIMARY_DOMAIN"
    IFS=',' read -ra SUBDOMAIN_ARRAY <<< "$SUBDOMAINS"
    for subdomain in "${SUBDOMAIN_ARRAY[@]}"; do
        domain_list="$domain_list -d ${subdomain}.${PRIMARY_DOMAIN}"
    done

    # 构建Certbot命令
    local certbot_cmd="certbot certonly --webroot -w $WEBROOT_PATH $domain_list --email $EMAIL --agree-tos --non-interactive"
    
    # 添加可选参数
    if [[ "$STAGING" == "true" ]]; then
        certbot_cmd="$certbot_cmd --staging"
        log_warning "使用Let's Encrypt测试环境"
    fi

    if [[ "$FORCE_RENEWAL" == "true" ]]; then
        certbot_cmd="$certbot_cmd --force-renewal"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        certbot_cmd="$certbot_cmd --dry-run"
        log_info "预览模式，不会实际申请证书"
    fi

    # 执行Certbot命令
    log_info "执行命令: $certbot_cmd"
    
    if $certbot_cmd; then
        if [[ "$DRY_RUN" != "true" ]]; then
            log_success "SSL证书申请成功！"
            
            # 显示证书信息
            log_info "证书详情："
            certbot certificates | grep -A 10 "$PRIMARY_DOMAIN" || true
        else
            log_success "预览模式完成，证书申请测试通过"
        fi
    else
        log_error "SSL证书申请失败"
        log_error "请检查："
        log_error "1. 域名DNS是否正确指向此服务器"
        log_error "2. 80端口是否可以从外网访问"
        log_error "3. Let's Encrypt速率限制（建议使用--staging测试）"
        exit 1
    fi
}

# 配置生产Nginx配置
setup_production_nginx_config() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "预览模式：跳过生产Nginx配置"
        return 0
    fi

    log_info "配置生产Nginx配置..."

    # 删除临时配置
    rm -f "$NGINX_CONF_PATH/conf.d/temp-ssl-setup.conf"

    # 复制生产配置
    if [[ -f "$PROJECT_ROOT/nginx/nginx-cloud.conf" ]]; then
        # 替换域名占位符
        sed "s/yourdomain\.com/$PRIMARY_DOMAIN/g" "$PROJECT_ROOT/nginx/nginx-cloud.conf" > "$NGINX_CONF_PATH/nginx.conf"
        
        # 测试配置
        if nginx -t; then
            systemctl reload nginx
            log_success "生产Nginx配置设置完成"
        else
            log_error "生产Nginx配置测试失败"
            # 恢复备份
            if [[ -f "$NGINX_CONF_PATH/nginx.conf.backup.$(date +%Y%m%d)_"* ]]; then
                cp "$NGINX_CONF_PATH/nginx.conf.backup."* "$NGINX_CONF_PATH/nginx.conf"
                nginx -t && systemctl reload nginx
                log_info "已恢复Nginx配置备份"
            fi
            exit 1
        fi
    else
        log_warning "生产Nginx配置文件不存在，使用默认配置"
    fi
}

# 创建SSL证书自动续期脚本
create_renewal_script() {
    if [[ "$DRY_RUN" == "true" || "$SETUP_CRON" != "true" ]]; then
        log_info "跳过SSL自动续期脚本创建"
        return 0
    fi

    log_info "创建SSL证书自动续期脚本..."

    cat > "$SSL_RENEWAL_SCRIPT" << 'EOF'
#!/bin/bash

# SaaS Control Deck SSL证书自动续期脚本
# 由setup-ssl-certificates.sh自动生成

set -e

LOG_FILE="/var/log/ssl-renewal.log"
DATE=$(date)

echo "[$DATE] 开始SSL证书续期检查" >> "$LOG_FILE"

# 尝试续期证书
if certbot renew --quiet --no-self-upgrade; then
    echo "[$DATE] 证书续期检查完成" >> "$LOG_FILE"
    
    # 检查是否有证书被续期
    if certbot renew --dry-run --quiet 2>/dev/null; then
        echo "[$DATE] 证书续期成功，重启Nginx" >> "$LOG_FILE"
        systemctl reload nginx
        
        # 发送通知（可选）
        # echo "SSL证书已自动续期" | mail -s "SSL证书续期通知" admin@yourdomain.com
    fi
else
    echo "[$DATE] 证书续期失败" >> "$LOG_FILE"
    
    # 发送错误通知（可选）
    # echo "SSL证书续期失败，请手动检查" | mail -s "SSL证书续期失败" admin@yourdomain.com
    
    exit 1
fi

echo "[$DATE] SSL证书续期脚本执行完成" >> "$LOG_FILE"
EOF

    chmod +x "$SSL_RENEWAL_SCRIPT"
    
    # 设置crontab定时任务
    local cron_job="0 2 * * * $SSL_RENEWAL_SCRIPT"
    
    # 检查是否已存在定时任务
    if ! crontab -l 2>/dev/null | grep -q "$SSL_RENEWAL_SCRIPT"; then
        (crontab -l 2>/dev/null; echo "$cron_job") | crontab -
        log_success "SSL自动续期定时任务设置完成（每天凌晨2点检查）"
    else
        log_info "SSL自动续期定时任务已存在"
    fi

    log_success "SSL自动续期脚本创建完成: $SSL_RENEWAL_SCRIPT"
}

# 测试SSL证书
test_ssl_certificate() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "预览模式：跳过SSL证书测试"
        return 0
    fi

    log_info "测试SSL证书..."

    # 等待Nginx重载完成
    sleep 5

    # 测试HTTPS连接
    local test_domains=("$PRIMARY_DOMAIN")
    IFS=',' read -ra SUBDOMAIN_ARRAY <<< "$SUBDOMAINS"
    for subdomain in "${SUBDOMAIN_ARRAY[@]}"; do
        if [[ "$subdomain" != "minio-console" ]]; then  # 跳过可能不可用的服务
            test_domains+=("${subdomain}.${PRIMARY_DOMAIN}")
        fi
    done

    local success_count=0
    local total_count=${#test_domains[@]}

    for domain in "${test_domains[@]}"; do
        log_info "测试域名: $domain"
        
        if curl -s -o /dev/null -w "%{http_code}" "https://$domain" --max-time 10 | grep -E "^(200|301|302|404)$" > /dev/null; then
            log_success "✓ $domain SSL连接正常"
            ((success_count++))
        else
            log_warning "✗ $domain SSL连接失败"
        fi
    done

    if [[ $success_count -eq $total_count ]]; then
        log_success "所有域名SSL证书测试通过！"
    elif [[ $success_count -gt 0 ]]; then
        log_warning "部分域名SSL证书测试通过 ($success_count/$total_count)"
    else
        log_error "所有域名SSL证书测试失败"
        return 1
    fi
}

# 显示SSL配置摘要
show_ssl_summary() {
    echo ""
    echo "================================================"
    echo "         SSL证书配置完成"
    echo "================================================"
    echo ""
    echo "主域名: $PRIMARY_DOMAIN"
    echo "子域名: $SUBDOMAINS"
    echo "邮箱: $EMAIL"
    
    if [[ "$STAGING" == "true" ]]; then
        echo "环境: Let's Encrypt 测试环境"
    else
        echo "环境: Let's Encrypt 生产环境"
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "模式: 预览模式（未实际申请证书）"
    else
        echo "模式: 生产模式"
        echo ""
        echo "证书文件位置:"
        echo "  证书: /etc/letsencrypt/live/$PRIMARY_DOMAIN/fullchain.pem"
        echo "  私钥: /etc/letsencrypt/live/$PRIMARY_DOMAIN/privkey.pem"
        echo ""
        echo "访问地址:"
        echo "  主站: https://$PRIMARY_DOMAIN"
        IFS=',' read -ra SUBDOMAIN_ARRAY <<< "$SUBDOMAINS"
        for subdomain in "${SUBDOMAIN_ARRAY[@]}"; do
            echo "  $subdomain: https://${subdomain}.${PRIMARY_DOMAIN}"
        done
        
        if [[ "$SETUP_CRON" == "true" ]]; then
            echo ""
            echo "自动续期: 已设置（每天凌晨2点检查）"
            echo "续期脚本: $SSL_RENEWAL_SCRIPT"
            echo "续期日志: /var/log/ssl-renewal.log"
        fi
    fi
    
    echo ""
    echo "================================================"
}

# 确认SSL配置
confirm_ssl_setup() {
    if [[ "$AUTO_CONFIRM" == "true" ]]; then
        return 0
    fi

    echo ""
    echo "================================================"
    echo "        SSL证书配置确认"
    echo "================================================"
    echo ""
    echo "即将为以下域名申请SSL证书："
    echo "  主域名: $PRIMARY_DOMAIN"
    echo "  子域名: $SUBDOMAINS"
    echo "  邮箱: $EMAIL"
    
    if [[ "$STAGING" == "true" ]]; then
        echo "  环境: Let's Encrypt 测试环境"
    else
        echo "  环境: Let's Encrypt 生产环境"
    fi
    
    echo ""
    echo "请确保："
    echo "1. 所有域名都已正确解析到此服务器"
    echo "2. 80端口可以从外网访问"
    echo "3. 首次申请建议使用 --staging 测试"
    echo ""

    read -p "确认继续申请SSL证书? (y/N): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "SSL配置已取消"
        exit 0
    fi
}

# 清理函数
cleanup() {
    # 清理临时文件
    rm -f "$NGINX_CONF_PATH/conf.d/temp-ssl-setup.conf" 2>/dev/null || true
}

# 主函数
main() {
    echo "================================================"
    echo "    SaaS Control Deck SSL证书自动化配置"
    echo "================================================"

    parse_args "$@"
    validate_args
    confirm_ssl_setup

    # 设置清理陷阱
    trap cleanup EXIT

    check_requirements
    setup_webroot
    setup_temp_nginx_config
    verify_dns_resolution
    request_ssl_certificate
    setup_production_nginx_config
    create_renewal_script
    test_ssl_certificate

    show_ssl_summary

    if [[ "$DRY_RUN" == "true" ]]; then
        log_success "SSL证书配置预览完成！"
        log_info "使用相同参数但不加 --dry-run 来实际申请证书"
    else
        log_success "SSL证书配置完成！"
    fi
}

# 错误处理
trap 'log_error "SSL配置过程中发生错误"; cleanup; exit 1' ERR

# 执行主函数
main "$@"