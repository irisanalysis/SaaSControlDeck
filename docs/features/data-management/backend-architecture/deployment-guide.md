# 数据管理功能 - 部署配置指南

## 🚀 部署架构概览

基于现有的Docker + Docker Compose + Kubernetes混合部署架构，为数据管理功能提供完整的部署解决方案，支持开发、测试和生产环境的自动化部署。

## 🏗️ 部署环境配置

### 环境分层策略

```yaml
# 环境配置层次
environments:
  development:
    purpose: "本地开发和功能测试"
    infrastructure: "Docker Compose"
    database: "saascontrol_dev_pro1/pro2"
    resources: "minimal"
    monitoring: "basic"

  staging:
    purpose: "集成测试和用户验收测试"
    infrastructure: "Kubernetes (Minikube)"
    database: "saascontrol_stage_pro1/pro2"
    resources: "medium"
    monitoring: "enhanced"

  production:
    purpose: "生产环境"
    infrastructure: "Kubernetes Cluster"
    database: "saascontrol_prod_pro1/pro2"
    resources: "high_availability"
    monitoring: "full_observability"
```

### 服务端口分配

```yaml
# 端口分配策略 (与现有架构保持一致)
port_allocation:
  backend_pro1: "8000-8099"
    api_gateway: 8000
    data_service: 8001
    ai_service: 8002
    quality_service: 8003      # 新增
    ai_chat_service: 8004      # 新增
    file_processing_service: 8005  # 新增

  backend_pro2: "8100-8199"
    api_gateway: 8100
    data_service: 8101
    ai_service: 8102
    quality_service: 8103      # 新增
    ai_chat_service: 8104      # 新增
    file_processing_service: 8105  # 新增

  infrastructure:
    postgresql: 5432
    redis: 6379/6380
    prometheus: 9090/9091
    grafana: 3000
    nginx: 80/443
```

## 🐳 Docker容器化配置

### 新增服务Dockerfile

#### 质量分析服务 Dockerfile
```dockerfile
# backend/backend-pro1/quality-service/Dockerfile
FROM python:3.11-slim

LABEL maintainer="SaaSControl Team"
LABEL service="quality-analysis-service"
LABEL version="1.0.0"

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 创建应用目录
WORKDIR /app

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/
COPY shared/ ./shared/

# 设置权限
RUN chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

#### AI对话服务 Dockerfile
```dockerfile
# backend/backend-pro1/ai-chat-service/Dockerfile
FROM python:3.11-slim

LABEL maintainer="SaaSControl Team"
LABEL service="ai-chat-service"
LABEL version="1.0.0"

# 系统依赖和优化
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip

WORKDIR /app

# 用户管理
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 依赖安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码
COPY app/ ./app/
COPY shared/ ./shared/

# 权限设置
RUN chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8004/health || exit 1

# 环境变量
ENV PYTHONPATH=/app
ENV OPENAI_API_TIMEOUT=30

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
```

### Docker Compose扩展配置

```yaml
# backend/backend-pro1/docker-compose.data-management.yml
version: '3.8'

services:
  # 质量分析服务
  quality-service:
    build:
      context: ./quality-service
      dockerfile: Dockerfile
    container_name: saascontrol-quality-service-pro1
    ports:
      - "8003:8003"
    environment:
      - SERVICE_NAME=quality-service
      - SERVICE_PORT=8003
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - PYTHONPATH=/app
    volumes:
      - ./shared:/app/shared:ro
      - quality_temp_data:/app/temp_data
    depends_on:
      - postgres
      - redis
    networks:
      - saascontrol-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

  # AI对话服务
  ai-chat-service:
    build:
      context: ./ai-chat-service
      dockerfile: Dockerfile
    container_name: saascontrol-ai-chat-service-pro1
    ports:
      - "8004:8004"
    environment:
      - SERVICE_NAME=ai-chat-service
      - SERVICE_PORT=8004
      - DATABASE_URL=${SECONDARY_DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_API_TIMEOUT=30
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./shared:/app/shared:ro
      - ai_chat_cache:/app/cache
    depends_on:
      - postgres
      - redis
    networks:
      - saascontrol-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M

  # 文件处理服务
  file-processing-service:
    build:
      context: ./file-processing-service
      dockerfile: Dockerfile
    container_name: saascontrol-file-processing-service-pro1
    ports:
      - "8005:8005"
    environment:
      - SERVICE_NAME=file-processing-service
      - SERVICE_PORT=8005
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - MINIO_URL=${MINIO_URL}
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
      - MAX_FILE_SIZE=104857600  # 100MB
      - CHUNK_SIZE=8388608       # 8MB
    volumes:
      - ./shared:/app/shared:ro
      - file_temp_storage:/app/temp_files
      - file_upload_storage:/app/uploads
    depends_on:
      - postgres
      - redis
      - minio
    networks:
      - saascontrol-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8005/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 1.5G
        reservations:
          cpus: '0.5'
          memory: 512M

  # Celery Worker - 数据分析队列
  celery-quality-worker:
    build:
      context: ./quality-service
      dockerfile: Dockerfile
    container_name: saascontrol-celery-quality-worker-pro1
    command: ["celery", "-A", "app.celery_app", "worker", "-Q", "quality_analysis", "--concurrency=4", "--loglevel=info"]
    environment:
      - CELERY_BROKER_URL=${REDIS_URL}
      - CELERY_RESULT_BACKEND=${REDIS_URL}
      - DATABASE_URL=${DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./shared:/app/shared:ro
      - quality_temp_data:/app/temp_data
    depends_on:
      - redis
      - postgres
    networks:
      - saascontrol-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  # Celery Worker - AI对话队列
  celery-ai-chat-worker:
    build:
      context: ./ai-chat-service
      dockerfile: Dockerfile
    container_name: saascontrol-celery-ai-chat-worker-pro1
    command: ["celery", "-A", "app.celery_app", "worker", "-Q", "ai_chat", "--concurrency=2", "--loglevel=info"]
    environment:
      - CELERY_BROKER_URL=${REDIS_URL}
      - CELERY_RESULT_BACKEND=${REDIS_URL}
      - DATABASE_URL=${SECONDARY_DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_API_TIMEOUT=30
    volumes:
      - ./shared:/app/shared:ro
      - ai_chat_cache:/app/cache
    depends_on:
      - redis
      - postgres
    networks:
      - saascontrol-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

volumes:
  quality_temp_data:
    driver: local
  ai_chat_cache:
    driver: local
  file_temp_storage:
    driver: local
  file_upload_storage:
    driver: local

networks:
  saascontrol-network:
    external: true
```

### 环境变量配置

```bash
# backend/backend-pro1/.env.data-management
# 数据管理功能专用环境变量

# === 质量分析服务配置 ===
QUALITY_SERVICE_PORT=8003
QUALITY_ANALYSIS_TIMEOUT=30
QUALITY_CACHE_TTL=1800
ENABLE_PARALLEL_ANALYSIS=true
MAX_ANALYSIS_WORKERS=4

# === AI对话服务配置 ===
AI_CHAT_SERVICE_PORT=8004
OPENAI_API_KEY=${OPENAI_API_KEY}
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_API_TIMEOUT=30
CHAT_SESSION_TIMEOUT=3600
MAX_CHAT_HISTORY=100

# === 文件处理服务配置 ===
FILE_PROCESSING_SERVICE_PORT=8005
MAX_FILE_SIZE=104857600    # 100MB
CHUNK_SIZE=8388608         # 8MB
ALLOWED_FILE_TYPES=csv,xlsx,json,parquet
TEMP_FILE_CLEANUP_HOURS=24

# === Celery配置 ===
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=["json"]

# === 安全配置 ===
JWT_SECRET_KEY=${JWT_SECRET_KEY}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
RATE_LIMIT_STORAGE_URL=${REDIS_URL}

# === 监控配置 ===
ENABLE_PROMETHEUS_METRICS=true
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_metrics
LOG_LEVEL=INFO
STRUCTURED_LOGGING=true

# === 数据库连接配置 ===
# 主数据库 (用户、数据源、质量评估)
DATABASE_URL=postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1

# 扩展数据库 (AI分析、对话历史)
SECONDARY_DATABASE_URL=postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro2

# === Redis配置 ===
REDIS_URL=redis://:redis123@localhost:6379/0
REDIS_CACHE_DB=1
REDIS_SESSION_DB=2
REDIS_RATE_LIMIT_DB=3

# === MinIO配置 ===
MINIO_URL=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_DATA_SOURCES=data-sources
MINIO_BUCKET_TEMP_FILES=temp-files
```

## ☸️ Kubernetes部署配置

### 命名空间和标签策略

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: saascontrol-data-management
  labels:
    name: saascontrol-data-management
    environment: production
    component: data-platform
---
# 资源配额
apiVersion: v1
kind: ResourceQuota
metadata:
  name: data-management-quota
  namespace: saascontrol-data-management
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "50"
    services: "10"
    persistentvolumeclaims: "20"
```

### 配置管理

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: data-management-config
  namespace: saascontrol-data-management
data:
  # 服务配置
  quality-service-config.yaml: |
    service:
      name: quality-service
      port: 8003
      max_workers: 4
      analysis_timeout: 30
    cache:
      ttl: 1800
      enabled: true
    security:
      rate_limit: 100
      max_file_size: 104857600

  ai-chat-service-config.yaml: |
    service:
      name: ai-chat-service
      port: 8004
      session_timeout: 3600
    openai:
      model: gpt-3.5-turbo
      timeout: 30
      max_tokens: 4000
    cache:
      ttl: 3600
      max_history: 100

  file-processing-config.yaml: |
    service:
      name: file-processing-service
      port: 8005
      chunk_size: 8388608
    allowed_types:
      - csv
      - xlsx
      - json
      - parquet
    cleanup:
      temp_files_hours: 24
      upload_files_days: 7

---
# 密钥管理
apiVersion: v1
kind: Secret
metadata:
  name: data-management-secrets
  namespace: saascontrol-data-management
type: Opaque
stringData:
  DATABASE_URL: "postgresql+asyncpg://saascontrol_prod_user:prod_pass_secure_2024@47.79.87.199:5432/saascontrol_prod_pro1"
  SECONDARY_DATABASE_URL: "postgresql+asyncpg://saascontrol_prod_user:prod_pass_secure_2024@47.79.87.199:5432/saascontrol_prod_pro2"
  REDIS_URL: "redis://:redis_prod_pass_2024@redis-service:6379/0"
  OPENAI_API_KEY: "your-openai-api-key-here"
  JWT_SECRET_KEY: "your-jwt-secret-key-here"
  ENCRYPTION_KEY: "your-encryption-key-here"
```

### 服务部署配置

```yaml
# k8s/quality-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quality-service
  namespace: saascontrol-data-management
  labels:
    app: quality-service
    component: data-analysis
    version: v1.0.0
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
  selector:
    matchLabels:
      app: quality-service
  template:
    metadata:
      labels:
        app: quality-service
        component: data-analysis
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/path: "/metrics"
        prometheus.io/port: "8003"
    spec:
      containers:
      - name: quality-service
        image: saascontrol/quality-service:1.0.0
        ports:
        - containerPort: 8003
          protocol: TCP
        env:
        - name: SERVICE_PORT
          value: "8003"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: data-management-secrets
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: data-management-secrets
              key: REDIS_URL
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: data-management-secrets
              key: OPENAI_API_KEY
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8003
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8003
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
          readOnly: true
        - name: temp-storage
          mountPath: /app/temp_data
      volumes:
      - name: config-volume
        configMap:
          name: data-management-config
      - name: temp-storage
        emptyDir:
          sizeLimit: 2Gi
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - quality-service
              topologyKey: kubernetes.io/hostname

---
# Service配置
apiVersion: v1
kind: Service
metadata:
  name: quality-service
  namespace: saascontrol-data-management
  labels:
    app: quality-service
    component: data-analysis
spec:
  selector:
    app: quality-service
  ports:
  - name: http
    port: 8003
    targetPort: 8003
    protocol: TCP
  type: ClusterIP

---
# HPA自动扩缩容
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: quality-service-hpa
  namespace: saascontrol-data-management
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: quality-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 300
      policies:
      - type: Pods
        value: 2
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Pods
        value: 1
        periodSeconds: 60
```

### Ingress网关配置

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: data-management-ingress
  namespace: saascontrol-data-management
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$1
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.saascontrol.io
    secretName: saascontrol-tls
  rules:
  - host: api.saascontrol.io
    http:
      paths:
      # 质量分析服务路由
      - path: /api/v1/quality-analysis/(.*)
        pathType: Prefix
        backend:
          service:
            name: quality-service
            port:
              number: 8003
      # AI对话服务路由
      - path: /api/v1/ai-chat/(.*)
        pathType: Prefix
        backend:
          service:
            name: ai-chat-service
            port:
              number: 8004
      # 文件处理服务路由
      - path: /api/v1/data-management/(.*)
        pathType: Prefix
        backend:
          service:
            name: file-processing-service
            port:
              number: 8005
```

## 📊 监控和日志配置

### Prometheus监控配置

```yaml
# k8s/monitoring/prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: saascontrol-data-management
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    rule_files:
      - "/etc/prometheus/rules/*.yml"

    scrape_configs:
    # 质量分析服务监控
    - job_name: 'quality-service'
      static_configs:
        - targets: ['quality-service:8003']
      metrics_path: '/metrics'
      scrape_interval: 15s
      scrape_timeout: 10s

    # AI对话服务监控
    - job_name: 'ai-chat-service'
      static_configs:
        - targets: ['ai-chat-service:8004']
      metrics_path: '/metrics'
      scrape_interval: 15s

    # 文件处理服务监控
    - job_name: 'file-processing-service'
      static_configs:
        - targets: ['file-processing-service:8005']
      metrics_path: '/metrics'
      scrape_interval: 15s

    # Kubernetes集群监控
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - saascontrol-data-management
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true

  # 告警规则
  alert_rules.yml: |
    groups:
    - name: data_management_alerts
      rules:
      # 高错误率告警
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} for {{ $labels.service }}"

      # 响应时间告警
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      # 内存使用率告警
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      # 队列积压告警
      - alert: QueueBacklog
        expr: celery_queue_length > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Queue backlog detected"
          description: "Queue {{ $labels.queue }} has {{ $value }} pending tasks"
```

### 日志聚合配置

```yaml
# k8s/logging/fluentd-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: saascontrol-data-management
data:
  fluent.conf: |
    # 输入配置 - 收集Kubernetes日志
    <source>
      @type tail
      path /var/log/containers/*data-management*.log
      pos_file /var/log/fluentd-containers.log.pos
      tag kubernetes.*
      format json
      time_format %Y-%m-%dT%H:%M:%S.%NZ
    </source>

    # 过滤配置 - 解析和丰富日志
    <filter kubernetes.**>
      @type kubernetes_metadata
      merge_json_log true
      preserve_json_log true
    </filter>

    # 过滤敏感信息
    <filter kubernetes.**>
      @type record_transformer
      enable_ruby
      <record>
        # 移除敏感字段
        message ${record["message"].gsub(/password[^\\s]*\\s*[=:]\\s*[^\\s]+/i, "password=***")}
        message ${record["message"].gsub(/api[_-]?key[^\\s]*\\s*[=:]\\s*[^\\s]+/i, "api_key=***")}
      </record>
    </filter>

    # 输出配置 - 发送到Elasticsearch
    <match kubernetes.**>
      @type elasticsearch
      host elasticsearch-service
      port 9200
      index_name saascontrol-data-management
      type_name _doc
      include_tag_key true
      tag_key @log_name
      <buffer>
        @type file
        path /var/log/fluentd-buffers/kubernetes.system.buffer
        flush_mode interval
        retry_type exponential_backoff
        flush_thread_count 2
        flush_interval 5s
        retry_forever
        retry_max_interval 30
        chunk_limit_size 2M
        total_limit_size 500M
        overflow_action block
      </buffer>
    </match>
```

## 🔄 CI/CD集成

### GitHub Actions工作流

```yaml
# .github/workflows/data-management-deploy.yml
name: Deploy Data Management Services

on:
  push:
    branches: [main]
    paths:
      - 'backend/backend-pro1/quality-service/**'
      - 'backend/backend-pro1/ai-chat-service/**'
      - 'backend/backend-pro1/file-processing-service/**'
      - 'k8s/data-management/**'

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: saascontrol

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [quality-service, ai-chat-service, file-processing-service]

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd backend/backend-pro1/${{ matrix.service }}
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio

    - name: Run tests
      run: |
        cd backend/backend-pro1/${{ matrix.service }}
        pytest tests/ -v --cov=app --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: backend/backend-pro1/${{ matrix.service }}/coverage.xml
        flags: ${{ matrix.service }}

  build-images:
    needs: build-and-test
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [quality-service, ai-chat-service, file-processing-service]

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/${{ matrix.service }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}

    - name: Build and push image
      uses: docker/build-push-action@v5
      with:
        context: backend/backend-pro1/${{ matrix.service }}
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  security-scan:
    needs: build-images
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [quality-service, ai-chat-service, file-processing-service]

    steps:
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/${{ matrix.service }}:latest
        format: 'sarif'
        output: 'trivy-results-${{ matrix.service }}.sarif'

    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results-${{ matrix.service }}.sarif'

  deploy-staging:
    needs: [build-images, security-scan]
    runs-on: ubuntu-latest
    environment: staging

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Configure kubectl
      run: |
        mkdir -p $HOME/.kube
        echo "${{ secrets.KUBECONFIG_STAGING }}" | base64 -d > $HOME/.kube/config

    - name: Deploy to staging
      run: |
        # 更新镜像标签
        cd k8s/data-management
        sed -i "s|image: saascontrol/.*:.*|image: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/quality-service:${{ github.sha }}|g" quality-service-deployment.yaml
        sed -i "s|image: saascontrol/.*:.*|image: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/ai-chat-service:${{ github.sha }}|g" ai-chat-service-deployment.yaml
        sed -i "s|image: saascontrol/.*:.*|image: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/file-processing-service:${{ github.sha }}|g" file-processing-deployment.yaml

        # 应用配置
        kubectl apply -f namespace.yaml
        kubectl apply -f configmap.yaml
        kubectl apply -f secrets.yaml
        kubectl apply -f quality-service-deployment.yaml
        kubectl apply -f ai-chat-service-deployment.yaml
        kubectl apply -f file-processing-deployment.yaml
        kubectl apply -f ingress.yaml

    - name: Wait for deployment
      run: |
        kubectl rollout status deployment/quality-service -n saascontrol-data-management --timeout=300s
        kubectl rollout status deployment/ai-chat-service -n saascontrol-data-management --timeout=300s
        kubectl rollout status deployment/file-processing-service -n saascontrol-data-management --timeout=300s

    - name: Run integration tests
      run: |
        # 运行集成测试脚本
        cd tests/integration
        python test_data_management_integration.py --env staging

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main'

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Configure kubectl
      run: |
        mkdir -p $HOME/.kube
        echo "${{ secrets.KUBECONFIG_PRODUCTION }}" | base64 -d > $HOME/.kube/config

    - name: Deploy to production
      run: |
        cd k8s/data-management
        # 使用生产环境配置
        sed -i "s|namespace: saascontrol-data-management|namespace: saascontrol-prod|g" *.yaml
        sed -i "s|image: saascontrol/.*:.*|image: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/quality-service:${{ github.sha }}|g" quality-service-deployment.yaml

        # 蓝绿部署策略
        kubectl apply -f namespace.yaml
        kubectl apply -f configmap.yaml
        kubectl apply -f secrets.yaml

        # 逐个服务滚动更新
        kubectl set image deployment/quality-service quality-service=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/quality-service:${{ github.sha }} -n saascontrol-prod
        kubectl rollout status deployment/quality-service -n saascontrol-prod --timeout=600s

        kubectl set image deployment/ai-chat-service ai-chat-service=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/ai-chat-service:${{ github.sha }} -n saascontrol-prod
        kubectl rollout status deployment/ai-chat-service -n saascontrol-prod --timeout=600s

        kubectl set image deployment/file-processing-service file-processing-service=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/file-processing-service:${{ github.sha }} -n saascontrol-prod
        kubectl rollout status deployment/file-processing-service -n saascontrol-prod --timeout=600s

    - name: Health check
      run: |
        # 等待服务健康检查通过
        sleep 60
        kubectl get pods -n saascontrol-prod
        kubectl get services -n saascontrol-prod

        # 验证服务可访问性
        curl -f https://api.saascontrol.io/api/v1/quality-analysis/health
        curl -f https://api.saascontrol.io/api/v1/ai-chat/health
        curl -f https://api.saascontrol.io/api/v1/data-management/health

    - name: Notify deployment success
      if: success()
      run: |
        curl -X POST "${{ secrets.SLACK_WEBHOOK_URL }}" \
        -H 'Content-type: application/json' \
        --data '{"text":"✅ Data Management services deployed successfully to production"}'

    - name: Notify deployment failure
      if: failure()
      run: |
        curl -X POST "${{ secrets.SLACK_WEBHOOK_URL }}" \
        -H 'Content-type: application/json' \
        --data '{"text":"❌ Data Management services deployment failed"}'
```

## 🔧 部署脚本和自动化

### 一键部署脚本

```bash
#!/bin/bash
# scripts/deploy-data-management.sh

set -euo pipefail

# 配置变量
ENVIRONMENT=${1:-development}
PROJECT=${2:-pro1}
SERVICES=("quality-service" "ai-chat-service" "file-processing-service")

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查前置条件
check_prerequisites() {
    log_info "Checking prerequisites..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # 检查环境变量文件
    if [[ ! -f "backend/backend-${PROJECT}/.env" ]]; then
        log_error "Environment file not found: backend/backend-${PROJECT}/.env"
        exit 1
    fi

    log_info "Prerequisites check passed"
}

# 构建Docker镜像
build_images() {
    log_info "Building Docker images for environment: ${ENVIRONMENT}"

    cd "backend/backend-${PROJECT}"

    for service in "${SERVICES[@]}"; do
        log_info "Building ${service}..."

        if [[ -f "${service}/Dockerfile" ]]; then
            docker build -t "saascontrol/${service}:${ENVIRONMENT}" "${service}/"
            log_info "✅ ${service} image built successfully"
        else
            log_warn "Dockerfile not found for ${service}, skipping..."
        fi
    done

    cd - > /dev/null
}

# 启动服务
start_services() {
    log_info "Starting data management services..."

    cd "backend/backend-${PROJECT}"

    # 启动基础设施服务
    docker-compose up -d postgres redis minio

    # 等待基础设施服务启动
    log_info "Waiting for infrastructure services to be ready..."
    sleep 30

    # 启动数据管理服务
    docker-compose -f docker-compose.data-management.yml up -d

    log_info "Services started successfully"
    cd - > /dev/null
}

# 健康检查
health_check() {
    log_info "Performing health checks..."

    local base_port
    if [[ "${PROJECT}" == "pro1" ]]; then
        base_port=8000
    else
        base_port=8100
    fi

    local services_health=(
        "$((base_port + 3)):quality-service"
        "$((base_port + 4)):ai-chat-service"
        "$((base_port + 5)):file-processing-service"
    )

    for service_info in "${services_health[@]}"; do
        local port="${service_info%%:*}"
        local service="${service_info##*:}"

        log_info "Checking ${service} health on port ${port}..."

        # 等待服务启动
        local max_attempts=30
        local attempt=1

        while [[ ${attempt} -le ${max_attempts} ]]; do
            if curl -sf "http://localhost:${port}/health" > /dev/null 2>&1; then
                log_info "✅ ${service} is healthy"
                break
            fi

            if [[ ${attempt} -eq ${max_attempts} ]]; then
                log_error "❌ ${service} health check failed after ${max_attempts} attempts"
                return 1
            fi

            log_info "Attempt ${attempt}/${max_attempts}: ${service} not ready, waiting..."
            sleep 10
            ((attempt++))
        done
    done

    log_info "All services are healthy"
}

# 运行数据库迁移
run_migrations() {
    log_info "Running database migrations..."

    cd "backend/backend-${PROJECT}"

    # 主数据库迁移
    docker-compose exec quality-service python -m alembic upgrade head

    # 扩展数据库迁移
    docker-compose exec ai-chat-service python -m alembic upgrade head

    log_info "Database migrations completed"
    cd - > /dev/null
}

# 显示服务状态
show_status() {
    log_info "Service status:"

    cd "backend/backend-${PROJECT}"
    docker-compose -f docker-compose.data-management.yml ps
    cd - > /dev/null

    local base_port
    if [[ "${PROJECT}" == "pro1" ]]; then
        base_port=8000
    else
        base_port=8100
    fi

    echo ""
    log_info "Service endpoints:"
    echo "  Quality Analysis: http://localhost:$((base_port + 3))"
    echo "  AI Chat: http://localhost:$((base_port + 4))"
    echo "  File Processing: http://localhost:$((base_port + 5))"
    echo ""
    echo "  Health checks:"
    echo "  curl http://localhost:$((base_port + 3))/health"
    echo "  curl http://localhost:$((base_port + 4))/health"
    echo "  curl http://localhost:$((base_port + 5))/health"
}

# 清理函数
cleanup() {
    if [[ "${ENVIRONMENT}" == "development" ]]; then
        log_warn "To stop services, run:"
        echo "  cd backend/backend-${PROJECT} && docker-compose -f docker-compose.data-management.yml down"
    fi
}

# 主函数
main() {
    log_info "Starting data management deployment for ${ENVIRONMENT} environment (${PROJECT})"

    check_prerequisites
    build_images
    start_services
    run_migrations
    health_check
    show_status
    cleanup

    log_info "🎉 Data management deployment completed successfully!"
}

# 错误处理
trap 'log_error "Deployment failed at line $LINENO"' ERR

# 执行主函数
main "$@"
```

这个部署配置指南为数据管理功能提供了完整的容器化和Kubernetes部署解决方案，确保服务在各种环境中的可靠运行和高可用性。