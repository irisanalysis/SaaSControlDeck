-- ===========================================
-- SaaS Control Deck - 三环境数据库架构创建脚本
-- ===========================================
-- 目标PostgreSQL: 47.79.87.199:5432
-- 基础数据库: iris
-- 用户: jackchan

-- ===========================================
-- 1. 创建三环境数据库
-- ===========================================

-- 开发环境数据库
DROP DATABASE IF EXISTS saascontrol_dev_pro1;
DROP DATABASE IF EXISTS saascontrol_dev_pro2;

CREATE DATABASE saascontrol_dev_pro1 
    WITH OWNER = jackchan
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 50
    TEMPLATE = template0;

CREATE DATABASE saascontrol_dev_pro2 
    WITH OWNER = jackchan
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8' 
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 50
    TEMPLATE = template0;

-- 测试环境数据库
DROP DATABASE IF EXISTS saascontrol_stage_pro1;
DROP DATABASE IF EXISTS saascontrol_stage_pro2;

CREATE DATABASE saascontrol_stage_pro1 
    WITH OWNER = jackchan
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 30
    TEMPLATE = template0;

CREATE DATABASE saascontrol_stage_pro2 
    WITH OWNER = jackchan
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 30
    TEMPLATE = template0;

-- 生产环境数据库
DROP DATABASE IF EXISTS saascontrol_prod_pro1;
DROP DATABASE IF EXISTS saascontrol_prod_pro2;

CREATE DATABASE saascontrol_prod_pro1 
    WITH OWNER = jackchan
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 100
    TEMPLATE = template0;

CREATE DATABASE saascontrol_prod_pro2 
    WITH OWNER = jackchan
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = 100
    TEMPLATE = template0;

-- ===========================================
-- 2. 创建环境专用用户
-- ===========================================

-- 开发环境用户 (较宽松权限)
DROP USER IF EXISTS saascontrol_dev_user;
CREATE USER saascontrol_dev_user WITH 
    PASSWORD 'dev_pass_2024_secure'
    CREATEDB
    NOSUPERUSER
    NOCREATEROLE
    INHERIT
    LOGIN
    CONNECTION LIMIT 20;

-- 测试环境用户 (中等权限)  
DROP USER IF EXISTS saascontrol_stage_user;
CREATE USER saascontrol_stage_user WITH
    PASSWORD 'stage_pass_2024_secure'
    NOCREATEDB
    NOSUPERUSER
    NOCREATEROLE
    INHERIT
    LOGIN
    CONNECTION LIMIT 15;

-- 生产环境用户 (严格权限)
DROP USER IF EXISTS saascontrol_prod_user;
CREATE USER saascontrol_prod_user WITH
    PASSWORD 'prod_pass_2024_very_secure_XyZ9#mK'
    NOCREATEDB
    NOSUPERUSER
    NOCREATEROLE
    INHERIT
    LOGIN
    CONNECTION LIMIT 50;

-- ===========================================
-- 3. 数据库权限分配
-- ===========================================

-- 开发环境权限
GRANT ALL PRIVILEGES ON DATABASE saascontrol_dev_pro1 TO saascontrol_dev_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_dev_pro2 TO saascontrol_dev_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_dev_pro1 TO jackchan;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_dev_pro2 TO jackchan;

-- 测试环境权限
GRANT ALL PRIVILEGES ON DATABASE saascontrol_stage_pro1 TO saascontrol_stage_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_stage_pro2 TO saascontrol_stage_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_stage_pro1 TO jackchan;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_stage_pro2 TO jackchan;

-- 生产环境权限
GRANT ALL PRIVILEGES ON DATABASE saascontrol_prod_pro1 TO saascontrol_prod_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_prod_pro2 TO saascontrol_prod_user;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_prod_pro1 TO jackchan;
GRANT ALL PRIVILEGES ON DATABASE saascontrol_prod_pro2 TO jackchan;

-- ===========================================
-- 4. 数据库注释和标识
-- ===========================================

COMMENT ON DATABASE saascontrol_dev_pro1 IS 'SaaS Control Deck Development Environment - Pro1 Services (API Gateway, Data Service, AI Service)';
COMMENT ON DATABASE saascontrol_dev_pro2 IS 'SaaS Control Deck Development Environment - Pro2 Services (API Gateway, Data Service, AI Service)';

COMMENT ON DATABASE saascontrol_stage_pro1 IS 'SaaS Control Deck Staging Environment - Pro1 Services - CI/CD Testing';
COMMENT ON DATABASE saascontrol_stage_pro2 IS 'SaaS Control Deck Staging Environment - Pro2 Services - CI/CD Testing';

COMMENT ON DATABASE saascontrol_prod_pro1 IS 'SaaS Control Deck Production Environment - Pro1 Services - Live Production Data';
COMMENT ON DATABASE saascontrol_prod_pro2 IS 'SaaS Control Deck Production Environment - Pro2 Services - Live Production Data';

-- ===========================================
-- 执行完成提示
-- ===========================================

SELECT 
    'SaaS Control Deck数据库创建完成!' as status,
    COUNT(*) as total_databases
FROM pg_database 
WHERE datname LIKE 'saascontrol_%';