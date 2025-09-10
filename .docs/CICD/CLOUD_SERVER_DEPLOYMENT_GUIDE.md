# 云服务器部署指南

## 📋 概述

本指南详细说明如何将SaaS Control Deck部署到云服务器（AWS、阿里云、腾讯云等）。

## 🔧 前置要求

### 服务器要求
- **操作系统**: Ubuntu 20.04+ 或 CentOS 8+
- **CPU**: 最少 4 核心（推荐 8 核心）
- **内存**: 最少 8GB（推荐 16GB）
- **存储**: 最少 100GB SSD
- **端口**: 开放 80, 443, 8000-8199, 3000-3099

### 软件要求
- Docker 20.10+
- Docker Compose 2.0+
- Git
- Nginx（反向代理）
- SSL证书（Let's Encrypt推荐）

## 🚀 部署步骤

### 1. 服务器初始化

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要工具
sudo apt install -y git curl wget vim

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 2. 克隆项目代码

```bash
# 创建应用目录
sudo mkdir -p /opt/saascontroldeck
cd /opt

# 克隆代码（使用您的私有仓库）
git clone https://github.com/irisanalysis/SaaSControlDeck.git saascontroldeck
cd saascontroldeck
```

### 3. 配置环境变量

```bash
# 复制环境配置模板
cd docker/environments
cp .env.production .env.production.local

# 编辑生产环境配置
vim .env.production.local
```

**必须配置的环境变量**:
```env
# 数据库配置
POSTGRES_PASSWORD=<强密码>
POSTGRES_DB=saascontroldb
POSTGRES_USER=saascontrol

# Redis配置
REDIS_PASSWORD=<强密码>

# MinIO配置
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=<强密码>

# API密钥
JWT_SECRET_KEY=<随机生成的密钥>
OPENAI_API_KEY=<您的OpenAI密钥>
GOOGLE_GENKIT_API_KEY=<您的Genkit密钥>

# 域名配置
DOMAIN_NAME=your-domain.com
API_URL=https://api.your-domain.com
FRONTEND_URL=https://your-domain.com
```

### 4. 启动Docker服务

```bash
# 进入Docker配置目录
cd /opt/saascontroldeck/docker/environments

# 拉取最新镜像
docker-compose -f docker-compose.production.yml pull

# 启动所有服务
docker-compose -f docker-compose.production.yml --env-file .env.production.local up -d

# 查看服务状态
docker-compose -f docker-compose.production.yml ps

# 查看日志
docker-compose -f docker-compose.production.yml logs -f
```

### 5. 配置Nginx反向代理

```bash
# 安装Nginx
sudo apt install -y nginx

# 创建站点配置
sudo vim /etc/nginx/sites-available/saascontroldeck
```

**Nginx配置示例**:
```nginx
# 前端服务
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# API网关
server {
    listen 80;
    server_name api.your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/saascontroldeck /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. 配置SSL证书

```bash
# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# 自动续期
sudo systemctl enable certbot.timer
```

## 📊 监控和维护

### 健康检查

```bash
# 检查所有服务状态
cd /opt/saascontroldeck/docker/environments
docker-compose -f docker-compose.production.yml ps

# API健康检查
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health

# 前端检查
curl http://localhost:3001
```

### 日志管理

```bash
# 查看特定服务日志
docker-compose -f docker-compose.production.yml logs api-gateway
docker-compose -f docker-compose.production.yml logs frontend-blue

# 实时日志
docker-compose -f docker-compose.production.yml logs -f --tail=100
```

### 备份策略

```bash
# 数据库备份
docker exec postgres-container pg_dump -U saascontrol saascontroldb > backup_$(date +%Y%m%d).sql

# MinIO数据备份
docker run --rm -v minio-data:/data -v $(pwd):/backup alpine tar czf /backup/minio_$(date +%Y%m%d).tar.gz /data
```

## 🔄 更新部署

```bash
# 拉取最新代码
cd /opt/saascontroldeck
git pull origin main

# 重新构建和部署
cd docker/environments
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d --remove-orphans

# 清理旧镜像
docker system prune -f
```

## 🚨 故障排除

### 常见问题

**1. 端口占用**
```bash
# 检查端口占用
sudo netstat -tulpn | grep :8000
# 停止占用服务或修改配置端口
```

**2. 内存不足**
```bash
# 检查内存使用
docker stats
# 调整Docker资源限制或升级服务器
```

**3. 网络连接问题**
```bash
# 检查Docker网络
docker network ls
docker network inspect saascontroldeck_default
```

### 紧急回滚

```bash
# 停止当前服务
docker-compose -f docker-compose.production.yml down

# 恢复到上一个版本
git checkout <previous-commit>
docker-compose -f docker-compose.production.yml up -d
```

## 🔐 安全建议

1. **防火墙配置**
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. **定期更新**
- 系统补丁
- Docker版本
- 依赖包更新

3. **监控告警**
- 设置Prometheus + Grafana
- 配置告警规则
- 日志聚合（ELK Stack）

## 📞 支持

- **文档**: `.docs/CICD/`
- **Docker配置**: `docker/README.md`
- **故障排除**: `.docs/CICD/vercel/VERCEL_DEPLOYMENT_TROUBLESHOOTING.md`

---

**最后更新**: 2024年12月
**适用版本**: v1.0.0+