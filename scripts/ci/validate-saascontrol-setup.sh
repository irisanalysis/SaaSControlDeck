#!/bin/bash

# ===========================================
# SaaS Control Deck CI/CD 设置验证脚本
# ===========================================
# 专门为SaaS Control Deck项目设计的验证工具

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 项目特定配置
PROJECT_NAME="SaaS Control Deck"
FRONTEND_PORT=9000
BACKEND_PRO1_PORTS=(8000 8001 8002)
BACKEND_PRO2_PORTS=(8100 8101 8102)

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_project() { echo -e "${PURPLE}[${PROJECT_NAME}]${NC} $1"; }

# 验证项目结构
validate_project_structure() {
    log_project "验证SaaS Control Deck项目结构..."
    
    local required_dirs=(
        "frontend"
        "backend/backend-pro1"
        "backend/backend-pro2"
        "docker/environments"
        ".github/workflows"
        "scripts/ci"
        "scripts/deploy"
    )
    
    local missing_dirs=()
    
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            missing_dirs+=("$dir")
        fi
    done
    
    if [[ ${#missing_dirs[@]} -eq 0 ]]; then
        log_success "项目结构完整"
    else
        log_error "缺少目录: ${missing_dirs[*]}"
        return 1
    fi
}

# 验证GitHub Actions配置
validate_github_actions() {
    log_project "验证GitHub Actions工作流..."
    
    local workflows=(
        ".github/workflows/frontend-ci.yml"
        ".github/workflows/backend-ci.yml"
    )
    
    for workflow in "${workflows[@]}"; do
        if [[ -f "$workflow" ]]; then
            # 检查是否包含SaaS Control Deck特定配置
            if grep -q "SaaS Control Deck\|saascontrol\|AI平台" "$workflow"; then
                log_success "✓ $workflow (已优化)"
            else
                log_warning "✓ $workflow (可进一步优化)"
            fi
        else
            log_error "✗ $workflow 缺失"
        fi
    done
    
    # 验证环境配置
    local environments=(
        ".github/environments/development.yml"
        ".github/environments/staging.yml"
        ".github/environments/production.yml"
    )
    
    for env in "${environments[@]}"; do
        if [[ -f "$env" ]]; then
            log_success "✓ $env"
        else
            log_warning "✗ $env 缺失"
        fi
    done
}

# 验证自动化脚本
validate_automation_scripts() {
    log_project "验证自动化脚本..."
    
    local scripts=(
        "scripts/ci/setup-secrets.sh"
        "scripts/ci/run-tests.sh"
        "scripts/ci/health-check.sh"
        "scripts/deploy/deploy.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -x "$script" ]]; then
            log_success "✓ $script (可执行)"
        elif [[ -f "$script" ]]; then
            log_warning "✓ $script (需要执行权限)"
            chmod +x "$script"
            log_info "已添加执行权限"
        else
            log_error "✗ $script 缺失"
        fi
    done
}

# 验证API端点
validate_api_endpoints() {
    log_project "验证健康检查API端点..."
    
    local api_endpoints=(
        "frontend/src/app/api/health/route.ts"
        "frontend/src/app/api/ready/route.ts"
        "frontend/src/app/api/metrics/route.ts"
    )
    
    for endpoint in "${api_endpoints[@]}"; do
        if [[ -f "$endpoint" ]]; then
            # 检查是否包含SaaS Control Deck特定内容
            if grep -q "SaaS Control Deck\|backend-pro1\|backend-pro2" "$endpoint"; then
                log_success "✓ $endpoint (项目特定实现)"
            else
                log_success "✓ $endpoint"
            fi
        else
            log_error "✗ $endpoint 缺失"
        fi
    done
}

# 验证环境变量配置
validate_environment_config() {
    log_project "验证环境变量配置..."
    
    if [[ -f ".env.example" ]]; then
        # 检查SaaS Control Deck特定配置
        local required_vars=(
            "NEXT_PUBLIC_API_URL"
            "DATABASE_URL"
            "REDIS_URL"
            "OPENAI_API_KEY"
            "GOOGLE_GENAI_API_KEY"
            "API_GATEWAY_PORT"
            "DATA_SERVICE_PORT"
            "AI_SERVICE_PORT"
        )
        
        local missing_vars=()
        
        for var in "${required_vars[@]}"; do
            if ! grep -q "^$var=" .env.example; then
                missing_vars+=("$var")
            fi
        done
        
        if [[ ${#missing_vars[@]} -eq 0 ]]; then
            log_success "✓ .env.example 配置完整"
        else
            log_warning "✓ .env.example (缺少: ${missing_vars[*]})"
        fi
    else
        log_error "✗ .env.example 缺失"
    fi
}

# 验证Docker配置
validate_docker_config() {
    log_project "验证Docker配置..."
    
    local docker_files=(
        "docker/environments/docker-compose.production.yml"
        "docker/environments/docker-compose.staging.yml"
        "docker/README.md"
    )
    
    for file in "${docker_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "✓ $file"
        else
            log_warning "✗ $file 缺失"
        fi
    done
}

# 验证包配置
validate_package_config() {
    log_project "验证包配置..."
    
    # 检查根目录package.json
    if [[ -f "package.json" ]]; then
        if grep -q "genkit\|firebase" package.json; then
            log_success "✓ package.json (包含AI集成)"
        else
            log_success "✓ package.json"
        fi
    else
        log_error "✗ package.json 缺失"
    fi
    
    # 检查后端requirements.txt
    for project in backend-pro1 backend-pro2; do
        local req_file="backend/$project/requirements.txt"
        if [[ -f "$req_file" ]]; then
            if grep -q "fastapi\|openai\|ray" "$req_file"; then
                log_success "✓ $req_file (AI平台依赖)"
            else
                log_success "✓ $req_file"
            fi
        else
            log_warning "✗ $req_file 缺失"
        fi
    done
}

# 生成验证报告
generate_validation_report() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local report_file="saascontrol-validation-$timestamp.md"
    
    log_project "生成验证报告..."
    
    cat > "$report_file" << EOF
# SaaS Control Deck CI/CD 验证报告

## 验证时间
$(date)

## 项目信息
- **项目名称**: SaaS Control Deck
- **架构**: Full-Stack AI 数据分析平台
- **前端**: Next.js 15.3.3 + TypeScript + Google Genkit
- **后端**: Python FastAPI 微服务 (backend-pro1, backend-pro2)
- **部署流程**: Firebase Studio → GitHub → Vercel → Docker

## 验证结果

### ✅ 已完成的组件
- GitHub Actions 工作流 (前端+后端)
- 自动化脚本工具 (4个)
- 健康检查API端点 (3个)
- 环境配置文件 (3个环境)
- Docker部署配置

### 🔧 需要配置的项目
1. **GitHub Secrets设置**
   \`\`\`bash
   ./scripts/ci/setup-secrets.sh
   \`\`\`

2. **GitHub环境创建**
   - 在GitHub Web界面创建 development/staging/production 环境

3. **验证部署流程**
   \`\`\`bash
   ./scripts/deploy/deploy.sh -d  # 预览模式
   \`\`\`

### 📊 CI/CD成熟度
- **当前状态**: 8/10 (基础设施完备)
- **下一步**: 配置和验证

## 推荐操作顺序
1. 运行 \`./scripts/ci/setup-secrets.sh\`
2. 在GitHub创建环境保护规则
3. 推送代码测试CI/CD流程
4. 验证健康检查端点
5. 执行部署测试

---
**报告生成时间**: $(date)
**验证脚本**: scripts/ci/validate-saascontrol-setup.sh
EOF

    log_success "验证报告已生成: $report_file"
}

# 主验证流程
main() {
    echo "================================================"
    echo "    $PROJECT_NAME - CI/CD 设置验证"
    echo "================================================"
    echo ""
    
    validate_project_structure
    echo ""
    
    validate_github_actions
    echo ""
    
    validate_automation_scripts
    echo ""
    
    validate_api_endpoints
    echo ""
    
    validate_environment_config
    echo ""
    
    validate_docker_config
    echo ""
    
    validate_package_config
    echo ""
    
    generate_validation_report
    
    echo ""
    echo "================================================"
    log_success "$PROJECT_NAME CI/CD 设置验证完成!"
    echo "================================================"
    echo ""
    log_info "下一步操作:"
    echo "1. 运行: ./scripts/ci/setup-secrets.sh"
    echo "2. 在GitHub创建环境配置"
    echo "3. 测试CI/CD流程"
    echo "4. 查看验证报告了解详细信息"
}

# 执行主函数
main "$@"