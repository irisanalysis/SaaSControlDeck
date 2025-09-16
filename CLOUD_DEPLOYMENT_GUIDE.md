# SaaS Control Deck 云服务器部署完整指南

## 概述

本指南详细说明如何将 SaaS Control Deck 全栈AI平台部署到云服务器上。我们的平台采用现代化的微服务架构，支持高可用性、自动扩展和完整的监控体系。

## 🏗️ 架构概览

### 技术栈
- **前端**: Next.js 15.3.3 + TypeScript + Tailwind CSS + Google Genkit AI
- **后端**: Python FastAPI 微服务架构
- **数据库**: PostgreSQL 15 (主数据库)
- **缓存**: Redis 7 (高性能缓存)
- **存储**: MinIO (对象存储)
- **计算**: Ray (分布式AI计算)
- **监控**: Prometheus + Grafana + Elasticsearch + Kibana
- **代理**: Nginx (负载均衡和SSL终止)

### 服务架构
```
┌─────────────────────────────────────────────────────────────┐
│                    Nginx Load Balancer                      │
│                   (SSL + Rate Limiting)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
┌─────────┐    ┌─────────────┐    ┌─────────────┐
│Frontend │    │   Pro1 API  │    │   Pro2 API  │
│Next.js  │    │ Gateway:8000│    │ Gateway:8100│
│  :9000  │    │             │    │             │
└─────────┘    └─────────────┘    └─────────────┘
                      │                 │
              ┌───────┼───────┐ ┌───────┼───────┐
              ▼       ▼       ▼ ▼       ▼       ▼
        ┌─────────┐┌─────────┐┌─────────┐┌─────────┐
        │Data Svc ││AI Service││Data Svc ││AI Service│
        │  :8001  ││  :8002  ││  :8101  ││  :8102  │
        └─────────┘└─────────┘└─────────┘└─────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
  ┌───────────┐ ┌───────────┐ ┌──────────┐
  │PostgreSQL │ │   Redis   │ │  MinIO   │
  │   :5432   │ │   :6379   │ │  :9000   │
  └───────────┘ └───────────┘ └──────────┘
```

## 🚀 快速部署

### 先决条件
- Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- 最小 4GB RAM, 2 CPU核心 (推荐 8GB RAM, 4 CPU核心)
- 至少 20GB 可用磁盘空间
- 云服务器具有公网IP和域名

### 一键部署流程

#### 1. 环境初始化
```bash
# 下载项目代码到云服务器
git clone <your-repository-url> /tmp/saascontroldeck
cd /tmp/saascontroldeck

# 运行环境初始化脚本
sudo ./scripts/deploy/cloud-server-setup.sh -y

# 等待环境初始化完成（约10-15分钟）
```

#### 2. 配置环境变量
```bash
# 复制并编辑环境配置
sudo cp .env.cloud /opt/saascontroldeck/.env
sudo nano /opt/saascontroldeck/.env

# 必须修改的关键配置：
# - PRIMARY_DOMAIN=yourdomain.com
# - SECRET_KEY_PRO1=your_secure_secret_key_here
# - POSTGRES_PASSWORD=your_secure_database_password
# - REDIS_PASSWORD=your_secure_redis_password
# - MINIO_ACCESS_KEY=your_minio_access_key
# - MINIO_SECRET_KEY=your_minio_secret_key
# - OPENAI_API_KEY=your_openai_api_key
# - GOOGLE_GENAI_API_KEY=your_google_ai_key
```

#### 3. SSL证书配置
```bash
# 配置SSL证书（确保域名已指向服务器）
sudo ./scripts/ssl/setup-ssl-certificates.sh \
  -d yourdomain.com \
  -e admin@yourdomain.com \
  --staging  # 首次建议使用测试环境

# 测试通过后，申请正式证书
sudo ./scripts/ssl/setup-ssl-certificates.sh \
  -d yourdomain.com \
  -e admin@yourdomain.com
```

#### 4. 执行部署
```bash
# 执行完整部署流水线
sudo -u saascontrol ./scripts/deploy/cloud-deploy-pipeline.sh

# 或者预览模式检查
sudo -u saascontrol ./scripts/deploy/cloud-deploy-pipeline.sh --dry-run -v
```

#### 5. 验证部署
```bash
# 检查服务状态
sudo -u saascontrol docker-compose -f /opt/saascontroldeck/docker/cloud-deployment/docker-compose.cloud.yml ps

# 验证服务健康
curl -f https://yourdomain.com/api/health
curl -f https://api.yourdomain.com/v1/pro1/health
curl -f https://api.yourdomain.com/v1/pro2/health
```

## 📋 详细配置说明

### 环境变量配置

#### 核心安全配置
```bash
# 生产环境必须更改的密钥
SECRET_KEY_PRO1=CHANGE_THIS_super_secret_key_pro1_min_32_chars_production_2024
SECRET_KEY_PRO2=CHANGE_THIS_super_secret_key_pro2_min_32_chars_production_2024
POSTGRES_PASSWORD=CHANGE_DATABASE_PASSWORD_SECURE_PASSWORD_HERE
REDIS_PASSWORD=CHANGE_REDIS_PASSWORD_SECURE_HERE
```

#### AI服务配置
```bash
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=4000

# Google AI配置
GOOGLE_GENAI_API_KEY=your_google_ai_api_key_here
NEXT_PUBLIC_GENKIT_ENV=production
```

#### 域名和网络配置
```bash
# 主域名配置
PRIMARY_DOMAIN=yourdomain.com
WWW_DOMAIN=www.yourdomain.com
API_DOMAIN=api.yourdomain.com

# CORS配置
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,https://api.yourdomain.com
```

### 微服务端口配置

| 服务类型 | Pro1端口 | Pro2端口 | 说明 |
|---------|----------|----------|------|
| API Gateway | 8000 | 8100 | 主API入口 |
| Data Service | 8001 | 8101 | 数据处理服务 |
| AI Service | 8002 | 8102 | AI分析服务 |

### 基础设施端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Frontend | 9000 | Next.js应用 |
| PostgreSQL | 5432 | 主数据库 |
| Redis | 6379 | 缓存服务 |
| MinIO API | 9010 | 对象存储API |
| MinIO Console | 9011 | 对象存储控制台 |
| Prometheus | 9090 | 监控指标收集 |
| Grafana | 3000 | 监控仪表板 |
| Elasticsearch | 9200 | 日志存储 |
| Kibana | 5601 | 日志分析 |

## 🔧 高级配置

### 自定义域名配置
```bash
# 编辑Nginx配置
sudo nano /opt/saascontroldeck/nginx/nginx-cloud.conf

# 替换示例域名
sed -i 's/yourdomain\.com/your-actual-domain.com/g' /opt/saascontroldeck/nginx/nginx-cloud.conf

# 重载Nginx配置
sudo nginx -t && sudo systemctl reload nginx
```

### 数据库优化配置
```bash
# 根据服务器规格调整PostgreSQL配置
sudo nano /opt/saascontroldeck/scripts/postgres/postgresql-cloud.conf

# 4GB内存服务器推荐配置
shared_buffers = 1GB
effective_cache_size = 3GB
maintenance_work_mem = 256MB
work_mem = 16MB

# 8GB内存服务器推荐配置
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
work_mem = 32MB
```

### 监控告警配置
```bash
# 配置Prometheus告警规则
sudo mkdir -p /opt/saascontroldeck/monitoring/prometheus/rules

# 创建基础告警规则
cat > /opt/saascontroldeck/monitoring/prometheus/rules/saascontrol-alerts.yml << 'EOF'
groups:
- name: saascontrol.rules
  rules:
  - alert: HighCPUUsage
    expr: cpu_usage_percent > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "CPU使用率过高"
      
  - alert: HighMemoryUsage
    expr: memory_usage_percent > 85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "内存使用率过高"
      
  - alert: ServiceDown
    expr: up{job=~"frontend-app|api-gateway-.*"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "关键服务宕机"
EOF
```

## 📊 监控和运维

### 监控访问地址
- **应用监控**: https://grafana.yourdomain.com
- **系统指标**: https://yourdomain.com:9090 (Prometheus)
- **日志分析**: https://kibana.yourdomain.com
- **文件存储**: https://minio-console.yourdomain.com

### 日常运维命令
```bash
# 查看服务状态
sudo -u saascontrol docker-compose -f /opt/saascontroldeck/docker/cloud-deployment/docker-compose.cloud.yml ps

# 查看服务日志
sudo -u saascontrol docker-compose -f /opt/saascontroldeck/docker/cloud-deployment/docker-compose.cloud.yml logs -f frontend-app

# 重启特定服务
sudo -u saascontrol docker-compose -f /opt/saascontroldeck/docker/cloud-deployment/docker-compose.cloud.yml restart api-gateway-pro1

# 更新服务
sudo -u saascontrol ./scripts/deploy/cloud-deploy-pipeline.sh --services frontend

# 数据库备份
sudo -u saascontrol docker-compose -f /opt/saascontroldeck/docker/cloud-deployment/docker-compose.cloud.yml exec postgres-primary pg_dump -U saasuser saascontroldeck_production > backup.sql
```

### 健康检查端点
```bash
# 检查所有服务健康状态
./scripts/ci/health-check.sh -t all

# 单独检查特定服务
curl -f https://yourdomain.com/api/health
curl -f https://api.yourdomain.com/v1/pro1/health  
curl -f https://api.yourdomain.com/v1/pro2/health
```

## 🔒 安全配置

### SSL证书管理
```bash
# 查看证书状态
sudo certbot certificates

# 手动续期证书
sudo certbot renew

# 测试自动续期
sudo certbot renew --dry-run

# 查看续期日志
sudo cat /var/log/ssl-renewal.log
```

### 防火墙配置
```bash
# 查看防火墙状态
sudo ufw status

# 添加自定义规则
sudo ufw allow from 192.168.1.0/24 to any port 9090  # 内网访问Prometheus
sudo ufw allow from trusted_ip to any port 3000      # 信任IP访问Grafana
```

### 备份和恢复
```bash
# 创建完整系统备份
sudo ./scripts/deploy/cloud-deploy-pipeline.sh --skip-monitoring

# 手动数据库备份
sudo -u saascontrol docker exec postgres-primary pg_dumpall -U saasuser > full_backup_$(date +%Y%m%d).sql

# 恢复数据库
sudo -u saascontrol docker exec -i postgres-primary psql -U saasuser < backup_file.sql
```

## 🚀 性能优化

### 系统级优化
```bash
# 调整系统参数
echo 'vm.swappiness = 10' >> /etc/sysctl.conf
echo 'net.core.somaxconn = 65535' >> /etc/sysctl.conf
sysctl -p

# 优化文件句柄限制
echo '* soft nofile 65535' >> /etc/security/limits.conf
echo '* hard nofile 65535' >> /etc/security/limits.conf
```

### 应用层优化
```bash
# 调整Docker服务配置
sudo nano /opt/saascontroldeck/docker/cloud-deployment/docker-compose.cloud.yml

# 根据服务器规格调整内存限制
deploy:
  resources:
    limits:
      memory: 4G  # 调整为适合的值
      cpus: '2.0'
```

### 数据库性能调优
```bash
# 启用数据库性能统计
sudo -u saascontrol docker exec postgres-primary psql -U saasuser -c "CREATE EXTENSION IF NOT EXISTS pg_stat_statements;"

# 查看慢查询
sudo -u saascontrol docker exec postgres-primary psql -U saasuser -c "SELECT query, calls, total_time, mean_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

## 🔧 故障排除

### 常见问题及解决方案

#### 1. 服务启动失败
```bash
# 检查容器状态
docker ps -a

# 查看具体错误日志
docker logs container_name

# 检查资源使用
docker stats --no-stream
```

#### 2. 数据库连接失败
```bash
# 检查数据库服务状态
docker exec postgres-primary pg_isready -U saasuser

# 检查数据库连接
docker exec postgres-primary psql -U saasuser -c "SELECT version();"
```

#### 3. SSL证书问题
```bash
# 检查证书有效期
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/cert.pem -text -noout | grep "Not After"

# 测试SSL配置
curl -I https://yourdomain.com
```

#### 4. 内存使用过高
```bash
# 查看内存使用情况
free -h
docker stats --no-stream

# 清理未使用的Docker对象
docker system prune -f
```

### 日志文件位置
- **应用日志**: `/var/log/saascontroldeck/`
- **Nginx日志**: `/var/log/nginx/`
- **SSL续期日志**: `/var/log/ssl-renewal.log`
- **部署日志**: `/var/log/saascontroldeck/deploy-*.log`

## 📈 扩展部署

### 水平扩展
```bash
# 增加API Gateway实例
docker-compose -f /opt/saascontroldeck/docker/cloud-deployment/docker-compose.cloud.yml up -d --scale api-gateway-pro1=2

# 配置负载均衡
# 编辑 nginx/nginx-cloud.conf 添加更多upstream服务器
```

### 多服务器部署
```bash
# 分离数据库到独立服务器
# 1. 修改环境变量中的数据库连接
DATABASE_URL=postgresql+asyncpg://saasuser:password@db-server:5432/saascontroldeck_production

# 2. 更新Docker Compose配置移除本地数据库服务
# 3. 重新部署应用服务
```

## 🆘 紧急恢复

### 快速恢复流程
```bash
# 1. 停止所有服务
sudo -u saascontrol docker-compose -f /opt/saascontroldeck/docker/cloud-deployment/docker-compose.cloud.yml down

# 2. 恢复最近备份
sudo cp /opt/saascontroldeck/backups/latest/.env /opt/saascontroldeck/.env

# 3. 重启基础设施服务
sudo -u saascontrol docker-compose -f /opt/saascontroldeck/docker/cloud-deployment/docker-compose.cloud.yml up -d postgres-primary redis-cache minio-storage

# 4. 恢复数据库
sudo -u saascontrol docker exec -i postgres-primary psql -U saasuser < /opt/saascontroldeck/backups/latest/database_backup.sql

# 5. 启动应用服务
sudo -u saascontrol docker-compose -f /opt/saascontroldeck/docker/cloud-deployment/docker-compose.cloud.yml up -d
```

## 📞 技术支持

### 获取帮助
- **部署脚本帮助**: `./scripts/deploy/cloud-deploy-pipeline.sh --help`
- **SSL配置帮助**: `./scripts/ssl/setup-ssl-certificates.sh --help`
- **环境初始化帮助**: `./scripts/deploy/cloud-server-setup.sh --help`

### 系统信息收集
```bash
# 生成系统诊断报告
cat > system-diagnostic.sh << 'EOF'
#!/bin/bash
echo "=== 系统信息 ==="
uname -a
cat /etc/os-release

echo -e "\n=== 资源使用 ==="
free -h
df -h
docker system df

echo -e "\n=== 服务状态 ==="
systemctl status nginx docker
docker-compose -f /opt/saascontroldeck/docker/cloud-deployment/docker-compose.cloud.yml ps

echo -e "\n=== 网络连接 ==="
netstat -tuln | grep -E ':(80|443|9000|8000|8100|5432|6379|9090)'
EOF

chmod +x system-diagnostic.sh && ./system-diagnostic.sh
```

---

## 🎉 部署完成

恭喜！您已成功将 SaaS Control Deck 全栈AI平台部署到云服务器。您的平台现在具备：

✅ **高可用架构** - 微服务架构确保服务可靠性  
✅ **自动扩展能力** - 支持水平和垂直扩展  
✅ **完整监控体系** - Prometheus + Grafana + ELK Stack  
✅ **SSL安全防护** - Let's Encrypt自动证书管理  
✅ **自动备份恢复** - 数据安全有保障  
✅ **负载均衡** - Nginx高性能反向代理  

### 下一步建议
1. 配置监控告警通知
2. 设置定期数据备份
3. 优化性能参数
4. 配置CDN加速
5. 实施安全加固措施

访问您的应用：**https://yourdomain.com** 🚀