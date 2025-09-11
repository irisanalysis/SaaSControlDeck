#!/bin/bash

# ===========================================
# GitHub Secrets 设置脚本
# ===========================================
# 用于批量设置GitHub Repository Secrets
# 使用GitHub CLI (gh) 工具

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖工具..."
    
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) 未安装。请安装: https://cli.github.com/"
        exit 1
    fi
    
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI 未认证。请运行: gh auth login"
        exit 1
    fi
    
    log_success "依赖检查完成"
}

# 设置基础密钥
setup_basic_secrets() {
    log_info "设置基础密钥..."
    
    # 生成强密钥
    SECRET_KEY=$(openssl rand -base64 32)
    
    # 基础认证密钥
    gh secret set SECRET_KEY --body "$SECRET_KEY" || log_warning "SECRET_KEY 设置失败"
    
    # 提示用户设置数据库URL
    log_warning "请手动设置以下密钥:"
    echo "  gh secret set DATABASE_URL --body 'postgresql+asyncpg://user:pass@host:port/db'"
    echo "  gh secret set REDIS_URL --body 'redis://:password@host:port/0'"
    
    log_success "基础密钥设置完成"
}

# 设置第三方服务密钥
setup_third_party_secrets() {
    log_info "设置第三方服务密钥..."
    
    log_warning "请手动设置以下第三方服务密钥:"
    echo "  # OpenAI"
    echo "  gh secret set OPENAI_API_KEY --body 'your_openai_key'"
    echo ""
    echo "  # Google AI (for Genkit)"
    echo "  gh secret set GOOGLE_GENAI_API_KEY --body 'your_google_ai_key'"
    echo ""
    echo "  # Sentry"
    echo "  gh secret set SENTRY_DSN --body 'https://your-sentry-dsn'"
    echo ""
    echo "  # Vercel"
    echo "  gh secret set VERCEL_TOKEN --body 'your_vercel_token'"
    echo "  gh secret set VERCEL_ORG_ID --body 'your_org_id'"
    echo "  gh secret set VERCEL_PROJECT_ID --body 'your_project_id'"
    
    log_success "第三方服务密钥提示完成"
}

# 设置Docker注册表密钥
setup_docker_secrets() {
    log_info "设置Docker注册表密钥..."
    
    log_warning "请手动设置Docker注册表密钥:"
    echo "  # Docker Hub"
    echo "  gh secret set DOCKER_REGISTRY --body 'docker.io'"
    echo "  gh secret set DOCKER_USERNAME --body 'your_username'"
    echo "  gh secret set DOCKER_PASSWORD --body 'your_password_or_token'"
    echo ""
    echo "  # 或者使用私有注册表"
    echo "  gh secret set DOCKER_REGISTRY --body 'your-registry.com'"
    
    log_success "Docker密钥设置提示完成"
}

# 设置部署密钥
setup_deployment_secrets() {
    log_info "设置部署密钥..."
    
    # 生成部署令牌
    DEPLOY_TOKEN=$(openssl rand -hex 32)
    
    log_warning "请手动设置部署相关密钥:"
    echo "  # 部署Webhook"
    echo "  gh secret set DEPLOY_WEBHOOK_URL --body 'https://your-server.com/webhook'"
    echo "  gh secret set DEPLOY_TOKEN --body '$DEPLOY_TOKEN'"
    echo ""
    echo "  # SSH密钥 (用于服务器部署)"
    echo "  gh secret set DEPLOY_SSH_KEY --body \"\$(cat ~/.ssh/id_rsa)\""
    echo "  gh secret set DEPLOY_HOST --body 'your-server.com'"
    echo "  gh secret set DEPLOY_USER --body 'deploy'"
    
    log_success "部署密钥设置提示完成"
}

# 验证密钥设置
verify_secrets() {
    log_info "验证密钥设置..."
    
    echo "当前已设置的密钥:"
    gh secret list
    
    log_success "密钥验证完成"
}

# 创建环境配置
setup_environments() {
    log_info "设置GitHub环境..."
    
    # 由于GitHub CLI不直接支持环境创建，提供手动指南
    log_warning "请在GitHub Web界面手动创建环境:"
    echo "  1. 访问: https://github.com/OWNER/REPO/settings/environments"
    echo "  2. 创建以下环境:"
    echo "     - development (无保护规则)"
    echo "     - staging (需要审查)"
    echo "     - production (严格保护规则)"
    echo "  3. 参考 .github/environments/ 目录中的配置文件"
    
    log_success "环境设置指南完成"
}

# 生成密钥报告
generate_secrets_report() {
    log_info "生成密钥设置报告..."
    
    cat > secrets-setup-report.md << EOF
# GitHub Secrets 设置报告

## 已设置的密钥

\`\`\`bash
$(gh secret list)
\`\`\`

## 待设置的密钥

### 必需密钥 (Core)
- [ ] SECRET_KEY (已自动生成)
- [ ] DATABASE_URL 
- [ ] REDIS_URL
- [ ] OPENAI_API_KEY

### Vercel部署密钥
- [ ] VERCEL_TOKEN
- [ ] VERCEL_ORG_ID  
- [ ] VERCEL_PROJECT_ID

### Docker注册表密钥
- [ ] DOCKER_REGISTRY
- [ ] DOCKER_USERNAME
- [ ] DOCKER_PASSWORD

### 可选密钥
- [ ] SENTRY_DSN
- [ ] GOOGLE_GENAI_API_KEY
- [ ] DEPLOY_WEBHOOK_URL
- [ ] DEPLOY_TOKEN

## 设置命令参考

\`\`\`bash
# 数据库
gh secret set DATABASE_URL --body "postgresql+asyncpg://user:pass@host:port/db"

# OpenAI
gh secret set OPENAI_API_KEY --body "sk-your-openai-key"

# Vercel
gh secret set VERCEL_TOKEN --body "your_vercel_token"
gh secret set VERCEL_ORG_ID --body "team_xxx"
gh secret set VERCEL_PROJECT_ID --body "prj_xxx"

# Docker
gh secret set DOCKER_REGISTRY --body "docker.io"
gh secret set DOCKER_USERNAME --body "your_username"
gh secret set DOCKER_PASSWORD --body "your_password"
\`\`\`

## 生成时间
$(date)
EOF

    log_success "密钥设置报告已生成: secrets-setup-report.md"
}

# 主函数
main() {
    echo "================================================"
    echo "    SaaS Control Deck - GitHub Secrets 设置"
    echo "================================================"
    echo ""
    
    check_dependencies
    echo ""
    
    setup_basic_secrets
    echo ""
    
    setup_third_party_secrets
    echo ""
    
    setup_docker_secrets
    echo ""
    
    setup_deployment_secrets
    echo ""
    
    setup_environments
    echo ""
    
    verify_secrets
    echo ""
    
    generate_secrets_report
    
    echo ""
    echo "================================================"
    log_success "GitHub Secrets 设置完成!"
    echo "================================================"
    echo ""
    log_info "下一步:"
    echo "1. 查看 secrets-setup-report.md 获取详细设置指南"
    echo "2. 根据提示手动设置必需的密钥"
    echo "3. 在GitHub Web界面创建环境配置"
    echo "4. 测试CI/CD流程"
}

# 执行主函数
main "$@"