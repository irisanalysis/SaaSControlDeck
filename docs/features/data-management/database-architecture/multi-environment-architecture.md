# 多环境数据库架构设计

## 📋 架构概览

基于SaaS Control Deck平台的商业化扩展需求，设计了支持数据管理功能的完整三环境数据库架构。该架构支持从开发到生产的完整部署流程，并为不同用户层级（免费版、专业版、企业版）提供弹性的数据处理能力。

### 🏗️ 环境分层设计

```
生产环境 (Production) - 企业级高可用
├── saascontrol_prod_pro1     # 核心业务数据库
│   ├── 用户管理 & 权限控制
│   ├── 数据源管理 & 质量评估
│   ├── 商业化功能 & 订阅管理
│   └── 多租户数据隔离
└── saascontrol_prod_pro2     # AI分析 & 扩展服务
    ├── AI分析结果 & 对话历史
    ├── 长期归档数据 & 报告缓存
    ├── 实时数据流处理
    └── 性能监控 & 审计日志

测试环境 (Staging) - 生产镜像环境
├── saascontrol_stage_pro1    # 业务逻辑测试
└── saascontrol_stage_pro2    # AI服务测试

开发环境 (Development) - 灵活开发环境
├── saascontrol_dev_pro1      # 核心功能开发
└── saascontrol_dev_pro2      # AI功能开发
```

## 🔐 权限分层与安全策略

### 环境访问权限矩阵

| 权限类型 | 开发环境 | 测试环境 | 生产环境 |
|---------|---------|---------|---------|
| **数据库管理** | 完全权限 | 受限权限 | 严格控制 |
| **Schema修改** | ✅ 允许 | ⚠️ 审批制 | ❌ 禁止 |
| **数据操作** | 完全CRUD | 完全CRUD | 业务CRUD |
| **外部连接** | 开放网络 | 限制IP | VPN专网 |
| **备份恢复** | 手动操作 | 自动+手动 | 自动+审计 |
| **监控审计** | 基础监控 | 完整监控 | 企业监控 |

### 用户权限配置

```sql
-- 开发环境用户 (完全开发权限)
CREATE USER saascontrol_dev_user WITH
    CREATEDB
    PASSWORD 'dev_pass_2024_secure';

GRANT ALL PRIVILEGES ON DATABASE saascontrol_dev_pro1 TO saascontrol_dev_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_dev_pro2 TO saascontrol_dev_user;

-- 测试环境用户 (受限权限)
CREATE USER saascontrol_stage_user WITH
    PASSWORD 'stage_pass_2024_secure';

GRANT CONNECT, CREATE ON DATABASE saascontrol_stage_pro1 TO saascontrol_stage_user;
GRANT CONNECT, CREATE ON DATABASE saascontrol_stage_pro2 TO saascontrol_stage_user;

-- 生产环境用户 (业务权限)
CREATE USER saascontrol_prod_user WITH
    PASSWORD 'prod_pass_2024_secure';

GRANT CONNECT ON DATABASE saascontrol_prod_pro1 TO saascontrol_prod_user;
GRANT CONNECT ON DATABASE saascontrol_prod_pro2 TO saascontrol_prod_user;
```

## 📊 数据分布策略

### 主数据库 (Pro1) - 核心业务数据

**主要功能模块:**
- 用户管理与认证
- 数据源管理与配置
- 质量评估与评分
- 商业化订阅管理
- 多租户权限控制
- 实时业务操作

**数据特征:**
- 高频读写操作
- 强一致性要求
- 实时响应需求
- 严格权限控制

### 扩展数据库 (Pro2) - AI分析与扩展

**主要功能模块:**
- AI分析结果存储
- 对话历史管理
- 长期数据归档
- 分析报告缓存
- 实时数据流处理
- 性能监控数据

**数据特征:**
- 大数据量存储
- 分析型查询为主
- 可接受最终一致性
- 读多写少场景

## 🔄 环境间数据同步策略

### 开发环境 → 测试环境

```sql
-- 数据同步脚本 (schema + 示例数据)
#!/bin/bash

# 1. 导出开发环境Schema
pg_dump -h 47.79.87.199 -U saascontrol_dev_user \
        -d saascontrol_dev_pro1 \
        --schema-only \
        --no-owner --no-privileges \
        -f dev_to_stage_schema_pro1.sql

# 2. 导入到测试环境
psql -h 47.79.87.199 -U saascontrol_stage_user \
     -d saascontrol_stage_pro1 \
     -f dev_to_stage_schema_pro1.sql

# 3. 同步基础数据 (用户、配置等)
pg_dump -h 47.79.87.199 -U saascontrol_dev_user \
        -d saascontrol_dev_pro1 \
        --data-only \
        --table=users --table=user_subscriptions \
        --table=ai_models --table=quality_thresholds \
        -f dev_to_stage_data.sql
```

### 测试环境 → 生产环境

```sql
-- 生产部署脚本 (仅Schema，数据独立)
#!/bin/bash

# 1. 验证测试环境完整性
psql -h 47.79.87.199 -U saascontrol_stage_user \
     -d saascontrol_stage_pro1 \
     -c "SELECT COUNT(*) FROM information_schema.tables;"

# 2. 生成生产环境脚本
pg_dump -h 47.79.87.199 -U saascontrol_stage_user \
        -d saascontrol_stage_pro1 \
        --schema-only --clean --if-exists \
        --no-owner --no-privileges \
        -f stage_to_prod_schema.sql

# 3. 在生产环境执行 (需要DBA审批)
# psql -h 47.79.87.199 -U saascontrol_prod_user \
#      -d saascontrol_prod_pro1 \
#      -f stage_to_prod_schema.sql
```

## 🚀 商业化多租户架构

### 租户隔离策略

```sql
-- 组织/租户管理表
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    subscription_tier VARCHAR(20) DEFAULT 'free', -- 'free', 'professional', 'enterprise'
    max_users INTEGER DEFAULT 5,
    max_data_sources INTEGER DEFAULT 10,
    max_storage_mb BIGINT DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 用户-组织关联表
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member', -- 'owner', 'admin', 'member', 'viewer'
    permissions JSONB DEFAULT '{}',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);

-- 订阅管理表
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    plan_name VARCHAR(100) NOT NULL,
    plan_tier VARCHAR(20) NOT NULL, -- 'free', 'professional', 'enterprise'
    billing_cycle VARCHAR(20) DEFAULT 'monthly', -- 'monthly', 'annual'
    price_cents INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'CNY',
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'suspended', 'cancelled'
    starts_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ends_at TIMESTAMP WITH TIME ZONE,
    auto_renew BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 资源配额管理

```sql
-- 使用配额表
CREATE TABLE usage_quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL, -- 'data_sources', 'storage_mb', 'api_calls', 'ai_analysis'
    quota_limit BIGINT NOT NULL,
    quota_used BIGINT DEFAULT 0,
    reset_period VARCHAR(20) DEFAULT 'monthly', -- 'daily', 'monthly', 'annual', 'never'
    last_reset TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, resource_type)
);

-- 使用记录表
CREATE TABLE usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL,
    resource_amount BIGINT NOT NULL,
    operation_type VARCHAR(50) NOT NULL, -- 'create_data_source', 'run_analysis', 'api_call'
    resource_metadata JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_usage_quotas_org_type ON usage_quotas(organization_id, resource_type);
CREATE INDEX idx_usage_records_org_time ON usage_records(organization_id, recorded_at DESC);
CREATE INDEX idx_usage_records_type_time ON usage_records(resource_type, recorded_at DESC);
```

## 🎯 环境特定配置

### 开发环境配置

```yaml
development:
  database:
    primary:
      host: "47.79.87.199"
      port: 5432
      database: "saascontrol_dev_pro1"
      username: "saascontrol_dev_user"
      password: "dev_pass_2024_secure"
      pool_size: 5
      max_overflow: 10
    secondary:
      host: "47.79.87.199"
      port: 5432
      database: "saascontrol_dev_pro2"
      username: "saascontrol_dev_user"
      password: "dev_pass_2024_secure"
      pool_size: 3
      max_overflow: 5
  features:
    enable_debug_logging: true
    enable_sql_echo: true
    skip_auth_checks: false
    unlimited_quotas: true
```

### 测试环境配置

```yaml
staging:
  database:
    primary:
      host: "47.79.87.199"
      port: 5432
      database: "saascontrol_stage_pro1"
      username: "saascontrol_stage_user"
      password: "stage_pass_2024_secure"
      pool_size: 10
      max_overflow: 15
    secondary:
      host: "47.79.87.199"
      port: 5432
      database: "saascontrol_stage_pro2"
      username: "saascontrol_stage_user"
      password: "stage_pass_2024_secure"
      pool_size: 5
      max_overflow: 10
  features:
    enable_debug_logging: false
    enable_sql_echo: false
    skip_auth_checks: false
    realistic_quotas: true
```

### 生产环境配置

```yaml
production:
  database:
    primary:
      host: "47.79.87.199"
      port: 5432
      database: "saascontrol_prod_pro1"
      username: "saascontrol_prod_user"
      password: "prod_pass_2024_secure"
      pool_size: 20
      max_overflow: 30
    secondary:
      host: "47.79.87.199"
      port: 5432
      database: "saascontrol_prod_pro2"
      username: "saascontrol_prod_user"
      password: "prod_pass_2024_secure"
      pool_size: 15
      max_overflow: 20
  features:
    enable_debug_logging: false
    enable_sql_echo: false
    skip_auth_checks: false
    enforce_quotas: true
    enable_audit_logging: true
```

## 🔄 数据迁移与版本管理

### 迁移脚本管理

```sql
-- 数据库版本表
CREATE TABLE schema_migrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(50) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    migration_type VARCHAR(20) NOT NULL, -- 'schema', 'data', 'index', 'security'
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    applied_by VARCHAR(100) NOT NULL,
    execution_time_ms INTEGER,
    checksum VARCHAR(64) NOT NULL
);

-- 迁移执行示例
INSERT INTO schema_migrations (version, description, migration_type, applied_by, checksum)
VALUES ('001_initial_schema', 'Create initial database schema', 'schema', 'system', 'abc123...');
```

### 环境一致性检查

```sql
-- 环境一致性验证函数
CREATE OR REPLACE FUNCTION verify_environment_consistency(
    source_env TEXT,
    target_env TEXT
) RETURNS TABLE (
    table_name TEXT,
    column_differences TEXT,
    index_differences TEXT,
    constraint_differences TEXT
) AS $$
BEGIN
    -- 比较表结构
    -- 比较索引配置
    -- 比较约束条件
    -- 返回差异报告
END;
$$ LANGUAGE plpgsql;
```

## 📈 监控与告警策略

### 环境级监控指标

```sql
-- 环境监控表
CREATE TABLE environment_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    environment VARCHAR(20) NOT NULL, -- 'development', 'staging', 'production'
    database_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- 'connection_count', 'query_performance', 'storage_usage'
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(20) NOT NULL,
    alert_threshold DECIMAL(15,6),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 告警配置表
CREATE TABLE environment_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    environment VARCHAR(20) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    alert_threshold DECIMAL(15,6) NOT NULL,
    alert_message TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

这个多环境架构设计确保了数据管理功能能够支持从开发到生产的完整生命周期，并为商业化扩展提供了坚实的基础架构。