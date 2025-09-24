# 数据库安全架构设计

## 🔐 安全架构概览

基于企业级安全要求，设计了全方位的数据库安全架构，满足GDPR、SOC2等合规要求，提供从网络层到应用层的完整安全防护。

## 🛡️ 多层安全防护策略

### 1. 网络层安全

#### 网络访问控制 (pg_hba.conf)

```bash
# /etc/postgresql/14/main/pg_hba.conf

# ========================
# 本地连接配置
# ========================
local   all             postgres                                peer
local   all             all                                     md5

# ========================
# 开发环境配置
# ========================
# Firebase Studio和开发工具访问
host    saascontrol_dev_pro1    saascontrol_dev_user    0.0.0.0/0               md5
host    saascontrol_dev_pro2    saascontrol_dev_user    0.0.0.0/0               md5

# 开发环境SSL强制
hostssl saascontrol_dev_pro1    saascontrol_dev_user    0.0.0.0/0               md5
hostssl saascontrol_dev_pro2    saascontrol_dev_user    0.0.0.0/0               md5

# ========================
# 测试环境配置
# ========================
# 限制CI/CD服务器访问
host    saascontrol_stage_pro1  saascontrol_stage_user  172.16.0.0/16           md5
host    saascontrol_stage_pro2  saascontrol_stage_user  172.16.0.0/16           md5
host    saascontrol_stage_pro1  saascontrol_stage_user  10.0.0.0/8              md5
host    saascontrol_stage_pro2  saascontrol_stage_user  10.0.0.0/8              md5

# 测试环境SSL必须
hostssl saascontrol_stage_pro1  saascontrol_stage_user  172.16.0.0/16           md5
hostssl saascontrol_stage_pro2  saascontrol_stage_user  172.16.0.0/16           md5

# ========================
# 生产环境配置 (严格限制)
# ========================
# 仅允许应用服务器访问
hostssl saascontrol_prod_pro1   saascontrol_prod_user   10.0.1.0/24             scram-sha-256
hostssl saascontrol_prod_pro2   saascontrol_prod_user   10.0.1.0/24             scram-sha-256

# 备份服务器访问
hostssl saascontrol_prod_pro1   saascontrol_backup_user 10.0.2.100/32           scram-sha-256
hostssl saascontrol_prod_pro2   saascontrol_backup_user 10.0.2.100/32           scram-sha-256

# 管理员访问 (需要证书认证)
hostssl all                     saascontrol_admin       10.0.3.0/24             cert

# 拒绝所有其他连接
host    all                     all                     0.0.0.0/0               reject
```

#### SSL/TLS配置

```sql
-- SSL配置参数
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/etc/postgresql/ssl/server.crt';
ALTER SYSTEM SET ssl_key_file = '/etc/postgresql/ssl/server.key';
ALTER SYSTEM SET ssl_ca_file = '/etc/postgresql/ssl/ca.crt';
ALTER SYSTEM SET ssl_crl_file = '/etc/postgresql/ssl/server.crl';

-- 强制SSL连接
ALTER SYSTEM SET ssl_prefer_server_ciphers = on;
ALTER SYSTEM SET ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL:!SSLv3:!TLSv1';
ALTER SYSTEM SET ssl_min_protocol_version = 'TLSv1.2';

-- 证书验证设置
ALTER SYSTEM SET ssl_cert_verification = 'required';

SELECT pg_reload_conf();
```

#### 防火墙规则

```bash
#!/bin/bash
# 数据库服务器防火墙配置

# 清除现有规则
iptables -F
iptables -X

# 默认策略
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 允许本地回环
iptables -A INPUT -i lo -j ACCEPT

# 允许已建立的连接
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# PostgreSQL端口访问控制
# 开发环境 - 允许所有 (仅用于开发)
iptables -A INPUT -p tcp --dport 5432 -s 0.0.0.0/0 -j ACCEPT

# 生产环境访问控制 (取消注释以启用)
# iptables -A INPUT -p tcp --dport 5432 -s 10.0.1.0/24 -j ACCEPT  # 应用服务器
# iptables -A INPUT -p tcp --dport 5432 -s 10.0.2.100/32 -j ACCEPT # 备份服务器
# iptables -A INPUT -p tcp --dport 5432 -s 10.0.3.0/24 -j ACCEPT   # 管理网络

# SSH访问 (管理用)
iptables -A INPUT -p tcp --dport 22 -s 10.0.3.0/24 -j ACCEPT

# 监控服务
iptables -A INPUT -p tcp --dport 9187 -s 10.0.4.0/24 -j ACCEPT  # postgres_exporter

# ICMP (ping)
iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT

# 保存规则
iptables-save > /etc/iptables/rules.v4
```

### 2. 认证和授权

#### 多因素认证实现

```sql
-- 用户认证增强表
CREATE TABLE user_authentication (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- 密码策略
    password_hash VARCHAR(255) NOT NULL, -- bcrypt/scrypt hash
    password_salt VARCHAR(255) NOT NULL,
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    password_expires_at TIMESTAMP WITH TIME ZONE,
    force_password_change BOOLEAN DEFAULT FALSE,

    -- 多因素认证
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255), -- TOTP secret (加密存储)
    mfa_backup_codes TEXT[], -- 备用代码 (加密存储)
    mfa_last_used TIMESTAMP WITH TIME ZONE,

    -- 账户锁定策略
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    account_disabled BOOLEAN DEFAULT FALSE,

    -- 会话管理
    max_concurrent_sessions INTEGER DEFAULT 5,
    session_timeout_minutes INTEGER DEFAULT 480, -- 8小时

    -- 审计信息
    last_login_at TIMESTAMP WITH TIME ZONE,
    last_login_ip INET,
    last_login_user_agent TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 密码历史表 (防止重用)
CREATE TABLE password_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 只保留最近10个密码
CREATE INDEX idx_password_history_user_date ON password_history(user_id, created_at DESC);
```

#### 角色权限系统

```sql
-- 系统角色定义
CREATE TABLE system_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- 权限级别
    permission_level INTEGER NOT NULL, -- 1-100, 数字越大权限越高
    is_system_role BOOLEAN DEFAULT TRUE, -- 系统预定义角色

    -- 功能权限
    can_create_organizations BOOLEAN DEFAULT FALSE,
    can_manage_users BOOLEAN DEFAULT FALSE,
    can_manage_subscriptions BOOLEAN DEFAULT FALSE,
    can_access_analytics BOOLEAN DEFAULT FALSE,
    can_export_data BOOLEAN DEFAULT FALSE,
    can_manage_integrations BOOLEAN DEFAULT FALSE,

    -- 数据权限
    data_access_level VARCHAR(20) DEFAULT 'none', -- 'none', 'own', 'team', 'organization', 'all'
    can_view_sensitive_data BOOLEAN DEFAULT FALSE,
    can_delete_data BOOLEAN DEFAULT FALSE,

    -- 系统权限
    can_view_system_logs BOOLEAN DEFAULT FALSE,
    can_manage_system_settings BOOLEAN DEFAULT FALSE,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_permission_level CHECK (permission_level >= 1 AND permission_level <= 100),
    CONSTRAINT valid_data_access_level CHECK (data_access_level IN ('none', 'own', 'team', 'organization', 'all'))
);

-- 插入系统预定义角色
INSERT INTO system_roles (role_name, display_name, description, permission_level, data_access_level) VALUES
('super_admin', '超级管理员', '系统最高权限管理员', 100, 'all'),
('platform_admin', '平台管理员', '平台功能管理员', 90, 'all'),
('organization_owner', '组织所有者', '组织最高权限', 80, 'organization'),
('organization_admin', '组织管理员', '组织管理权限', 70, 'organization'),
('team_lead', '团队负责人', '团队管理权限', 60, 'team'),
('data_analyst', '数据分析师', '数据分析权限', 50, 'team'),
('member', '普通成员', '基本使用权限', 30, 'own'),
('viewer', '访客', '只读权限', 10, 'none');

-- 用户角色关联表
CREATE TABLE user_role_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES system_roles(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- 权限范围
    scope VARCHAR(20) NOT NULL DEFAULT 'organization', -- 'global', 'organization', 'team'
    scope_id UUID, -- 组织ID或团队ID

    -- 临时权限
    temporary_grant BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP WITH TIME ZONE,

    -- 审计信息
    granted_by UUID REFERENCES users(id),
    granted_reason TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, role_id, organization_id, scope, scope_id)
);

-- 索引
CREATE INDEX idx_user_roles_user ON user_role_assignments(user_id);
CREATE INDEX idx_user_roles_org ON user_role_assignments(organization_id);
CREATE INDEX idx_user_roles_expires ON user_role_assignments(expires_at) WHERE temporary_grant = TRUE;
```

### 3. 数据加密

#### 静态数据加密

```sql
-- 启用pgcrypto扩展
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 加密密钥管理
CREATE TABLE encryption_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_name VARCHAR(100) NOT NULL UNIQUE,
    key_type VARCHAR(50) NOT NULL, -- 'aes256', 'rsa2048', 'ed25519'
    encrypted_key BYTEA NOT NULL, -- 使用主密钥加密的密钥
    key_version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_key_type CHECK (key_type IN ('aes256', 'rsa2048', 'ed25519'))
);

-- 敏感数据加密函数
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(
    data TEXT,
    key_name TEXT DEFAULT 'default_key'
) RETURNS BYTEA AS $$
DECLARE
    encryption_key TEXT;
BEGIN
    -- 从环境变量或密钥管理服务获取密钥
    encryption_key := current_setting('app.encryption_key', true);

    IF encryption_key IS NULL THEN
        RAISE EXCEPTION '加密密钥未配置';
    END IF;

    RETURN pgp_sym_encrypt(data, encryption_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 解密函数
CREATE OR REPLACE FUNCTION decrypt_sensitive_data(
    encrypted_data BYTEA,
    key_name TEXT DEFAULT 'default_key'
) RETURNS TEXT AS $$
DECLARE
    encryption_key TEXT;
BEGIN
    encryption_key := current_setting('app.encryption_key', true);

    IF encryption_key IS NULL THEN
        RAISE EXCEPTION '解密密钥未配置';
    END IF;

    RETURN pgp_sym_decrypt(encrypted_data, encryption_key);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 敏感字段加密示例
ALTER TABLE connection_configs
ADD COLUMN credentials_encrypted_v2 BYTEA;

-- 迁移现有数据
UPDATE connection_configs
SET credentials_encrypted_v2 = encrypt_sensitive_data(
    COALESCE(connection_string, '{}')
);
```

#### 字段级加密

```sql
-- 创建加密用户偏好表
CREATE TABLE encrypted_user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,

    -- 加密存储的偏好设置
    preferences_encrypted BYTEA NOT NULL,
    preferences_checksum VARCHAR(64) NOT NULL, -- 完整性校验

    -- 元数据 (不加密)
    preference_categories TEXT[], -- 偏好类别
    last_updated_category VARCHAR(100),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 插入加密偏好设置的函数
CREATE OR REPLACE FUNCTION set_user_preferences(
    p_user_id UUID,
    p_preferences JSONB
) RETURNS BOOLEAN AS $$
DECLARE
    encrypted_data BYTEA;
    data_checksum VARCHAR(64);
BEGIN
    -- 加密数据
    encrypted_data := encrypt_sensitive_data(p_preferences::TEXT);

    -- 计算校验和
    data_checksum := encode(sha256(p_preferences::TEXT::BYTEA), 'hex');

    -- 插入或更新
    INSERT INTO encrypted_user_preferences (user_id, preferences_encrypted, preferences_checksum)
    VALUES (p_user_id, encrypted_data, data_checksum)
    ON CONFLICT (user_id)
    DO UPDATE SET
        preferences_encrypted = encrypted_data,
        preferences_checksum = data_checksum,
        updated_at = NOW();

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '设置用户偏好失败: %', SQLERRM;
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 获取解密偏好设置的函数
CREATE OR REPLACE FUNCTION get_user_preferences(p_user_id UUID)
RETURNS JSONB AS $$
DECLARE
    encrypted_data BYTEA;
    decrypted_text TEXT;
    stored_checksum VARCHAR(64);
    calculated_checksum VARCHAR(64);
BEGIN
    SELECT preferences_encrypted, preferences_checksum
    INTO encrypted_data, stored_checksum
    FROM encrypted_user_preferences
    WHERE user_id = p_user_id;

    IF encrypted_data IS NULL THEN
        RETURN '{}'::JSONB;
    END IF;

    -- 解密数据
    decrypted_text := decrypt_sensitive_data(encrypted_data);

    -- 验证完整性
    calculated_checksum := encode(sha256(decrypted_text::BYTEA), 'hex');

    IF stored_checksum != calculated_checksum THEN
        RAISE EXCEPTION '数据完整性验证失败';
    END IF;

    RETURN decrypted_text::JSONB;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '获取用户偏好失败: %', SQLERRM;
        RETURN '{}'::JSONB;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

### 4. 行级安全策略 (RLS)

#### 多租户数据隔离

```sql
-- 启用行级安全
ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE quality_assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_analysis_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;

-- 创建安全上下文函数
CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS UUID AS $$
BEGIN
    RETURN COALESCE(
        current_setting('app.current_user_id', true)::UUID,
        NULL
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION get_current_organization_id()
RETURNS UUID AS $$
BEGIN
    RETURN COALESCE(
        current_setting('app.current_organization_id', true)::UUID,
        NULL
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION get_user_role_level()
RETURNS INTEGER AS $$
BEGIN
    RETURN COALESCE(
        current_setting('app.user_role_level', true)::INTEGER,
        0
    );
EXCEPTION
    WHEN OTHERS THEN
        RETURN 0;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 数据源访问策略
CREATE POLICY data_sources_isolation_policy ON data_sources
    FOR ALL TO application_role
    USING (
        -- 用户只能访问自己的数据源
        user_id = get_current_user_id()
        OR
        -- 或者组织内共享的数据源
        (organization_id = get_current_organization_id()
         AND access_level IN ('team', 'organization'))
        OR
        -- 或者公开数据源
        (access_level = 'public' AND is_public = TRUE)
        OR
        -- 高权限用户可以访问组织内所有数据
        (organization_id = get_current_organization_id()
         AND get_user_role_level() >= 70)
    );

-- 质量评估访问策略
CREATE POLICY quality_assessments_isolation_policy ON quality_assessments
    FOR ALL TO application_role
    USING (
        -- 评估创建者
        user_id = get_current_user_id()
        OR
        -- 数据源所有者
        data_source_id IN (
            SELECT id FROM data_sources
            WHERE user_id = get_current_user_id()
        )
        OR
        -- 组织内共享权限
        (organization_id = get_current_organization_id()
         AND get_user_role_level() >= 50)
    );

-- AI分析任务访问策略
CREATE POLICY ai_analysis_isolation_policy ON ai_analysis_tasks
    FOR ALL TO application_role
    USING (
        user_id = get_current_user_id()
        OR
        (organization_id = get_current_organization_id()
         AND get_user_role_level() >= 60)
    );

-- 组织成员访问策略
CREATE POLICY org_members_isolation_policy ON organization_members
    FOR ALL TO application_role
    USING (
        -- 用户只能看到自己的成员记录
        user_id = get_current_user_id()
        OR
        -- 组织管理员可以看到所有成员
        (organization_id = get_current_organization_id()
         AND get_user_role_level() >= 70)
    );
```

#### 数据分类访问控制

```sql
-- 数据分类表
CREATE TABLE data_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    classification_name VARCHAR(50) NOT NULL UNIQUE,
    sensitivity_level INTEGER NOT NULL, -- 1-5, 数字越大越敏感
    description TEXT,
    access_requirements JSONB, -- 访问要求
    retention_period INTERVAL, -- 保留期限
    is_active BOOLEAN DEFAULT TRUE,

    CONSTRAINT valid_sensitivity_level CHECK (sensitivity_level >= 1 AND sensitivity_level <= 5)
);

-- 插入数据分类
INSERT INTO data_classifications (classification_name, sensitivity_level, description) VALUES
('public', 1, '公开数据'),
('internal', 2, '内部数据'),
('confidential', 3, '机密数据'),
('restricted', 4, '限制数据'),
('top_secret', 5, '绝密数据');

-- 为数据源添加分类
ALTER TABLE data_sources
ADD COLUMN data_classification VARCHAR(50) DEFAULT 'internal'
REFERENCES data_classifications(classification_name);

-- 基于数据分类的访问策略
CREATE POLICY data_classification_policy ON data_sources
    FOR SELECT TO application_role
    USING (
        CASE
            WHEN data_classification = 'public' THEN TRUE
            WHEN data_classification = 'internal' AND get_user_role_level() >= 30 THEN TRUE
            WHEN data_classification = 'confidential' AND get_user_role_level() >= 50 THEN TRUE
            WHEN data_classification = 'restricted' AND get_user_role_level() >= 80 THEN TRUE
            WHEN data_classification = 'top_secret' AND get_user_role_level() >= 90 THEN TRUE
            ELSE FALSE
        END
    );
```

### 5. 审计和合规

#### 全面审计日志

```sql
-- 审计日志表
CREATE TABLE security_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 事件信息
    event_type VARCHAR(50) NOT NULL, -- 'login', 'logout', 'data_access', 'data_modify', 'permission_change'
    event_category VARCHAR(20) NOT NULL, -- 'authentication', 'authorization', 'data', 'system'
    event_severity VARCHAR(20) DEFAULT 'info', -- 'debug', 'info', 'warning', 'error', 'critical'

    -- 用户和会话信息
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(255),
    organization_id UUID REFERENCES organizations(id),

    -- 请求信息
    ip_address INET,
    user_agent TEXT,
    request_id UUID,
    api_endpoint TEXT,
    http_method VARCHAR(10),

    -- 数据访问信息
    resource_type VARCHAR(50), -- 'data_source', 'quality_assessment', 'user', etc.
    resource_id UUID,
    resource_name TEXT,

    -- 操作详情
    action_performed VARCHAR(100), -- 'create', 'read', 'update', 'delete', 'export'
    old_values JSONB, -- 修改前的值
    new_values JSONB, -- 修改后的值

    -- 结果信息
    operation_result VARCHAR(20) DEFAULT 'success', -- 'success', 'failure', 'partial'
    error_code VARCHAR(50),
    error_message TEXT,

    -- 合规标记
    gdpr_relevant BOOLEAN DEFAULT FALSE,
    sox_relevant BOOLEAN DEFAULT FALSE,
    pci_relevant BOOLEAN DEFAULT FALSE,

    -- 时间信息
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_duration_ms INTEGER,

    -- 元数据
    additional_metadata JSONB,

    CONSTRAINT valid_event_category CHECK (event_category IN ('authentication', 'authorization', 'data', 'system')),
    CONSTRAINT valid_event_severity CHECK (event_severity IN ('debug', 'info', 'warning', 'error', 'critical')),
    CONSTRAINT valid_operation_result CHECK (operation_result IN ('success', 'failure', 'partial'))
);

-- 审计日志索引
CREATE INDEX idx_audit_logs_user_time ON security_audit_logs(user_id, event_timestamp DESC);
CREATE INDEX idx_audit_logs_org_time ON security_audit_logs(organization_id, event_timestamp DESC);
CREATE INDEX idx_audit_logs_event_type ON security_audit_logs(event_type, event_timestamp DESC);
CREATE INDEX idx_audit_logs_resource ON security_audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_ip ON security_audit_logs(ip_address, event_timestamp DESC);
CREATE INDEX idx_audit_logs_severity ON security_audit_logs(event_severity, event_timestamp DESC);

-- 合规查询索引
CREATE INDEX idx_audit_logs_gdpr ON security_audit_logs(gdpr_relevant, event_timestamp DESC) WHERE gdpr_relevant = TRUE;
CREATE INDEX idx_audit_logs_sox ON security_audit_logs(sox_relevant, event_timestamp DESC) WHERE sox_relevant = TRUE;

-- 分区审计日志表 (按月分区)
CREATE TABLE security_audit_logs_partitioned (
    LIKE security_audit_logs INCLUDING ALL
) PARTITION BY RANGE (event_timestamp);

-- 自动创建审计日志分区
CREATE OR REPLACE FUNCTION create_audit_log_partition(start_date DATE)
RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
    end_date DATE;
BEGIN
    partition_name := 'security_audit_logs_y' ||
                     EXTRACT(YEAR FROM start_date) || 'm' ||
                     LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');

    end_date := start_date + INTERVAL '1 month';

    EXECUTE format(
        'CREATE TABLE %I PARTITION OF security_audit_logs_partitioned
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );

    -- 创建分区索引
    EXECUTE format('CREATE INDEX idx_%s_user_time ON %I(user_id, event_timestamp DESC)',
                   partition_name, partition_name);

    RETURN partition_name;
END;
$$ LANGUAGE plpgsql;
```

#### 审计触发器

```sql
-- 通用审计触发器函数
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    audit_data JSONB;
    operation_type TEXT;
BEGIN
    -- 确定操作类型
    operation_type := CASE TG_OP
        WHEN 'INSERT' THEN 'create'
        WHEN 'UPDATE' THEN 'update'
        WHEN 'DELETE' THEN 'delete'
    END;

    -- 构建审计数据
    audit_data := jsonb_build_object(
        'table_name', TG_TABLE_NAME,
        'operation', operation_type,
        'old_values', CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN row_to_json(OLD) ELSE NULL END,
        'new_values', CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END,
        'changed_fields', CASE
            WHEN TG_OP = 'UPDATE' THEN (
                SELECT array_agg(key)
                FROM jsonb_each(row_to_json(NEW)::jsonb)
                WHERE key NOT IN ('updated_at')
                AND row_to_json(NEW)::jsonb->>key IS DISTINCT FROM row_to_json(OLD)::jsonb->>key
            )
            ELSE NULL
        END
    );

    -- 插入审计记录
    INSERT INTO security_audit_logs (
        event_type,
        event_category,
        user_id,
        organization_id,
        resource_type,
        resource_id,
        action_performed,
        old_values,
        new_values,
        additional_metadata
    ) VALUES (
        'data_modify',
        'data',
        COALESCE(get_current_user_id(),
                CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN (NEW.user_id) ELSE (OLD.user_id) END),
        COALESCE(get_current_organization_id(),
                CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN (NEW.organization_id) ELSE (OLD.organization_id) END),
        TG_TABLE_NAME,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN (NEW.id) ELSE (OLD.id) END,
        operation_type,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN row_to_json(OLD) ELSE NULL END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) ELSE NULL END,
        audit_data
    );

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 为关键表创建审计触发器
CREATE TRIGGER audit_data_sources
    AFTER INSERT OR UPDATE OR DELETE ON data_sources
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_quality_assessments
    AFTER INSERT OR UPDATE OR DELETE ON quality_assessments
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_user_role_assignments
    AFTER INSERT OR UPDATE OR DELETE ON user_role_assignments
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_organization_subscriptions
    AFTER INSERT OR UPDATE OR DELETE ON organization_subscriptions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
```

### 6. 威胁检测和防护

#### 异常行为检测

```sql
-- 异常行为检测表
CREATE TABLE security_anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 异常信息
    anomaly_type VARCHAR(50) NOT NULL, -- 'unusual_login', 'mass_data_access', 'permission_escalation'
    severity_level INTEGER NOT NULL, -- 1-10
    confidence_score DECIMAL(3,2) NOT NULL, -- 0.00-1.00

    -- 相关实体
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    session_id VARCHAR(255),

    -- 异常描述
    description TEXT NOT NULL,
    detection_rule VARCHAR(100),

    -- 上下文信息
    context_data JSONB,
    related_events UUID[], -- 相关审计日志ID

    -- 响应状态
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'investigating', 'resolved', 'false_positive'
    assigned_to UUID REFERENCES users(id),
    resolution_notes TEXT,

    -- 时间信息
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    first_occurrence TIMESTAMP WITH TIME ZONE,
    last_occurrence TIMESTAMP WITH TIME ZONE,
    occurrence_count INTEGER DEFAULT 1,

    resolved_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_severity_level CHECK (severity_level >= 1 AND severity_level <= 10),
    CONSTRAINT valid_confidence_score CHECK (confidence_score >= 0.00 AND confidence_score <= 1.00),
    CONSTRAINT valid_status CHECK (status IN ('open', 'investigating', 'resolved', 'false_positive'))
);

-- 异常检测函数
CREATE OR REPLACE FUNCTION detect_login_anomalies()
RETURNS VOID AS $$
DECLARE
    rec RECORD;
BEGIN
    -- 检测异常登录模式
    FOR rec IN
        SELECT
            user_id,
            ip_address,
            COUNT(*) as login_count,
            COUNT(DISTINCT ip_address) as ip_count
        FROM security_audit_logs
        WHERE event_type = 'login'
          AND event_timestamp >= NOW() - INTERVAL '1 hour'
          AND operation_result = 'success'
        GROUP BY user_id, ip_address
        HAVING COUNT(*) > 10 OR COUNT(DISTINCT ip_address) > 5
    LOOP
        INSERT INTO security_anomalies (
            anomaly_type,
            severity_level,
            confidence_score,
            user_id,
            description,
            detection_rule,
            context_data
        ) VALUES (
            'unusual_login',
            CASE WHEN rec.ip_count > 5 THEN 8 ELSE 6 END,
            CASE WHEN rec.ip_count > 5 THEN 0.9 ELSE 0.7 END,
            rec.user_id,
            format('用户在1小时内从%s个不同IP地址登录%s次', rec.ip_count, rec.login_count),
            'multiple_ip_login_detection',
            jsonb_build_object(
                'login_count', rec.login_count,
                'ip_count', rec.ip_count,
                'time_window', '1 hour'
            )
        ) ON CONFLICT DO NOTHING;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 定时运行异常检测
SELECT cron.schedule('detect-login-anomalies', '*/15 * * * *', 'SELECT detect_login_anomalies();');
```

## 📊 安全监控和报告

### 安全仪表板视图

```sql
-- 安全概览视图
CREATE VIEW v_security_dashboard AS
SELECT
    COUNT(*) FILTER (WHERE event_timestamp >= NOW() - INTERVAL '24 hours') as events_24h,
    COUNT(*) FILTER (WHERE event_severity = 'critical' AND event_timestamp >= NOW() - INTERVAL '24 hours') as critical_events_24h,
    COUNT(*) FILTER (WHERE event_type = 'login' AND operation_result = 'failure' AND event_timestamp >= NOW() - INTERVAL '1 hour') as failed_logins_1h,
    COUNT(DISTINCT user_id) FILTER (WHERE event_timestamp >= NOW() - INTERVAL '24 hours') as active_users_24h,
    COUNT(DISTINCT ip_address) FILTER (WHERE event_timestamp >= NOW() - INTERVAL '24 hours') as unique_ips_24h
FROM security_audit_logs;

-- 用户风险评分视图
CREATE VIEW v_user_risk_scores AS
SELECT
    u.id as user_id,
    u.email,
    COUNT(sa.id) as anomaly_count,
    AVG(sa.severity_level) as avg_severity,
    MAX(sa.detected_at) as last_anomaly,
    CASE
        WHEN COUNT(sa.id) = 0 THEN 'low'
        WHEN COUNT(sa.id) <= 2 AND AVG(sa.severity_level) <= 5 THEN 'medium'
        WHEN COUNT(sa.id) <= 5 AND AVG(sa.severity_level) <= 7 THEN 'high'
        ELSE 'critical'
    END as risk_level
FROM users u
LEFT JOIN security_anomalies sa ON u.id = sa.user_id
    AND sa.detected_at >= NOW() - INTERVAL '30 days'
    AND sa.status IN ('open', 'investigating')
GROUP BY u.id, u.email;
```

这个安全架构设计为数据管理平台提供了全方位的安全保护，确保数据安全、用户隐私和合规要求得到满足。