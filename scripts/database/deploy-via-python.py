#!/usr/bin/env python3
"""
SaaS Control Deck - Python数据库部署脚本
适用于Firebase Studio Nix环境
"""

import os
import sys
import subprocess
import logging
from typing import Dict, List, Optional
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseDeployer:
    """数据库部署器 - Python版本"""

    def __init__(self):
        self.db_config = {
            'host': '47.79.87.199',
            'port': 5432,
            'admin_user': 'jackchan',
            'admin_password': 'secure_password_123',
            'admin_database': 'postgres'
        }

        self.environments = {
            'dev': {
                'databases': ['saascontrol_dev_pro1', 'saascontrol_dev_pro2'],
                'user': 'saascontrol_dev_user',
                'password': 'dev_pass_2024_secure'
            },
            'stage': {
                'databases': ['saascontrol_stage_pro1', 'saascontrol_stage_pro2'],
                'user': 'saascontrol_stage_user',
                'password': 'stage_pass_2024_secure'
            },
            'prod': {
                'databases': ['saascontrol_prod_pro1', 'saascontrol_prod_pro2'],
                'user': 'saascontrol_prod_user',
                'password': 'prod_pass_2024_very_secure_XyZ9#mK'
            }
        }

    def check_dependencies(self) -> bool:
        """检查系统依赖"""
        logger.info("🔍 检查系统依赖...")

        try:
            import psycopg2
            logger.info("✅ psycopg2 已安装")
            return True
        except ImportError:
            logger.error("❌ 缺少 psycopg2，请安装: pip install psycopg2-binary")
            return False

    def test_connection(self, test_only: bool = False) -> bool:
        """测试数据库连接"""
        logger.info("🔗 测试数据库连接...")

        try:
            import psycopg2

            # 测试管理员连接
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['admin_user'],
                password=self.db_config['admin_password'],
                database=self.db_config['admin_database']
            )

            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                logger.info(f"✅ PostgreSQL连接成功: {version}")

            conn.close()

            if test_only:
                logger.info("🎯 仅测试模式，跳过实际部署")
                return True

            return True

        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False

    def execute_sql_file(self, sql_file_path: str, database: str = None) -> bool:
        """执行SQL文件"""
        try:
            import psycopg2

            database = database or self.db_config['admin_database']

            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['admin_user'],
                password=self.db_config['admin_password'],
                database=database
            )

            conn.autocommit = True

            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            with conn.cursor() as cursor:
                cursor.execute(sql_content)

            conn.close()
            logger.info(f"✅ SQL文件执行成功: {sql_file_path}")
            return True

        except Exception as e:
            logger.error(f"❌ SQL文件执行失败 {sql_file_path}: {e}")
            return False

    def create_databases_and_users(self) -> bool:
        """创建数据库和用户"""
        logger.info("🏗️ 创建数据库和用户...")

        sql_file = "scripts/database/create-saascontrol-databases.sql"
        if os.path.exists(sql_file):
            return self.execute_sql_file(sql_file)
        else:
            logger.error(f"❌ SQL文件不存在: {sql_file}")
            return False

    def create_schema(self) -> bool:
        """创建数据库Schema"""
        logger.info("📋 创建数据库表结构...")

        sql_file = "scripts/database/saascontrol-schema.sql"
        if not os.path.exists(sql_file):
            logger.error(f"❌ Schema文件不存在: {sql_file}")
            return False

        # 为每个数据库创建表结构
        success_count = 0
        total_databases = sum(len(env['databases']) for env in self.environments.values())

        for env_name, env_config in self.environments.items():
            for database in env_config['databases']:
                logger.info(f"📊 为数据库 {database} 创建表结构...")

                if self.execute_sql_file(sql_file, database):
                    success_count += 1
                    logger.info(f"✅ {database} 表结构创建成功")
                else:
                    logger.error(f"❌ {database} 表结构创建失败")

        logger.info(f"📊 Schema创建完成: {success_count}/{total_databases} 成功")
        return success_count == total_databases

    def generate_env_config(self) -> bool:
        """生成环境配置文件"""
        logger.info("⚙️ 生成环境配置文件...")

        try:
            config_content = f"""# SaaS Control Deck - 多环境数据库配置
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# ===========================================
# 开发环境配置 (Firebase Studio)
# ===========================================
DEV_DATABASE_URL="postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1"
DEV_SECONDARY_DATABASE_URL="postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro2"

# ===========================================
# 测试环境配置
# ===========================================
STAGE_DATABASE_URL="postgresql+asyncpg://saascontrol_stage_user:stage_pass_2024_secure@47.79.87.199:5432/saascontrol_stage_pro1"
STAGE_SECONDARY_DATABASE_URL="postgresql+asyncpg://saascontrol_stage_user:stage_pass_2024_secure@47.79.87.199:5432/saascontrol_stage_pro2"

# ===========================================
# 生产环境配置
# ===========================================
PROD_DATABASE_URL="postgresql+asyncpg://saascontrol_prod_user:prod_pass_2024_very_secure_XyZ9#mK@47.79.87.199:5432/saascontrol_prod_pro1"
PROD_SECONDARY_DATABASE_URL="postgresql+asyncpg://saascontrol_prod_user:prod_pass_2024_very_secure_XyZ9#mK@47.79.87.199:5432/saascontrol_prod_prod2"

# ===========================================
# Firebase Studio 默认配置
# ===========================================
DATABASE_URL="postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro1"
SECONDARY_DATABASE_URL="postgresql+asyncpg://saascontrol_dev_user:dev_pass_2024_secure@47.79.87.199:5432/saascontrol_dev_pro2"

# ===========================================
# 连接池配置
# ===========================================
DEV_MIN_POOL_SIZE=2
DEV_MAX_POOL_SIZE=10

STAGE_MIN_POOL_SIZE=3
STAGE_MAX_POOL_SIZE=15

PROD_MIN_POOL_SIZE=5
PROD_MAX_POOL_SIZE=50
"""

            with open('.env.deployed', 'w', encoding='utf-8') as f:
                f.write(config_content)

            logger.info("✅ 环境配置文件已生成: .env.deployed")
            return True

        except Exception as e:
            logger.error(f"❌ 环境配置文件生成失败: {e}")
            return False

    def deploy(self, test_only: bool = False, schema_only: bool = False) -> bool:
        """执行完整部署"""
        logger.info("🚀 开始数据库部署...")
        logger.info("=" * 60)
        logger.info("🎯 SaaS Control Deck - Python数据库部署工具")
        logger.info("🌐 PostgreSQL服务器: 47.79.87.199:5432")
        logger.info("👤 管理员用户: jackchan")
        logger.info("📊 数据库数量: 6个 (dev/stage/prod × pro1/pro2)")
        logger.info("=" * 60)

        # 1. 检查依赖
        if not self.check_dependencies():
            return False

        # 2. 测试连接
        if not self.test_connection(test_only):
            return False

        if test_only:
            return True

        # 3. 创建数据库和用户
        if not schema_only:
            if not self.create_databases_and_users():
                logger.error("❌ 数据库和用户创建失败")
                return False

        # 4. 创建表结构
        if not self.create_schema():
            logger.error("❌ 数据库Schema创建失败")
            return False

        # 5. 生成配置文件
        if not self.generate_env_config():
            logger.error("❌ 环境配置生成失败")
            return False

        logger.info("🎉 数据库部署完成！")
        logger.info("📋 下一步:")
        logger.info("   1. 复制 .env.deployed 到 .env")
        logger.info("   2. 在Firebase Studio中重启开发服务器")
        logger.info("   3. 验证数据库连接: python3 scripts/database/test-db-connectivity.py")

        return True

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='SaaS Control Deck 数据库部署工具 (Python版本)')
    parser.add_argument('--test-only', action='store_true', help='仅测试连接，不执行部署')
    parser.add_argument('--schema-only', action='store_true', help='仅创建表结构，跳过数据库和用户创建')

    args = parser.parse_args()

    deployer = DatabaseDeployer()

    try:
        success = deployer.deploy(
            test_only=args.test_only,
            schema_only=args.schema_only
        )

        if success:
            logger.info("✅ 部署成功完成")
            sys.exit(0)
        else:
            logger.error("❌ 部署失败")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("🛑 部署被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 部署过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()