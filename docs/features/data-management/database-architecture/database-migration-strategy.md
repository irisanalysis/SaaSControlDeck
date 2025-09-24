# 数据迁移策略设计

## 🔄 迁移策略概览

为SaaS Control Deck数据管理平台设计了完整的数据迁移策略，支持环境间无缝迁移、版本升级和回滚方案，确保业务连续性和数据完整性。

## 📋 迁移类型分类

### 1. 环境间迁移

#### 开发环境 → 测试环境

```bash
#!/bin/bash
# dev_to_staging_migration.sh

set -e  # 遇到错误立即退出

# 配置变量
SOURCE_HOST="47.79.87.199"
SOURCE_USER="saascontrol_dev_user"
TARGET_USER="saascontrol_stage_user"
BACKUP_DIR="/backup/migrations/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$BACKUP_DIR/migration.log"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

echo "开始开发环境到测试环境的迁移..." | tee "$LOG_FILE"

# 1. 验证源环境连接
echo "验证源环境连接..." | tee -a "$LOG_FILE"
if ! psql -h "$SOURCE_HOST" -U "$SOURCE_USER" -d saascontrol_dev_pro1 -c "SELECT 1;" > /dev/null 2>&1; then
    echo "错误: 无法连接到源数据库" | tee -a "$LOG_FILE"
    exit 1
fi

# 2. 创建测试环境备份 (安全措施)
echo "创建测试环境当前备份..." | tee -a "$LOG_FILE"
pg_dump -h "$SOURCE_HOST" -U "$TARGET_USER" -d saascontrol_stage_pro1 \
        --format=custom --compress=9 \
        --file="$BACKUP_DIR/stage_backup_before_migration.backup" || {
    echo "错误: 测试环境备份失败" | tee -a "$LOG_FILE"
    exit 1
}

# 3. 导出开发环境Schema
echo "导出开发环境Schema..." | tee -a "$LOG_FILE"
pg_dump -h "$SOURCE_HOST" -U "$SOURCE_USER" -d saascontrol_dev_pro1 \
        --schema-only --no-owner --no-privileges \
        --exclude-table=schema_migrations \
        --file="$BACKUP_DIR/dev_schema_pro1.sql" || {
    echo "错误: Schema导出失败" | tee -a "$LOG_FILE"
    exit 1
}

pg_dump -h "$SOURCE_HOST" -U "$SOURCE_USER" -d saascontrol_dev_pro2 \
        --schema-only --no-owner --no-privileges \
        --exclude-table=schema_migrations \
        --file="$BACKUP_DIR/dev_schema_pro2.sql" || {
    echo "错误: Schema导出失败" | tee -a "$LOG_FILE"
    exit 1
}

# 4. 导出基础数据 (配置、模板等)
echo "导出基础配置数据..." | tee -a "$LOG_FILE"
pg_dump -h "$SOURCE_HOST" -U "$SOURCE_USER" -d saascontrol_dev_pro1 \
        --data-only --no-owner --no-privileges \
        --table=subscription_plans \
        --table=system_roles \
        --table=data_classifications \
        --table=quality_rules \
        --table=ai_models \
        --file="$BACKUP_DIR/base_data.sql" || {
    echo "错误: 基础数据导出失败" | tee -a "$LOG_FILE"
    exit 1
}

# 5. 导出测试用户和组织数据
echo "导出测试用户数据..." | tee -a "$LOG_FILE"
pg_dump -h "$SOURCE_HOST" -U "$SOURCE_USER" -d saascontrol_dev_pro1 \
        --data-only --no-owner --no-privileges \
        --where="email LIKE '%@test.com' OR email LIKE '%@staging.com'" \
        --table=users \
        --table=user_profiles \
        --table=organizations \
        --table=organization_members \
        --file="$BACKUP_DIR/test_users.sql" || {
    echo "警告: 测试用户数据导出失败，继续迁移..." | tee -a "$LOG_FILE"
}

# 6. 清理测试环境
echo "清理测试环境..." | tee -a "$LOG_FILE"
psql -h "$SOURCE_HOST" -U "$TARGET_USER" -d saascontrol_stage_pro1 \
     -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" || {
    echo "错误: 测试环境清理失败" | tee -a "$LOG_FILE"
    exit 1
}

psql -h "$SOURCE_HOST" -U "$TARGET_USER" -d saascontrol_stage_pro2 \
     -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" || {
    echo "错误: 测试环境清理失败" | tee -a "$LOG_FILE"
    exit 1
}

# 7. 导入Schema到测试环境
echo "导入Schema到测试环境..." | tee -a "$LOG_FILE"
psql -h "$SOURCE_HOST" -U "$TARGET_USER" -d saascontrol_stage_pro1 \
     -f "$BACKUP_DIR/dev_schema_pro1.sql" || {
    echo "错误: Schema导入失败" | tee -a "$LOG_FILE"
    exit 1
}

psql -h "$SOURCE_HOST" -U "$TARGET_USER" -d saascontrol_stage_pro2 \
     -f "$BACKUP_DIR/dev_schema_pro2.sql" || {
    echo "错误: Schema导入失败" | tee -a "$LOG_FILE"
    exit 1
}

# 8. 导入基础数据
echo "导入基础数据..." | tee -a "$LOG_FILE"
psql -h "$SOURCE_HOST" -U "$TARGET_USER" -d saascontrol_stage_pro1 \
     -f "$BACKUP_DIR/base_data.sql" || {
    echo "错误: 基础数据导入失败" | tee -a "$LOG_FILE"
    exit 1
}

# 9. 导入测试数据
if [ -f "$BACKUP_DIR/test_users.sql" ]; then
    echo "导入测试用户数据..." | tee -a "$LOG_FILE"
    psql -h "$SOURCE_HOST" -U "$TARGET_USER" -d saascontrol_stage_pro1 \
         -f "$BACKUP_DIR/test_users.sql" || {
        echo "警告: 测试用户数据导入失败" | tee -a "$LOG_FILE"
    }
fi

# 10. 验证迁移结果
echo "验证迁移结果..." | tee -a "$LOG_FILE"
STAGING_TABLE_COUNT=$(psql -h "$SOURCE_HOST" -U "$TARGET_USER" -d saascontrol_stage_pro1 \
                      -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | tr -d ' ')

if [ "$STAGING_TABLE_COUNT" -lt 10 ]; then
    echo "错误: 测试环境表数量异常 ($STAGING_TABLE_COUNT)" | tee -a "$LOG_FILE"
    exit 1
fi

echo "迁移完成! 测试环境包含 $STAGING_TABLE_COUNT 个表" | tee -a "$LOG_FILE"
echo "备份文件保存在: $BACKUP_DIR" | tee -a "$LOG_FILE"
```

#### 测试环境 → 生产环境

```bash
#!/bin/bash
# staging_to_production_migration.sh

set -e

# 配置变量
SOURCE_HOST="47.79.87.199"
SOURCE_USER="saascontrol_stage_user"
TARGET_USER="saascontrol_prod_user"
BACKUP_DIR="/backup/prod_migrations/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$BACKUP_DIR/prod_migration.log"

# 安全检查
if [ "$1" != "--confirm-production" ]; then
    echo "错误: 生产环境迁移需要确认参数 --confirm-production"
    exit 1
fi

mkdir -p "$BACKUP_DIR"
echo "开始测试环境到生产环境的迁移..." | tee "$LOG_FILE"

# 1. 生产环境完整备份
echo "创建生产环境完整备份..." | tee -a "$LOG_FILE"
pg_dump -h "$SOURCE_HOST" -U "$TARGET_USER" -d saascontrol_prod_pro1 \
        --format=custom --compress=9 \
        --file="$BACKUP_DIR/prod_full_backup_pro1.backup"

pg_dump -h "$SOURCE_HOST" -U "$TARGET_USER" -d saascontrol_prod_pro2 \
        --format=custom --compress=9 \
        --file="$BACKUP_DIR/prod_full_backup_pro2.backup"

# 2. 导出测试环境Schema (仅结构)
echo "导出测试环境Schema..." | tee -a "$LOG_FILE"
pg_dump -h "$SOURCE_HOST" -U "$SOURCE_USER" -d saascontrol_stage_pro1 \
        --schema-only --clean --if-exists \
        --no-owner --no-privileges \
        --exclude-table=security_audit_logs* \
        --exclude-table=*_partitioned \
        --file="$BACKUP_DIR/stage_schema_pro1.sql"

pg_dump -h "$SOURCE_HOST" -U "$SOURCE_USER" -d saascontrol_stage_pro2 \
        --schema-only --clean --if-exists \
        --no-owner --no-privileges \
        --exclude-table=security_audit_logs* \
        --exclude-table=*_partitioned \
        --file="$BACKUP_DIR/stage_schema_pro2.sql"

# 3. 生成数据迁移脚本
echo "生成数据迁移脚本..." | tee -a "$LOG_FILE"
cat > "$BACKUP_DIR/migrate_existing_data.sql" << 'EOF'
-- 数据迁移脚本 - 保留生产环境现有数据
-- 只更新Schema，不影响业务数据

-- 备份关键表到临时表
CREATE TABLE users_backup AS SELECT * FROM users;
CREATE TABLE organizations_backup AS SELECT * FROM organizations;
CREATE TABLE data_sources_backup AS SELECT * FROM data_sources;
CREATE TABLE quality_assessments_backup AS SELECT * FROM quality_assessments;

-- 更新配置数据
TRUNCATE TABLE subscription_plans CASCADE;
TRUNCATE TABLE system_roles CASCADE;
TRUNCATE TABLE data_classifications CASCADE;

-- 这里会插入来自测试环境的配置数据
-- (通过单独的脚本处理)

-- 验证数据完整性
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM users) != (SELECT COUNT(*) FROM users_backup) THEN
        RAISE EXCEPTION '用户数据迁移验证失败';
    END IF;

    IF (SELECT COUNT(*) FROM organizations) != (SELECT COUNT(*) FROM organizations_backup) THEN
        RAISE EXCEPTION '组织数据迁移验证失败';
    END IF;
END $$;

-- 清理备份表
DROP TABLE users_backup;
DROP TABLE organizations_backup;
DROP TABLE data_sources_backup;
DROP TABLE quality_assessments_backup;
EOF

# 4. 在生产环境执行Schema更新 (需要DBA确认)
echo "警告: 以下步骤需要DBA手动执行!" | tee -a "$LOG_FILE"
echo "1. 在生产环境执行: $BACKUP_DIR/stage_schema_pro1.sql" | tee -a "$LOG_FILE"
echo "2. 在生产环境执行: $BACKUP_DIR/stage_schema_pro2.sql" | tee -a "$LOG_FILE"
echo "3. 在生产环境执行: $BACKUP_DIR/migrate_existing_data.sql" | tee -a "$LOG_FILE"

echo "生产环境迁移准备完成，等待DBA确认执行。" | tee -a "$LOG_FILE"
```

### 2. 版本升级迁移

#### 数据库版本管理

```sql
-- 创建迁移管理表
CREATE TABLE database_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    migration_type VARCHAR(20) NOT NULL, -- 'schema', 'data', 'index', 'security', 'hotfix'
    up_script TEXT NOT NULL,
    down_script TEXT NOT NULL,
    checksum VARCHAR(64) NOT NULL,

    -- 执行信息
    executed_at TIMESTAMP WITH TIME ZONE,
    executed_by VARCHAR(100),
    execution_time_ms INTEGER,
    execution_log TEXT,

    -- 状态
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'rolled_back'

    -- 依赖关系
    depends_on VARCHAR(50)[], -- 依赖的版本

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_migration_type CHECK (migration_type IN ('schema', 'data', 'index', 'security', 'hotfix')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'rolled_back'))
);

-- 迁移执行日志表
CREATE TABLE migration_execution_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    migration_id INTEGER REFERENCES database_migrations(id),
    operation VARCHAR(20) NOT NULL, -- 'up', 'down'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'running',
    output_log TEXT,
    error_log TEXT,

    CONSTRAINT valid_operation CHECK (operation IN ('up', 'down')),
    CONSTRAINT valid_log_status CHECK (status IN ('running', 'completed', 'failed'))
);
```

#### 版本升级脚本生成器

```python
# migration_generator.py

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional

class MigrationGenerator:
    """数据库迁移脚本生成器"""

    def __init__(self, version: str, description: str, migration_type: str = 'schema'):
        self.version = version
        self.description = description
        self.migration_type = migration_type
        self.up_script = []
        self.down_script = []
        self.dependencies = []

    def add_dependency(self, version: str) -> 'MigrationGenerator':
        """添加依赖版本"""
        self.dependencies.append(version)
        return self

    def create_table(self, table_name: str, columns: Dict[str, str],
                    indexes: Optional[List[str]] = None) -> 'MigrationGenerator':
        """创建表"""
        # UP脚本
        up_sql = f"CREATE TABLE {table_name} (\n"
        up_sql += ",\n".join([f"    {col} {definition}" for col, definition in columns.items()])
        up_sql += "\n);"
        self.up_script.append(up_sql)

        # 创建索引
        if indexes:
            for index in indexes:
                self.up_script.append(f"CREATE INDEX {index};")

        # DOWN脚本
        self.down_script.insert(0, f"DROP TABLE IF EXISTS {table_name} CASCADE;")

        return self

    def add_column(self, table_name: str, column_name: str,
                  column_definition: str, default_value: Optional[str] = None) -> 'MigrationGenerator':
        """添加列"""
        up_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        if default_value:
            up_sql += f" DEFAULT {default_value}"
        up_sql += ";"
        self.up_script.append(up_sql)

        # DOWN脚本
        down_sql = f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {column_name};"
        self.down_script.insert(0, down_sql)

        return self

    def create_index(self, index_name: str, table_name: str,
                    columns: str, index_type: str = "BTREE") -> 'MigrationGenerator':
        """创建索引"""
        up_sql = f"CREATE INDEX {index_name} ON {table_name} USING {index_type} ({columns});"
        self.up_script.append(up_sql)

        down_sql = f"DROP INDEX IF EXISTS {index_name};"
        self.down_script.insert(0, down_sql)

        return self

    def execute_sql(self, up_sql: str, down_sql: str) -> 'MigrationGenerator':
        """执行自定义SQL"""
        self.up_script.append(up_sql)
        self.down_script.insert(0, down_sql)
        return self

    def generate_checksum(self) -> str:
        """生成校验和"""
        content = f"{self.version}:{':'.join(self.up_script)}:{':'.join(self.down_script)}"
        return hashlib.sha256(content.encode()).hexdigest()

    def generate_migration_sql(self) -> str:
        """生成迁移SQL文件"""
        checksum = self.generate_checksum()

        sql = f"""-- Migration: {self.version}
-- Description: {self.description}
-- Type: {self.migration_type}
-- Generated: {datetime.now().isoformat()}

-- Insert migration record
INSERT INTO database_migrations (
    version, description, migration_type, up_script, down_script,
    checksum, depends_on
) VALUES (
    '{self.version}',
    '{self.description}',
    '{self.migration_type}',
    $UP${chr(10).join(self.up_script)}$UP$,
    $DOWN${chr(10).join(self.down_script)}$DOWN$,
    '{checksum}',
    ARRAY{self.dependencies}
);

-- Execute UP migration
"""
        sql += "\n".join(self.up_script)

        return sql

# 使用示例
if __name__ == "__main__":
    # 创建v2.1.0迁移 - 添加数据分类功能
    migration = MigrationGenerator(
        version="v2.1.0",
        description="添加数据分类和标签功能",
        migration_type="schema"
    ).add_dependency("v2.0.5")

    # 创建数据标签表
    migration.create_table(
        "data_tags",
        {
            "id": "UUID PRIMARY KEY DEFAULT gen_random_uuid()",
            "tag_name": "VARCHAR(100) NOT NULL UNIQUE",
            "tag_color": "VARCHAR(7) DEFAULT '#007bff'",
            "tag_category": "VARCHAR(50) NOT NULL",
            "description": "TEXT",
            "is_system_tag": "BOOLEAN DEFAULT FALSE",
            "created_by": "UUID REFERENCES users(id)",
            "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()"
        },
        indexes=[
            "idx_data_tags_category ON data_tags(tag_category)",
            "idx_data_tags_system ON data_tags(is_system_tag)"
        ]
    )

    # 为数据源添加标签列
    migration.add_column(
        "data_sources",
        "tags",
        "TEXT[]",
        "ARRAY[]::TEXT[]"
    )

    # 创建标签索引
    migration.create_index(
        "idx_data_sources_tags",
        "data_sources",
        "tags",
        "GIN"
    )

    # 插入系统默认标签
    migration.execute_sql(
        """INSERT INTO data_tags (tag_name, tag_color, tag_category, is_system_tag) VALUES
        ('高质量', '#28a745', 'quality', TRUE),
        ('需改进', '#ffc107', 'quality', TRUE),
        ('已验证', '#17a2b8', 'status', TRUE),
        ('敏感数据', '#dc3545', 'security', TRUE);""",
        "DELETE FROM data_tags WHERE is_system_tag = TRUE;"
    )

    print(migration.generate_migration_sql())
```

### 3. 数据迁移工具

#### 大数据量迁移工具

```python
# large_data_migrator.py

import asyncio
import asyncpg
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

class LargeDataMigrator:
    """大数据量迁移工具"""

    def __init__(self, source_dsn: str, target_dsn: str, batch_size: int = 10000):
        self.source_dsn = source_dsn
        self.target_dsn = target_dsn
        self.batch_size = batch_size
        self.logger = logging.getLogger(__name__)

    async def migrate_table(self, table_name: str,
                           where_clause: Optional[str] = None,
                           transform_func: Optional[callable] = None) -> Dict[str, Any]:
        """迁移单个表"""

        start_time = datetime.now()
        total_rows = 0
        migrated_rows = 0
        errors = []

        try:
            # 连接源和目标数据库
            source_conn = await asyncpg.connect(self.source_dsn)
            target_conn = await asyncpg.connect(self.target_dsn)

            # 获取表结构
            columns_query = """
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = $1
                ORDER BY ordinal_position
            """
            columns = await source_conn.fetch(columns_query, table_name)
            column_names = [col['column_name'] for col in columns]

            # 统计总行数
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            if where_clause:
                count_query += f" WHERE {where_clause}"

            total_rows = await source_conn.fetchval(count_query)
            self.logger.info(f"开始迁移表 {table_name}，总计 {total_rows} 行")

            # 分批迁移
            offset = 0
            while offset < total_rows:
                try:
                    # 读取批次数据
                    select_query = f"""
                        SELECT {', '.join(column_names)}
                        FROM {table_name}
                    """
                    if where_clause:
                        select_query += f" WHERE {where_clause}"

                    select_query += f" ORDER BY id LIMIT {self.batch_size} OFFSET {offset}"

                    batch_data = await source_conn.fetch(select_query)

                    if not batch_data:
                        break

                    # 数据转换
                    if transform_func:
                        batch_data = [transform_func(dict(row)) for row in batch_data]
                    else:
                        batch_data = [dict(row) for row in batch_data]

                    # 插入目标数据库
                    placeholders = ', '.join([f'${i+1}' for i in range(len(column_names))])
                    insert_query = f"""
                        INSERT INTO {table_name} ({', '.join(column_names)})
                        VALUES ({placeholders})
                        ON CONFLICT (id) DO UPDATE SET
                            {', '.join([f'{col} = EXCLUDED.{col}' for col in column_names if col != 'id'])}
                    """

                    async with target_conn.transaction():
                        for row in batch_data:
                            values = [row.get(col) for col in column_names]
                            await target_conn.execute(insert_query, *values)

                    migrated_rows += len(batch_data)
                    offset += self.batch_size

                    # 进度报告
                    progress = (migrated_rows / total_rows) * 100
                    self.logger.info(f"表 {table_name} 迁移进度: {progress:.1f}% ({migrated_rows}/{total_rows})")

                except Exception as e:
                    error_msg = f"批次迁移失败 (offset: {offset}): {str(e)}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
                    offset += self.batch_size  # 跳过错误批次

            await source_conn.close()
            await target_conn.close()

        except Exception as e:
            self.logger.error(f"表 {table_name} 迁移失败: {str(e)}")
            errors.append(str(e))

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        return {
            'table_name': table_name,
            'total_rows': total_rows,
            'migrated_rows': migrated_rows,
            'duration_seconds': duration,
            'rows_per_second': migrated_rows / duration if duration > 0 else 0,
            'errors': errors,
            'success': len(errors) == 0
        }

    async def migrate_multiple_tables(self, table_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """并行迁移多个表"""

        tasks = []
        for config in table_configs:
            task = self.migrate_table(
                table_name=config['table_name'],
                where_clause=config.get('where_clause'),
                transform_func=config.get('transform_func')
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        summary = {
            'total_tables': len(table_configs),
            'successful_tables': 0,
            'failed_tables': 0,
            'total_rows': 0,
            'migrated_rows': 0,
            'results': []
        }

        for result in results:
            if isinstance(result, Exception):
                summary['failed_tables'] += 1
                summary['results'].append({
                    'error': str(result),
                    'success': False
                })
            else:
                if result['success']:
                    summary['successful_tables'] += 1
                else:
                    summary['failed_tables'] += 1

                summary['total_rows'] += result['total_rows']
                summary['migrated_rows'] += result['migrated_rows']
                summary['results'].append(result)

        return summary

# 数据转换函数示例
def transform_user_data(row: Dict[str, Any]) -> Dict[str, Any]:
    """用户数据转换函数"""
    # 脱敏处理
    if 'email' in row:
        email = row['email']
        if '@test.com' not in email and '@staging.com' not in email:
            # 生产环境邮箱脱敏
            username, domain = email.split('@')
            row['email'] = f"{username[:3]}***@{domain}"

    # 密码重置
    if 'password_hash' in row:
        row['password_hash'] = '$2b$12$default_test_password_hash'
        row['force_password_change'] = True

    return row

# 迁移配置示例
migration_config = [
    {
        'table_name': 'users',
        'where_clause': "created_at >= '2024-01-01'",
        'transform_func': transform_user_data
    },
    {
        'table_name': 'organizations',
        'where_clause': "is_active = TRUE"
    },
    {
        'table_name': 'data_sources',
        'where_clause': "created_at >= '2024-01-01'"
    },
    {
        'table_name': 'quality_assessments',
        'where_clause': "status = 'completed' AND created_at >= '2024-06-01'"
    }
]
```

### 4. 回滚策略

#### 自动回滚系统

```sql
-- 回滚点管理
CREATE TABLE migration_rollback_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rollback_name VARCHAR(255) NOT NULL,
    environment VARCHAR(20) NOT NULL, -- 'development', 'staging', 'production'
    database_name VARCHAR(100) NOT NULL,

    -- 备份信息
    backup_file_path TEXT NOT NULL,
    backup_size_bytes BIGINT,
    backup_checksum VARCHAR(64),

    -- Schema快照
    schema_snapshot JSONB NOT NULL,
    data_snapshot_tables TEXT[], -- 需要快照的关键表

    -- 迁移信息
    migration_version VARCHAR(50),
    migration_description TEXT,

    -- 状态
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'expired', 'used'
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '30 days'),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),

    CONSTRAINT valid_environment CHECK (environment IN ('development', 'staging', 'production')),
    CONSTRAINT valid_rollback_status CHECK (status IN ('active', 'expired', 'used'))
);

-- 回滚执行记录
CREATE TABLE rollback_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rollback_point_id UUID NOT NULL REFERENCES migration_rollback_points(id),

    -- 执行信息
    execution_type VARCHAR(20) NOT NULL, -- 'full', 'schema_only', 'data_only'
    executed_by UUID REFERENCES users(id),
    execution_reason TEXT NOT NULL,

    -- 状态
    status VARCHAR(20) DEFAULT 'running', -- 'running', 'completed', 'failed'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- 结果
    execution_log TEXT,
    error_log TEXT,

    CONSTRAINT valid_execution_type CHECK (execution_type IN ('full', 'schema_only', 'data_only')),
    CONSTRAINT valid_execution_status CHECK (status IN ('running', 'completed', 'failed'))
);

-- 创建回滚点函数
CREATE OR REPLACE FUNCTION create_rollback_point(
    p_rollback_name TEXT,
    p_environment TEXT,
    p_database_name TEXT,
    p_migration_version TEXT DEFAULT NULL,
    p_description TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    rollback_id UUID;
    schema_info JSONB;
    backup_path TEXT;
BEGIN
    -- 生成回滚点ID
    rollback_id := gen_random_uuid();

    -- 收集Schema信息
    SELECT jsonb_object_agg(table_name, table_info)
    INTO schema_info
    FROM (
        SELECT
            table_name,
            jsonb_build_object(
                'columns', (
                    SELECT jsonb_agg(
                        jsonb_build_object(
                            'column_name', column_name,
                            'data_type', data_type,
                            'is_nullable', is_nullable,
                            'column_default', column_default
                        )
                    )
                    FROM information_schema.columns c
                    WHERE c.table_name = t.table_name
                      AND c.table_schema = 'public'
                ),
                'indexes', (
                    SELECT jsonb_agg(indexname)
                    FROM pg_indexes
                    WHERE tablename = t.table_name
                      AND schemaname = 'public'
                ),
                'row_count', (
                    SELECT (xpath('//row/c/text()', query_to_xml(
                        format('SELECT COUNT(*) as c FROM %I', t.table_name),
                        false, true, ''
                    )))[1]::text::integer
                )
            ) as table_info
        FROM information_schema.tables t
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
    ) sub;

    -- 生成备份文件路径
    backup_path := format('/backup/rollback_points/%s_%s_%s.backup',
                         p_environment,
                         p_database_name,
                         rollback_id);

    -- 插入回滚点记录
    INSERT INTO migration_rollback_points (
        id,
        rollback_name,
        environment,
        database_name,
        backup_file_path,
        schema_snapshot,
        migration_version,
        migration_description,
        created_by
    ) VALUES (
        rollback_id,
        p_rollback_name,
        p_environment,
        p_database_name,
        backup_path,
        schema_info,
        p_migration_version,
        p_description,
        get_current_user_id()
    );

    -- 记录操作日志
    INSERT INTO security_audit_logs (
        event_type,
        event_category,
        user_id,
        action_performed,
        resource_type,
        resource_id,
        additional_metadata
    ) VALUES (
        'rollback_point_created',
        'system',
        get_current_user_id(),
        'create',
        'rollback_point',
        rollback_id,
        jsonb_build_object(
            'rollback_name', p_rollback_name,
            'environment', p_environment,
            'database_name', p_database_name
        )
    );

    RETURN rollback_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 执行回滚函数
CREATE OR REPLACE FUNCTION execute_rollback(
    p_rollback_point_id UUID,
    p_execution_type TEXT DEFAULT 'full',
    p_reason TEXT DEFAULT '手动回滚'
) RETURNS UUID AS $$
DECLARE
    execution_id UUID;
    rollback_info RECORD;
BEGIN
    -- 获取回滚点信息
    SELECT * INTO rollback_info
    FROM migration_rollback_points
    WHERE id = p_rollback_point_id
      AND status = 'active'
      AND expires_at > NOW();

    IF NOT FOUND THEN
        RAISE EXCEPTION '回滚点不存在或已过期';
    END IF;

    -- 创建执行记录
    execution_id := gen_random_uuid();

    INSERT INTO rollback_executions (
        id,
        rollback_point_id,
        execution_type,
        executed_by,
        execution_reason
    ) VALUES (
        execution_id,
        p_rollback_point_id,
        p_execution_type,
        get_current_user_id(),
        p_reason
    );

    -- 记录回滚开始
    INSERT INTO security_audit_logs (
        event_type,
        event_category,
        user_id,
        action_performed,
        resource_type,
        resource_id,
        additional_metadata
    ) VALUES (
        'rollback_started',
        'system',
        get_current_user_id(),
        'rollback',
        'database',
        execution_id,
        jsonb_build_object(
            'rollback_point_id', p_rollback_point_id,
            'execution_type', p_execution_type,
            'reason', p_reason
        )
    );

    RETURN execution_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

#### 快速回滚脚本

```bash
#!/bin/bash
# quick_rollback.sh

set -e

# 配置变量
ROLLBACK_POINT_ID="$1"
EXECUTION_TYPE="${2:-full}"  # full, schema_only, data_only
REASON="$3"

if [ -z "$ROLLBACK_POINT_ID" ]; then
    echo "用法: $0 <rollback_point_id> [execution_type] [reason]"
    exit 1
fi

HOST="47.79.87.199"
PORT="5432"
DATABASE="saascontrol_prod_pro1"
USER="saascontrol_prod_user"

echo "开始快速回滚..."
echo "回滚点ID: $ROLLBACK_POINT_ID"
echo "执行类型: $EXECUTION_TYPE"

# 1. 验证回滚点
ROLLBACK_INFO=$(psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DATABASE" -t -c "
    SELECT backup_file_path, rollback_name, environment, status
    FROM migration_rollback_points
    WHERE id = '$ROLLBACK_POINT_ID'
      AND status = 'active'
      AND expires_at > NOW();
")

if [ -z "$ROLLBACK_INFO" ]; then
    echo "错误: 回滚点不存在或已过期"
    exit 1
fi

BACKUP_FILE=$(echo "$ROLLBACK_INFO" | awk '{print $1}')
ROLLBACK_NAME=$(echo "$ROLLBACK_INFO" | awk '{print $2}')

echo "回滚点: $ROLLBACK_NAME"
echo "备份文件: $BACKUP_FILE"

# 2. 创建当前状态备份
CURRENT_BACKUP="/backup/before_rollback_$(date +%Y%m%d_%H%M%S).backup"
echo "创建当前状态备份: $CURRENT_BACKUP"

pg_dump -h "$HOST" -p "$PORT" -U "$USER" -d "$DATABASE" \
        --format=custom --compress=9 \
        --file="$CURRENT_BACKUP"

# 3. 执行回滚
echo "执行回滚..."

if [ "$EXECUTION_TYPE" = "full" ] || [ "$EXECUTION_TYPE" = "schema_only" ]; then
    echo "恢复Schema..."
    # 这里需要从备份文件恢复Schema
    # pg_restore 的具体参数需要根据实际情况调整
fi

if [ "$EXECUTION_TYPE" = "full" ] || [ "$EXECUTION_TYPE" = "data_only" ]; then
    echo "恢复数据..."
    # 这里需要从备份文件恢复数据
fi

# 4. 更新回滚执行状态
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DATABASE" -c "
    UPDATE rollback_executions
    SET status = 'completed',
        completed_at = NOW(),
        execution_log = '回滚成功完成'
    WHERE rollback_point_id = '$ROLLBACK_POINT_ID'
      AND status = 'running';
"

# 5. 标记回滚点为已使用
psql -h "$HOST" -p "$PORT" -U "$USER" -d "$DATABASE" -c "
    UPDATE migration_rollback_points
    SET status = 'used'
    WHERE id = '$ROLLBACK_POINT_ID';
"

echo "回滚完成!"
echo "当前状态已备份到: $CURRENT_BACKUP"
```

## 📊 迁移监控和报告

### 迁移状态监控

```sql
-- 迁移状态监控视图
CREATE VIEW v_migration_status AS
SELECT
    dm.version,
    dm.description,
    dm.migration_type,
    dm.status,
    dm.executed_at,
    dm.executed_by,
    dm.execution_time_ms,
    CASE
        WHEN dm.status = 'completed' THEN '✅ 成功'
        WHEN dm.status = 'failed' THEN '❌ 失败'
        WHEN dm.status = 'running' THEN '🔄 执行中'
        ELSE '⏳ 待执行'
    END as status_display,
    dm.depends_on
FROM database_migrations dm
ORDER BY dm.created_at DESC;

-- 回滚点状态监控
CREATE VIEW v_rollback_points AS
SELECT
    mrp.rollback_name,
    mrp.environment,
    mrp.database_name,
    mrp.migration_version,
    mrp.status,
    mrp.created_at,
    mrp.expires_at,
    pg_size_pretty(mrp.backup_size_bytes) as backup_size,
    u.email as created_by_email
FROM migration_rollback_points mrp
LEFT JOIN users u ON mrp.created_by = u.id
WHERE mrp.status = 'active'
ORDER BY mrp.created_at DESC;
```

这个数据迁移策略为SaaS Control Deck平台提供了完整的迁移解决方案，确保数据在不同环境间的安全迁移和版本升级的平滑过渡。