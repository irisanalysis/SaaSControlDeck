-- ===========================================
-- SaaS Control Deck 三环境数据库创建脚本
-- ===========================================
-- 执行用户: jackchan (超级用户)
-- 目标服务器: 47.79.87.199:5432
-- 执行顺序: 第一步 - 创建数据库
-- ===========================================

\echo '创建SaaS Control Deck三环境数据库...'

-- ===========================================
-- 开发环境数据库
-- ===========================================

\echo '创建开发环境数据库...'

-- 创建开发环境数据库 pro1
CREATE DATABASE saascontrol_dev_pro1
    WITH 
    OWNER = jackchan
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 50
    TEMPLATE = template0;

COMMENT ON DATABASE saascontrol_dev_pro1 IS 'SaaS Control Deck 开发环境 - Backend Pro1 服务组 (端口8000-8002)';

-- 创建开发环境数据库 pro2
CREATE DATABASE saascontrol_dev_pro2
    WITH 
    OWNER = jackchan
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 50
    TEMPLATE = template0;

COMMENT ON DATABASE saascontrol_dev_pro2 IS 'SaaS Control Deck 开发环境 - Backend Pro2 服务组 (端口8100-8102)';

-- ===========================================
-- 测试环境数据库
-- ===========================================

\echo '创建测试环境数据库...'

-- 创建测试环境数据库 pro1
CREATE DATABASE saascontrol_stage_pro1
    WITH 
    OWNER = jackchan
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 100
    TEMPLATE = template0;

COMMENT ON DATABASE saascontrol_stage_pro1 IS 'SaaS Control Deck 测试环境 - Backend Pro1 服务组';

-- 创建测试环境数据库 pro2
CREATE DATABASE saascontrol_stage_pro2
    WITH 
    OWNER = jackchan
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 100
    TEMPLATE = template0;

COMMENT ON DATABASE saascontrol_stage_pro2 IS 'SaaS Control Deck 测试环境 - Backend Pro2 服务组';

-- ===========================================
-- 生产环境数据库
-- ===========================================

\echo '创建生产环境数据库...'

-- 创建生产环境数据库 pro1
CREATE DATABASE saascontrol_prod_pro1
    WITH 
    OWNER = jackchan
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 200
    TEMPLATE = template0;

COMMENT ON DATABASE saascontrol_prod_pro1 IS 'SaaS Control Deck 生产环境 - Backend Pro1 服务组';

-- 创建生产环境数据库 pro2
CREATE DATABASE saascontrol_prod_pro2
    WITH 
    OWNER = jackchan
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 200
    TEMPLATE = template0;

COMMENT ON DATABASE saascontrol_prod_pro2 IS 'SaaS Control Deck 生产环境 - Backend Pro2 服务组';

-- ===========================================
-- 验证数据库创建
-- ===========================================

\echo '验证数据库创建结果...'

-- 显示所有SaaS Control Deck相关数据库
SELECT 
    datname AS database_name,
    pg_get_userbyid(datdba) AS owner,
    encoding,
    datcollate AS collate,
    datctype AS ctype,
    datconnlimit AS connection_limit,
    obj_description(oid, 'pg_database') AS description
FROM pg_database 
WHERE datname LIKE 'saascontrol_%'
ORDER BY datname;

\echo '数据库创建完成！请继续执行用户权限脚本。';

-- ===========================================
-- 执行说明
-- ===========================================
/*
执行命令:
psql -h 47.79.87.199 -U jackchan -d postgres -f 01-create-databases.sql

执行后验证:
psql -h 47.79.87.199 -U jackchan -d postgres -c "\l | grep saascontrol"

下一步:
执行 02-create-users-permissions.sql 创建用户和权限
*/