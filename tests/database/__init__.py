"""
SaaS Control Deck 数据库测试套件

提供完整的数据库验证测试，包括：
- 连接测试
- 权限验证
- Schema完整性检查
- CRUD操作测试
- 性能测试
- 集成测试
"""

__version__ = "1.0.0"
__author__ = "SaaS Control Deck Team"

# 测试环境配置
TEST_ENVIRONMENTS = {
    "dev_pro1": {
        "db_name": "saascontrol_dev_pro1",
        "user": "saasctl_dev_pro1_user",
        "password": "dev_pro1_secure_2025!",
        "host": "47.79.87.199",
        "port": 5432,
        "connection_limit": 50
    },
    "dev_pro2": {
        "db_name": "saascontrol_dev_pro2", 
        "user": "saasctl_dev_pro2_user",
        "password": "dev_pro2_secure_2025!",
        "host": "47.79.87.199",
        "port": 5432,
        "connection_limit": 50
    },
    "stage_pro1": {
        "db_name": "saascontrol_stage_pro1",
        "user": "saasctl_stage_pro1_user",
        "password": "stage_pro1_secure_2025!",
        "host": "47.79.87.199",
        "port": 5432,
        "connection_limit": 30
    },
    "stage_pro2": {
        "db_name": "saascontrol_stage_pro2",
        "user": "saasctl_stage_pro2_user", 
        "password": "stage_pro2_secure_2025!",
        "host": "47.79.87.199",
        "port": 5432,
        "connection_limit": 30
    },
    "prod_pro1": {
        "db_name": "saascontrol_prod_pro1",
        "user": "saasctl_prod_pro1_user",
        "password": "prod_pro1_ULTRA_secure_2025#$%",
        "host": "47.79.87.199",
        "port": 5432,
        "connection_limit": 100
    },
    "prod_pro2": {
        "db_name": "saascontrol_prod_pro2",
        "user": "saasctl_prod_pro2_user",
        "password": "prod_pro2_ULTRA_secure_2025#$%", 
        "host": "47.79.87.199",
        "port": 5432,
        "connection_limit": 100
    }
}

# 主要数据库表列表
CORE_TABLES = [
    "users",
    "user_profiles", 
    "user_sessions",
    "projects",
    "project_members",
    "project_settings",
    "ai_models",
    "ai_tasks",
    "ai_results",
    "data_sources",
    "analysis_jobs",
    "analysis_results",
    "file_storage",
    "file_metadata",
    "system_logs",
    "performance_metrics",
    "audit_trails",
    "notifications"
]

# 分区表列表
PARTITIONED_TABLES = [
    "system_logs",
    "performance_metrics", 
    "audit_trails"
]

# 索引列表
EXPECTED_INDEXES = [
    {"table": "users", "columns": ["email"], "unique": True},
    {"table": "users", "columns": ["username"], "unique": True},
    {"table": "projects", "columns": ["slug"], "unique": True},
    {"table": "project_members", "columns": ["project_id", "user_id"], "unique": True},
    {"table": "ai_tasks", "columns": ["project_id"]},
    {"table": "ai_tasks", "columns": ["status"]},
    {"table": "file_storage", "columns": ["file_hash"], "unique": True},
    {"table": "notifications", "columns": ["user_id", "is_read", "created_at"]},
    {"table": "audit_trails", "columns": ["user_id", "created_at"]},
    {"table": "audit_trails", "columns": ["resource_type", "resource_id", "created_at"]},
    {"table": "performance_metrics", "columns": ["service_name", "metric_name", "recorded_at"]}
]

# 外键约束列表
EXPECTED_FOREIGN_KEYS = [
    {"table": "user_profiles", "column": "user_id", "ref_table": "users", "ref_column": "id"},
    {"table": "user_sessions", "column": "user_id", "ref_table": "users", "ref_column": "id"},
    {"table": "projects", "column": "owner_id", "ref_table": "users", "ref_column": "id"},
    {"table": "project_members", "column": "project_id", "ref_table": "projects", "ref_column": "id"},
    {"table": "project_members", "column": "user_id", "ref_table": "users", "ref_column": "id"},
    {"table": "ai_tasks", "column": "project_id", "ref_table": "projects", "ref_column": "id"},
    {"table": "ai_tasks", "column": "user_id", "ref_table": "users", "ref_column": "id"},
    {"table": "ai_results", "column": "task_id", "ref_table": "ai_tasks", "ref_column": "id"},
    {"table": "file_storage", "column": "project_id", "ref_table": "projects", "ref_column": "id"},
    {"table": "file_metadata", "column": "file_id", "ref_table": "file_storage", "ref_column": "id"}
]

# 检查约束列表
EXPECTED_CHECK_CONSTRAINTS = [
    {"table": "users", "constraint": "users_email_format"},
    {"table": "users", "constraint": "users_username_length"},
    {"table": "users", "constraint": "users_failed_attempts_range"},
    {"table": "projects", "constraint": "projects_status_check"},
    {"table": "projects", "constraint": "projects_visibility_check"},
    {"table": "ai_tasks", "constraint": "ai_tasks_status_check"},
    {"table": "ai_tasks", "constraint": "ai_tasks_priority_check"},
    {"table": "file_storage", "constraint": "file_storage_size_check"}
]