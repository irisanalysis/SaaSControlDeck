-- ===========================================
-- SaaS Control Deck 用户和权限配置脚本
-- ===========================================
-- 执行用户: jackchan (超级用户)
-- 目标服务器: 47.79.87.199:5432
-- 执行顺序: 第二步 - 创建用户和权限
-- ===========================================

\echo '创建SaaS Control Deck环境专用用户...'

-- ===========================================
-- 开发环境用户 (开放权限)
-- ===========================================

\echo '创建开发环境用户...'

-- 开发环境 Pro1 用户
CREATE USER saasctl_dev_pro1_user WITH
    PASSWORD 'dev_pro1_secure_2025!'
    NOSUPERUSER
    CREATEDB
    CREATEROLE
    INHERIT
    LOGIN
    NOREPLICATION
    NOBYPASSRLS
    CONNECTION LIMIT 25;

COMMENT ON ROLE saasctl_dev_pro1_user IS 'SaaS Control Deck 开发环境 Pro1 服务专用用户';

-- 开发环境 Pro2 用户
CREATE USER saasctl_dev_pro2_user WITH
    PASSWORD 'dev_pro2_secure_2025!'
    NOSUPERUSER
    CREATEDB
    CREATEROLE
    INHERIT
    LOGIN
    NOREPLICATION
    NOBYPASSRLS
    CONNECTION LIMIT 25;

COMMENT ON ROLE saasctl_dev_pro2_user IS 'SaaS Control Deck 开发环境 Pro2 服务专用用户';

-- ===========================================
-- 测试环境用户 (受限权限)
-- ===========================================

\echo '创建测试环境用户...'

-- 测试环境 Pro1 用户
CREATE USER saasctl_stage_pro1_user WITH
    PASSWORD 'stage_pro1_secure_2025!'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    INHERIT
    LOGIN
    NOREPLICATION
    NOBYPASSRLS
    CONNECTION LIMIT 50;

COMMENT ON ROLE saasctl_stage_pro1_user IS 'SaaS Control Deck 测试环境 Pro1 服务专用用户';

-- 测试环境 Pro2 用户
CREATE USER saasctl_stage_pro2_user WITH
    PASSWORD 'stage_pro2_secure_2025!'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    INHERIT
    LOGIN
    NOREPLICATION
    NOBYPASSRLS
    CONNECTION LIMIT 50;

COMMENT ON ROLE saasctl_stage_pro2_user IS 'SaaS Control Deck 测试环境 Pro2 服务专用用户';

-- ===========================================
-- 生产环境用户 (严格权限)
-- ===========================================

\echo '创建生产环境用户...'

-- 生产环境 Pro1 用户
CREATE USER saasctl_prod_pro1_user WITH
    PASSWORD 'prod_pro1_ULTRA_secure_2025#$%'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    INHERIT
    LOGIN
    NOREPLICATION
    NOBYPASSRLS
    CONNECTION LIMIT 100;

COMMENT ON ROLE saasctl_prod_pro1_user IS 'SaaS Control Deck 生产环境 Pro1 服务专用用户';

-- 生产环境 Pro2 用户
CREATE USER saasctl_prod_pro2_user WITH
    PASSWORD 'prod_pro2_ULTRA_secure_2025#$%'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    INHERIT
    LOGIN
    NOREPLICATION
    NOBYPASSRLS
    CONNECTION LIMIT 100;

COMMENT ON ROLE saasctl_prod_pro2_user IS 'SaaS Control Deck 生产环境 Pro2 服务专用用户';

-- ===========================================
-- 分配数据库所有权和连接权限
-- ===========================================

\echo '分配数据库所有权和连接权限...'

-- 开发环境数据库权限
GRANT ALL PRIVILEGES ON DATABASE saascontrol_dev_pro1 TO saasctl_dev_pro1_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_dev_pro2 TO saasctl_dev_pro2_user;

-- 测试环境数据库权限
GRANT ALL PRIVILEGES ON DATABASE saascontrol_stage_pro1 TO saasctl_stage_pro1_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_stage_pro2 TO saasctl_stage_pro2_user;

-- 生产环境数据库权限
GRANT ALL PRIVILEGES ON DATABASE saascontrol_prod_pro1 TO saasctl_prod_pro1_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_prod_pro2 TO saasctl_prod_pro2_user;

-- ===========================================
-- 创建应用角色 (用于业务逻辑权限控制)
-- ===========================================

\echo '创建应用角色...'

-- 开发环境角色
CREATE ROLE saasctl_dev_app_role NOLOGIN;
COMMENT ON ROLE saasctl_dev_app_role IS '开发环境应用业务逻辑角色';

-- 测试环境角色  
CREATE ROLE saasctl_stage_app_role NOLOGIN;
COMMENT ON ROLE saasctl_stage_app_role IS '测试环境应用业务逻辑角色';

-- 生产环境角色
CREATE ROLE saasctl_prod_app_role NOLOGIN;
COMMENT ON ROLE saasctl_prod_app_role IS '生产环境应用业务逻辑角色';

-- 将角色分配给用户
GRANT saasctl_dev_app_role TO saasctl_dev_pro1_user;
GRANT saasctl_dev_app_role TO saasctl_dev_pro2_user;
GRANT saasctl_stage_app_role TO saasctl_stage_pro1_user;
GRANT saasctl_stage_app_role TO saasctl_stage_pro2_user;
GRANT saasctl_prod_app_role TO saasctl_prod_pro1_user;
GRANT saasctl_prod_app_role TO saasctl_prod_pro2_user;

-- ===========================================
-- 为每个数据库启用特殊扩展
-- ===========================================

\echo '为数据库启用特殊扩展...'

-- 在开发环境中启用扩展
\c saascontrol_dev_pro1
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
\c postgres

\c saascontrol_dev_pro2
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
\c postgres

-- 在测试环境中启用扩展
\c saascontrol_stage_pro1
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
\c postgres

\c saascontrol_stage_pro2
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
\c postgres

-- 在生产环境中启用扩展
\c saascontrol_prod_pro1
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
\c postgres

\c saascontrol_prod_pro2
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
\c postgres

-- ===========================================
-- 验证用户创建
-- ===========================================

\echo '验证用户创建结果...'

-- 显示所有SaaS Control Deck相关用户
SELECT 
    rolname AS username,
    rolsuper AS is_superuser,
    rolcreatedb AS can_create_db,
    rolcreaterole AS can_create_role,
    rolcanlogin AS can_login,
    rolconnlimit AS connection_limit,
    obj_description(oid, 'pg_authid') AS description
FROM pg_roles 
WHERE rolname LIKE 'saasctl_%'
ORDER BY rolname;

-- 显示数据库权限
SELECT 
    d.datname AS database_name,
    r.rolname AS username,
    CASE 
        WHEN has_database_privilege(r.rolname, d.datname, 'CONNECT') THEN 'CONNECT '
        ELSE ''
    END ||
    CASE 
        WHEN has_database_privilege(r.rolname, d.datname, 'CREATE') THEN 'CREATE '
        ELSE ''
    END ||
    CASE 
        WHEN has_database_privilege(r.rolname, d.datname, 'TEMPORARY') THEN 'TEMP '
        ELSE ''
    END AS privileges
FROM pg_database d
CROSS JOIN pg_roles r
WHERE d.datname LIKE 'saascontrol_%' 
    AND r.rolname LIKE 'saasctl_%'
ORDER BY d.datname, r.rolname;

\echo '用户和权限配置完成！请继续执行表结构创建脚本。';

-- ===========================================
-- 执行说明
-- ===========================================
/*
执行命令:
psql -h 47.79.87.199 -U jackchan -d postgres -f 02-create-users-permissions.sql

执行后验证:
psql -h 47.79.87.199 -U jackchan -d postgres -c "\du | grep saasctl"

测试连接:
psql -h 47.79.87.199 -U saasctl_dev_pro1_user -d saascontrol_dev_pro1 -c "SELECT version();"

下一步:
执行 03-create-table-structure.sql 创建表结构

密码信息:
- 开发环境: dev_pro1_secure_2025!, dev_pro2_secure_2025!
- 测试环境: stage_pro1_secure_2025!, stage_pro2_secure_2025!
- 生产环境: prod_pro1_ULTRA_secure_2025#$%, prod_pro2_ULTRA_secure_2025#$%
*/