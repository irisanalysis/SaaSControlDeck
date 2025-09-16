# SaaS Control Deck 三环境数据库架构设计

## 架构概览

本文档详细描述了SaaS Control Deck项目的三环境数据库架构设计，包括开发、测试、生产环境的完整数据库规划。

### 环境划分

```
开发环境 (Development)
├── saascontrol_dev_pro1      # backend-pro1服务组 (端口8000-8002)
│   ├── API Gateway Service   # 8000
│   ├── Data Service         # 8001  
│   └── AI Service           # 8002
└── saascontrol_dev_pro2      # backend-pro2服务组 (端口8100-8102)
    ├── API Gateway Service   # 8100
    ├── Data Service         # 8101
    └── AI Service           # 8102

测试环境 (Staging)
├── saascontrol_stage_pro1    # backend-pro1测试环境
└── saascontrol_stage_pro2    # backend-pro2测试环境

生产环境 (Production)  
├── saascontrol_prod_pro1     # backend-pro1生产环境
└── saascontrol_prod_pro2     # backend-pro2生产环境
```

### 数据库服务器信息

- **主机**: 47.79.87.199
- **端口**: 5432
- **现有数据库**: iris
- **超级用户**: jackchan
- **密码**: secure_password_123

## 用户权限设计

### 环境专用用户

```sql
-- 开发环境用户 (开放权限，支持schema修改)
saasctl_dev_pro1_user       # 开发环境pro1用户
saasctl_dev_pro2_user       # 开发环境pro2用户

-- 测试环境用户 (受限权限，支持数据重置)
saasctl_stage_pro1_user     # 测试环境pro1用户
saasctl_stage_pro2_user     # 测试环境pro2用户

-- 生产环境用户 (严格权限，仅业务操作)
saasctl_prod_pro1_user      # 生产环境pro1用户
saasctl_prod_pro2_user      # 生产环境pro2用户
```

### 权限层级设计

**开发环境权限**:
- CREATE/DROP DATABASE
- CREATE/ALTER/DROP TABLE
- INSERT/UPDATE/DELETE/SELECT
- CREATE/DROP INDEX
- 允许外部网络连接

**测试环境权限**:
- CREATE/ALTER/DROP TABLE (受限)
- INSERT/UPDATE/DELETE/SELECT
- CREATE/DROP INDEX
- TRUNCATE TABLE
- 数据库备份/恢复

**生产环境权限**:
- INSERT/UPDATE/DELETE/SELECT
- CREATE INDEX (仅优化用)
- 严格的网络访问控制
- 完整的审计日志

## 核心表结构设计

### 1. 用户管理模块

```sql
-- 用户基本信息表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- 用户详细资料表
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    avatar_url TEXT,
    bio TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 用户会话表
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT true
);
```

### 2. 项目管理模块

```sql
-- 项目信息表
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'active',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 项目成员表
CREATE TABLE project_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',
    permissions JSONB DEFAULT '{}',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, user_id)
);

-- 项目设置表
CREATE TABLE project_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    setting_key VARCHAR(100) NOT NULL,
    setting_value JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, setting_key)
);
```

### 3. AI任务管理模块

```sql
-- AI任务表
CREATE TABLE ai_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    task_name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- AI模型表
CREATE TABLE ai_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    configuration JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, version)
);

-- AI结果表
CREATE TABLE ai_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES ai_tasks(id) ON DELETE CASCADE,
    model_id UUID REFERENCES ai_models(id),
    result_data JSONB,
    confidence_score DECIMAL(5,4),
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 4. 数据分析模块

```sql
-- 数据源表
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(100) NOT NULL,
    connection_config JSONB,
    schema_info JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 数据分析作业表
CREATE TABLE analysis_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_name VARCHAR(255) NOT NULL,
    job_type VARCHAR(100) NOT NULL,
    data_source_ids UUID[] DEFAULT '{}',
    analysis_config JSONB,
    status VARCHAR(50) DEFAULT 'queued',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 分析结果表
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    result_type VARCHAR(100) NOT NULL,
    result_data JSONB,
    visualization_config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 5. 文件存储模块

```sql
-- 文件存储表
CREATE TABLE file_storage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(255),
    storage_type VARCHAR(50) DEFAULT 'local',
    storage_config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 文件元数据表
CREATE TABLE file_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES file_storage(id) ON DELETE CASCADE,
    metadata_key VARCHAR(100) NOT NULL,
    metadata_value JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_id, metadata_key)
);
```

### 6. 系统监控模块

```sql
-- 系统日志表
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) NOT NULL,
    log_level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    user_id UUID REFERENCES users(id),
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 性能指标表  
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(20),
    tags JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 审计跟踪表
CREATE TABLE audit_trails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## 索引策略设计

### 主要索引

```sql
-- 用户相关索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

-- 项目相关索引
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_project_members_project_id ON project_members(project_id);
CREATE INDEX idx_project_members_user_id ON project_members(user_id);

-- AI任务相关索引
CREATE INDEX idx_ai_tasks_project_id ON ai_tasks(project_id);
CREATE INDEX idx_ai_tasks_user_id ON ai_tasks(user_id);
CREATE INDEX idx_ai_tasks_status ON ai_tasks(status);
CREATE INDEX idx_ai_tasks_created_at ON ai_tasks(created_at);

-- 分析作业相关索引
CREATE INDEX idx_analysis_jobs_project_id ON analysis_jobs(project_id);
CREATE INDEX idx_analysis_jobs_user_id ON analysis_jobs(user_id);
CREATE INDEX idx_analysis_jobs_status ON analysis_jobs(status);

-- 系统监控相关索引
CREATE INDEX idx_system_logs_service_name ON system_logs(service_name);
CREATE INDEX idx_system_logs_log_level ON system_logs(log_level);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);
CREATE INDEX idx_performance_metrics_service_name ON performance_metrics(service_name);
CREATE INDEX idx_performance_metrics_recorded_at ON performance_metrics(recorded_at);
```

### 复合索引

```sql
-- 复合查询优化索引
CREATE INDEX idx_ai_tasks_project_status ON ai_tasks(project_id, status);
CREATE INDEX idx_user_sessions_user_active ON user_sessions(user_id, is_active);
CREATE INDEX idx_system_logs_service_level_time ON system_logs(service_name, log_level, created_at);
```

## 性能优化策略

### 1. 连接池配置

```python
# 各环境连接池配置建议
DEVELOPMENT_POOL_CONFIG = {
    "pool_size": 5,
    "max_overflow": 10,
    "pool_timeout": 30,
    "pool_recycle": 3600
}

STAGING_POOL_CONFIG = {
    "pool_size": 10, 
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 3600
}

PRODUCTION_POOL_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600
}
```

### 2. 分区表规划

```sql
-- 大数据量表分区策略 (如系统日志表)
CREATE TABLE system_logs_partitioned (
    LIKE system_logs INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- 按月分区
CREATE TABLE system_logs_202501 PARTITION OF system_logs_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
```

### 3. 查询优化

```sql
-- 定期更新表统计信息
ANALYZE users;
ANALYZE ai_tasks;
ANALYZE system_logs;

-- 创建部分索引优化特定查询
CREATE INDEX idx_active_users ON users(id) WHERE is_active = true;
CREATE INDEX idx_pending_tasks ON ai_tasks(id) WHERE status = 'pending';
```

## 安全考虑

### 1. 网络访问控制

```sql
-- pg_hba.conf 配置建议
# 开发环境 - 允许Firebase Studio访问
host saascontrol_dev_pro1 saasctl_dev_pro1_user 0.0.0.0/0 md5
host saascontrol_dev_pro2 saasctl_dev_pro2_user 0.0.0.0/0 md5

# 测试环境 - 限制CI/CD服务器访问
host saascontrol_stage_pro1 saasctl_stage_pro1_user 172.16.0.0/16 md5
host saascontrol_stage_pro2 saasctl_stage_pro2_user 172.16.0.0/16 md5

# 生产环境 - 严格限制应用服务器访问
host saascontrol_prod_pro1 saasctl_prod_pro1_user 10.0.0.0/16 md5
host saascontrol_prod_pro2 saasctl_prod_pro2_user 10.0.0.0/16 md5
```

### 2. 数据加密

```sql
-- 敏感字段加密
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 密码hash示例
INSERT INTO users (email, username, password_hash) 
VALUES ('user@example.com', 'username', crypt('password', gen_salt('bf')));
```

### 3. 行级安全策略

```sql
-- 启用行级安全
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- 用户只能访问自己的项目
CREATE POLICY user_projects ON projects
    FOR ALL TO saasctl_app_role
    USING (owner_id = current_setting('app.current_user_id')::uuid);
```

## 备份和恢复策略

### 1. 自动备份配置

```bash
#!/bin/bash
# 每日备份脚本

# 开发环境备份 (保留7天)
pg_dump -h 47.79.87.199 -U jackchan saascontrol_dev_pro1 | gzip > /backup/dev/saascontrol_dev_pro1_$(date +%Y%m%d).sql.gz

# 生产环境备份 (保留30天)
pg_dump -h 47.79.87.199 -U jackchan saascontrol_prod_pro1 | gzip > /backup/prod/saascontrol_prod_pro1_$(date +%Y%m%d).sql.gz
```

### 2. 恢复流程

```bash
# 恢复数据库
gunzip -c backup_file.sql.gz | psql -h 47.79.87.199 -U jackchan -d saascontrol_dev_pro1
```

## 监控和维护

### 1. 健康检查

```sql
-- 数据库健康检查查询
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_tuples,
    n_dead_tup as dead_tuples
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
```

### 2. 性能监控

```sql
-- 慢查询监控
SELECT 
    query,
    mean_time,
    calls,
    total_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

---

## 部署检查清单

- [ ] 创建所有数据库
- [ ] 创建所有用户并分配权限
- [ ] 执行表结构创建脚本
- [ ] 创建所有索引
- [ ] 配置连接池参数
- [ ] 设置备份策略
- [ ] 配置监控和告警
- [ ] 执行安全配置
- [ ] 验证所有环境连接
- [ ] 性能测试和优化

这个架构设计确保了SaaS Control Deck项目在开发、测试和生产环境中的数据库完整性、安全性和性能。