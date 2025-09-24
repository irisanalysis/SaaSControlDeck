# Environment Data Synchronization Workflows
# SaaS Control Deck - Multi-Environment Data Management

## Overview

This document defines comprehensive data synchronization workflows for the SaaS Control Deck platform, enabling secure and efficient data flow between Development, Staging, and Production environments while maintaining data privacy, consistency, and regulatory compliance.

## Environment Architecture

### Data Flow Strategy
```
Production (Source of Truth)
    ↓ (Sanitized Sync)
Staging (Production-like Testing)
    ↓ (Development Sync)
Development (Feature Development)
```

### Database Infrastructure
- **Production**: `saascontrol_prod_pro1`, `saascontrol_prod_pro2` (47.79.87.199:5432)
- **Staging**: `saascontrol_stage_pro1`, `saascontrol_stage_pro2` (47.79.87.199:5432)
- **Development**: `saascontrol_dev_pro1`, `saascontrol_dev_pro2` (47.79.87.199:5432)

## 1. Data Sanitization and Anonymization

### Production to Staging Data Sync

```yaml
# .github/workflows/environment-data-sync.yml
name: Environment Data Synchronization

on:
  schedule:
    # Daily sync from production to staging (2 AM UTC)
    - cron: '0 2 * * *'
  workflow_dispatch:
    inputs:
      source_environment:
        description: 'Source environment'
        required: true
        default: 'production'
        type: choice
        options:
        - production
        - staging

      target_environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options:
        - staging
        - development

      sync_type:
        description: 'Synchronization type'
        required: true
        default: 'incremental'
        type: choice
        options:
        - full
        - incremental
        - schema-only

jobs:
  validate-sync-request:
    runs-on: ubuntu-latest
    outputs:
      sync-allowed: ${{ steps.validate.outputs.allowed }}

    steps:
    - name: Validate sync request
      id: validate
      run: |
        # Validate sync direction (prevent production contamination)
        SOURCE="${{ github.event.inputs.source_environment }}"
        TARGET="${{ github.event.inputs.target_environment }}"

        if [[ "$TARGET" == "production" ]]; then
          echo "❌ Cannot sync TO production environment"
          echo "allowed=false" >> $GITHUB_OUTPUT
          exit 1
        fi

        if [[ "$SOURCE" == "development" && "$TARGET" == "staging" ]]; then
          echo "❌ Cannot sync from development to staging (wrong direction)"
          echo "allowed=false" >> $GITHUB_OUTPUT
          exit 1
        fi

        echo "✅ Sync direction validated: $SOURCE → $TARGET"
        echo "allowed=true" >> $GITHUB_OUTPUT

  production-to-staging-sync:
    needs: validate-sync-request
    if: needs.validate-sync-request.outputs.sync-allowed == 'true'
    runs-on: ubuntu-latest
    environment: staging

    strategy:
      matrix:
        service: [pro1, pro2]

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Setup Python Environment
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install data sync dependencies
      run: |
        pip install asyncpg psycopg2-binary faker cryptography

    - name: Create pre-sync backup
      env:
        TARGET_DATABASE_URL: ${{ secrets[format('STAGING_{0}_DATABASE_URL', upper(matrix.service))] }}
      run: |
        python scripts/create-pre-sync-backup.py \
          --service ${{ matrix.service }} \
          --environment staging \
          --backup-type pre-sync

    - name: Execute sanitized data sync
      env:
        SOURCE_DATABASE_URL: ${{ secrets[format('PROD_{0}_DATABASE_URL', upper(matrix.service))] }}
        TARGET_DATABASE_URL: ${{ secrets[format('STAGING_{0}_DATABASE_URL', upper(matrix.service))] }}
        ENCRYPTION_KEY: ${{ secrets.DATA_ENCRYPTION_KEY }}
      run: |
        python scripts/sanitized-data-sync.py \
          --source-db $SOURCE_DATABASE_URL \
          --target-db $TARGET_DATABASE_URL \
          --service ${{ matrix.service }} \
          --sync-type ${{ github.event.inputs.sync_type || 'incremental' }} \
          --sanitization-level high

    - name: Validate sync integrity
      env:
        TARGET_DATABASE_URL: ${{ secrets[format('STAGING_{0}_DATABASE_URL', upper(matrix.service))] }}
      run: |
        python scripts/validate-sync-integrity.py \
          --database-url $TARGET_DATABASE_URL \
          --service ${{ matrix.service }} \
          --environment staging

    - name: Update sync metadata
      env:
        TARGET_DATABASE_URL: ${{ secrets[format('STAGING_{0}_DATABASE_URL', upper(matrix.service))] }}
      run: |
        python scripts/update-sync-metadata.py \
          --database-url $TARGET_DATABASE_URL \
          --sync-timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ) \
          --source-environment production \
          --target-environment staging
```

### Advanced Data Sanitization Engine

```python
# scripts/sanitized-data-sync.py
import asyncio
import asyncpg
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib
import secrets
from faker import Faker
from cryptography.fernet import Fernet
import logging

class DataSanitizationEngine:
    def __init__(self, source_db_url: str, target_db_url: str, encryption_key: str):
        self.source_db_url = source_db_url
        self.target_db_url = target_db_url
        self.encryption_key = encryption_key
        self.faker = Faker()
        self.logger = logging.getLogger(__name__)

        # Initialize encryption
        self.cipher = Fernet(encryption_key.encode())

    async def execute_sanitized_sync(self, service: str, sync_type: str, sanitization_level: str) -> Dict[str, Any]:
        """Execute sanitized data synchronization"""
        start_time = datetime.utcnow()

        try:
            # Connect to both databases
            source_conn = await asyncpg.connect(self.source_db_url)
            target_conn = await asyncpg.connect(self.target_db_url)

            # Get sanitization rules
            sanitization_rules = await self.get_sanitization_rules(service, sanitization_level)

            # Execute sync based on type
            if sync_type == "full":
                result = await self.execute_full_sync(source_conn, target_conn, sanitization_rules)
            elif sync_type == "incremental":
                result = await self.execute_incremental_sync(source_conn, target_conn, sanitization_rules)
            else:  # schema-only
                result = await self.execute_schema_sync(source_conn, target_conn)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            await source_conn.close()
            await target_conn.close()

            return {
                "status": "success",
                "service": service,
                "sync_type": sync_type,
                "sanitization_level": sanitization_level,
                "duration_seconds": duration,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                **result
            }

        except Exception as e:
            self.logger.error(f"Sanitized sync failed: {e}")
            raise

    async def get_sanitization_rules(self, service: str, level: str) -> Dict[str, Any]:
        """Get sanitization rules based on service and level"""
        base_rules = {
            "users": {
                "email": "fake_email",
                "first_name": "fake_first_name",
                "last_name": "fake_last_name",
                "phone": "fake_phone",
                "address": "fake_address",
                "ssn": "null",
                "credit_card": "null"
            },
            "organizations": {
                "name": "fake_company",
                "tax_id": "fake_tax_id",
                "contact_email": "fake_email",
                "billing_address": "fake_address"
            },
            "ai_tasks": {
                "input_data": "sanitize_json",
                "output_data": "sanitize_json",
                "metadata": "sanitize_json"
            },
            "data_sources": {
                "connection_string": "encrypt",
                "api_key": "null",
                "credentials": "null"
            },
            "audit_logs": {
                "ip_address": "anonymize_ip",
                "user_agent": "generalize",
                "session_data": "null"
            }
        }

        if level == "high":
            # High sanitization: more aggressive anonymization
            base_rules["users"].update({
                "username": "fake_username",
                "avatar_url": "null",
                "last_login_ip": "anonymize_ip"
            })
            base_rules["ai_tasks"].update({
                "error_details": "null",
                "debug_info": "null"
            })

        return base_rules

    async def execute_full_sync(self, source_conn, target_conn, sanitization_rules: Dict) -> Dict[str, Any]:
        """Execute full database synchronization with sanitization"""
        tables_synced = []
        records_processed = 0

        # Get all tables to sync
        tables = await source_conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        for table_row in tables:
            table_name = table_row['table_name']

            # Skip system tables
            if table_name.startswith('alembic_'):
                continue

            self.logger.info(f"Syncing table: {table_name}")

            # Truncate target table
            await target_conn.execute(f"TRUNCATE TABLE {table_name} CASCADE")

            # Get table data from source
            source_data = await source_conn.fetch(f"SELECT * FROM {table_name}")

            if source_data:
                # Apply sanitization
                sanitized_data = await self.sanitize_table_data(
                    table_name, source_data, sanitization_rules.get(table_name, {})
                )

                # Insert sanitized data into target
                await self.bulk_insert_sanitized_data(target_conn, table_name, sanitized_data)

                records_processed += len(sanitized_data)

            tables_synced.append(table_name)

        return {
            "tables_synced": tables_synced,
            "records_processed": records_processed
        }

    async def sanitize_table_data(self, table_name: str, data: List[Dict], rules: Dict[str, str]) -> List[Dict]:
        """Sanitize table data according to rules"""
        sanitized_data = []

        for row in data:
            sanitized_row = dict(row)

            for column, rule in rules.items():
                if column in sanitized_row:
                    original_value = sanitized_row[column]
                    sanitized_row[column] = await self.apply_sanitization_rule(
                        rule, original_value, column
                    )

            sanitized_data.append(sanitized_row)

        return sanitized_data

    async def apply_sanitization_rule(self, rule: str, value: Any, column: str) -> Any:
        """Apply specific sanitization rule to a value"""
        if value is None:
            return None

        if rule == "fake_email":
            return self.faker.email()
        elif rule == "fake_first_name":
            return self.faker.first_name()
        elif rule == "fake_last_name":
            return self.faker.last_name()
        elif rule == "fake_username":
            return self.faker.user_name()
        elif rule == "fake_phone":
            return self.faker.phone_number()
        elif rule == "fake_address":
            return self.faker.address()
        elif rule == "fake_company":
            return self.faker.company()
        elif rule == "fake_tax_id":
            return self.faker.ssn()
        elif rule == "null":
            return None
        elif rule == "encrypt":
            return self.cipher.encrypt(str(value).encode()).decode()
        elif rule == "anonymize_ip":
            return self.anonymize_ip_address(str(value))
        elif rule == "sanitize_json":
            return await self.sanitize_json_data(value)
        elif rule == "generalize":
            return "SANITIZED_DATA"
        else:
            return value

    async def sanitize_json_data(self, json_data: Any) -> Any:
        """Sanitize JSON data by removing sensitive fields"""
        if isinstance(json_data, dict):
            sanitized = {}
            for key, value in json_data.items():
                # Remove sensitive keys
                if any(sensitive in key.lower() for sensitive in ['password', 'token', 'key', 'secret', 'credential']):
                    sanitized[key] = "[REDACTED]"
                elif any(pii in key.lower() for pii in ['email', 'phone', 'address', 'ssn', 'credit']):
                    sanitized[key] = "[PII_REMOVED]"
                else:
                    sanitized[key] = await self.sanitize_json_data(value)
            return sanitized
        elif isinstance(json_data, list):
            return [await self.sanitize_json_data(item) for item in json_data]
        else:
            return json_data

    def anonymize_ip_address(self, ip: str) -> str:
        """Anonymize IP address by zeroing last octet"""
        try:
            if '.' in ip:  # IPv4
                parts = ip.split('.')
                if len(parts) == 4:
                    return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
            elif ':' in ip:  # IPv6
                parts = ip.split(':')
                if len(parts) >= 4:
                    return ':'.join(parts[:4]) + '::0'
        except:
            pass
        return "0.0.0.0"

    async def execute_incremental_sync(self, source_conn, target_conn, sanitization_rules: Dict) -> Dict[str, Any]:
        """Execute incremental synchronization based on timestamps"""
        # Get last sync timestamp
        last_sync = await target_conn.fetchval("""
            SELECT last_sync_timestamp
            FROM sync_metadata
            WHERE source_environment = 'production'
            ORDER BY sync_timestamp DESC
            LIMIT 1
        """)

        if not last_sync:
            # First sync - fall back to full sync
            return await self.execute_full_sync(source_conn, target_conn, sanitization_rules)

        tables_synced = []
        records_processed = 0

        # Sync tables with updated_at columns
        timestamped_tables = ['users', 'organizations', 'projects', 'ai_tasks', 'data_sources']

        for table_name in timestamped_tables:
            # Get incremental data
            query = f"""
                SELECT * FROM {table_name}
                WHERE updated_at > $1
                ORDER BY updated_at
            """

            source_data = await source_conn.fetch(query, last_sync)

            if source_data:
                # Apply sanitization
                sanitized_data = await self.sanitize_table_data(
                    table_name, source_data, sanitization_rules.get(table_name, {})
                )

                # Upsert sanitized data
                await self.upsert_sanitized_data(target_conn, table_name, sanitized_data)

                records_processed += len(sanitized_data)
                tables_synced.append(table_name)

        return {
            "tables_synced": tables_synced,
            "records_processed": records_processed,
            "last_sync_timestamp": last_sync.isoformat()
        }

if __name__ == "__main__":
    source_db_url = os.getenv("SOURCE_DATABASE_URL")
    target_db_url = os.getenv("TARGET_DATABASE_URL")
    encryption_key = os.getenv("ENCRYPTION_KEY")
    service = os.getenv("SERVICE", "pro1")
    sync_type = os.getenv("SYNC_TYPE", "incremental")
    sanitization_level = os.getenv("SANITIZATION_LEVEL", "high")

    engine = DataSanitizationEngine(source_db_url, target_db_url, encryption_key)
    result = asyncio.run(engine.execute_sanitized_sync(service, sync_type, sanitization_level))

    print(f"✅ Sanitized sync completed for {service}")
    print(f"✅ Sync type: {result['sync_type']}")
    print(f"✅ Records processed: {result['records_processed']}")
    print(f"✅ Duration: {result['duration_seconds']:.2f} seconds")
```

## 2. Configuration Management and Version Control

### Environment Configuration Synchronization

```yaml
# .github/workflows/config-sync.yml
name: Configuration Synchronization

on:
  push:
    branches: [main]
    paths:
      - 'config/environments/**'
      - 'scripts/postgres/environment-configs.yaml'

  workflow_dispatch:
    inputs:
      config_type:
        description: 'Configuration type to sync'
        required: true
        default: 'database'
        type: choice
        options:
        - database
        - application
        - security
        - monitoring

jobs:
  sync-database-config:
    if: github.event.inputs.config_type == 'database' || contains(github.event.head_commit.modified, 'environment-configs.yaml')
    runs-on: ubuntu-latest

    strategy:
      matrix:
        environment: [development, staging, production]
        service: [pro1, pro2]

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Generate environment-specific PostgreSQL config
      run: |
        python scripts/generate-postgres-config.py \
          --environment ${{ matrix.environment }} \
          --service ${{ matrix.service }} \
          --config-file scripts/postgres/environment-configs.yaml \
          --output-dir config/postgres/

    - name: Validate configuration syntax
      run: |
        python scripts/validate-postgres-config.py \
          --config-file config/postgres/${{ matrix.environment }}-${{ matrix.service }}.conf

    - name: Apply configuration to database
      env:
        DATABASE_URL: ${{ secrets[format('{0}_{1}_DATABASE_URL', upper(matrix.environment), upper(matrix.service))] }}
      run: |
        python scripts/apply-postgres-config.py \
          --database-url $DATABASE_URL \
          --config-file config/postgres/${{ matrix.environment }}-${{ matrix.service }}.conf \
          --environment ${{ matrix.environment }}

    - name: Validate configuration changes
      env:
        DATABASE_URL: ${{ secrets[format('{0}_{1}_DATABASE_URL', upper(matrix.environment), upper(matrix.service))] }}
      run: |
        python scripts/validate-config-applied.py \
          --database-url $DATABASE_URL \
          --expected-config config/postgres/${{ matrix.environment }}-${{ matrix.service }}.conf
```

### Dynamic Configuration Generator

```python
# scripts/generate-postgres-config.py
import yaml
import os
import argparse
from typing import Dict, Any
import logging

class PostgreSQLConfigGenerator:
    def __init__(self, config_file: str):
        with open(config_file, 'r') as f:
            self.config_data = yaml.safe_load(f)

    def generate_config(self, environment: str, service: str) -> str:
        """Generate PostgreSQL configuration for specific environment and service"""

        # Get base environment config
        env_config = self.config_data.get(environment, {})

        # Get AI workload optimizations
        ai_optimizations = self.config_data.get('ai_workload_optimizations', {})

        # Get connection pool settings
        pool_config = self.config_data.get('connection_pools', {}).get(environment, {})
        service_pool = pool_config.get(f'{service.replace("pro", "ai_service")}', {})

        # Generate configuration file content
        config_content = self._generate_config_content(env_config, ai_optimizations, service_pool)

        return config_content

    def _generate_config_content(self, env_config: Dict, ai_config: Dict, pool_config: Dict) -> str:
        """Generate the actual PostgreSQL configuration content"""

        config_lines = [
            "# PostgreSQL Configuration",
            f"# Generated for SaaS Control Deck",
            f"# Generated at: {os.getenv('GITHUB_SHA', 'unknown')}",
            "",
            "# Memory Configuration"
        ]

        # Memory settings
        memory_config = env_config.get('memory', {})
        for key, value in memory_config.items():
            config_lines.append(f"{key} = '{value}'")

        config_lines.extend(["", "# Connection Settings"])

        # Connection settings
        connection_config = env_config.get('connection', {})
        for key, value in connection_config.items():
            if isinstance(value, str):
                config_lines.append(f"{key} = '{value}'")
            else:
                config_lines.append(f"{key} = {value}")

        config_lines.extend(["", "# Query Planner Settings"])

        # Planner settings
        planner_config = env_config.get('planner', {})
        for key, value in planner_config.items():
            config_lines.append(f"{key} = {value}")

        config_lines.extend(["", "# Logging Configuration"])

        # Logging settings
        logging_config = env_config.get('logging', {})
        for key, value in logging_config.items():
            if isinstance(value, str):
                config_lines.append(f"{key} = '{value}'")
            else:
                config_lines.append(f"{key} = {'on' if value else 'off'}")

        config_lines.extend(["", "# Autovacuum Settings"])

        # Autovacuum settings
        autovacuum_config = env_config.get('autovacuum', {})
        for key, value in autovacuum_config.items():
            if isinstance(value, str):
                config_lines.append(f"{key} = '{value}'")
            else:
                config_lines.append(f"{key} = {value}")

        config_lines.extend(["", "# Extensions and AI Optimizations"])

        # Extensions
        extensions_config = env_config.get('extensions', {})
        for key, value in extensions_config.items():
            if isinstance(value, str):
                config_lines.append(f"{key} = '{value}'")
            else:
                config_lines.append(f"{key} = {'on' if value else 'off'}")

        # AI-specific settings
        json_config = ai_config.get('json_optimization', {})
        for key, value in json_config.items():
            if isinstance(value, str):
                config_lines.append(f"{key} = '{value}'")
            else:
                config_lines.append(f"{key} = {value}")

        return '\n'.join(config_lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate PostgreSQL configuration')
    parser.add_argument('--environment', required=True, choices=['development', 'staging', 'production'])
    parser.add_argument('--service', required=True, choices=['pro1', 'pro2'])
    parser.add_argument('--config-file', required=True)
    parser.add_argument('--output-dir', required=True)

    args = parser.parse_args()

    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)

    # Generate configuration
    generator = PostgreSQLConfigGenerator(args.config_file)
    config_content = generator.generate_config(args.environment, args.service)

    # Write configuration file
    output_file = f"{args.output_dir}/{args.environment}-{args.service}.conf"
    with open(output_file, 'w') as f:
        f.write(config_content)

    print(f"✅ Generated PostgreSQL configuration: {output_file}")
```

## 3. Permission and Access Control Synchronization

### Role-Based Access Control Sync

```python
# scripts/sync-database-permissions.py
import asyncio
import asyncpg
import os
import json
from typing import Dict, Any, List
import logging

class DatabasePermissionSyncer:
    def __init__(self, source_db_url: str, target_db_url: str):
        self.source_db_url = source_db_url
        self.target_db_url = target_db_url
        self.logger = logging.getLogger(__name__)

    async def sync_permissions(self, environment: str) -> Dict[str, Any]:
        """Sync database permissions between environments"""

        source_conn = await asyncpg.connect(self.source_db_url)
        target_conn = await asyncpg.connect(self.target_db_url)

        try:
            # Get permission template for environment
            permission_template = await self.get_permission_template(environment)

            # Sync users and roles
            users_synced = await self.sync_users_and_roles(source_conn, target_conn, permission_template)

            # Sync table permissions
            table_permissions = await self.sync_table_permissions(target_conn, permission_template)

            # Sync function/procedure permissions
            function_permissions = await self.sync_function_permissions(target_conn, permission_template)

            # Create environment-specific roles
            environment_roles = await self.create_environment_roles(target_conn, environment)

            return {
                "status": "success",
                "environment": environment,
                "users_synced": users_synced,
                "table_permissions": table_permissions,
                "function_permissions": function_permissions,
                "environment_roles": environment_roles
            }

        finally:
            await source_conn.close()
            await target_conn.close()

    async def get_permission_template(self, environment: str) -> Dict[str, Any]:
        """Get permission template for specific environment"""

        templates = {
            "development": {
                "default_privileges": {
                    "tables": {"SELECT": True, "INSERT": True, "UPDATE": True, "DELETE": True},
                    "sequences": {"USAGE": True, "SELECT": True},
                    "functions": {"EXECUTE": True}
                },
                "restricted_tables": [],
                "admin_access": True
            },
            "staging": {
                "default_privileges": {
                    "tables": {"SELECT": True, "INSERT": True, "UPDATE": True, "DELETE": False},
                    "sequences": {"USAGE": True, "SELECT": True},
                    "functions": {"EXECUTE": True}
                },
                "restricted_tables": ["audit_logs", "security_events"],
                "admin_access": False
            },
            "production": {
                "default_privileges": {
                    "tables": {"SELECT": True, "INSERT": False, "UPDATE": False, "DELETE": False},
                    "sequences": {"USAGE": False, "SELECT": True},
                    "functions": {"EXECUTE": False}
                },
                "restricted_tables": ["users", "organizations", "audit_logs", "security_events", "billing_data"],
                "admin_access": False
            }
        }

        return templates.get(environment, templates["development"])

    async def sync_users_and_roles(self, source_conn, target_conn, template: Dict) -> List[str]:
        """Sync users and roles between databases"""

        # Get application roles from source
        source_roles = await source_conn.fetch("""
            SELECT rolname, rolcanlogin, rolcreaterole, rolcreatedb, rolsuper
            FROM pg_roles
            WHERE rolname LIKE 'saascontrol_%'
            ORDER BY rolname
        """)

        synced_roles = []

        for role in source_roles:
            role_name = role['rolname']

            # Check if role exists in target
            role_exists = await target_conn.fetchval("""
                SELECT 1 FROM pg_roles WHERE rolname = $1
            """, role_name)

            if not role_exists:
                # Create role in target with appropriate permissions
                create_sql = f"CREATE ROLE {role_name}"

                if role['rolcanlogin']:
                    create_sql += " LOGIN"

                # Adjust permissions based on environment
                if template["admin_access"] and role['rolcreatedb']:
                    create_sql += " CREATEDB"

                await target_conn.execute(create_sql)
                synced_roles.append(role_name)

        return synced_roles

    async def sync_table_permissions(self, target_conn, template: Dict) -> Dict[str, List[str]]:
        """Sync table permissions according to environment template"""

        # Get all tables
        tables = await target_conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """)

        permissions_applied = {}

        for table_row in tables:
            table_name = table_row['table_name']
            table_permissions = []

            # Check if table is restricted
            if table_name in template.get("restricted_tables", []):
                # Apply restricted permissions
                await target_conn.execute(f"REVOKE ALL ON {table_name} FROM PUBLIC")
                table_permissions.append("REVOKE ALL FROM PUBLIC")
            else:
                # Apply default permissions
                default_privs = template.get("default_privileges", {}).get("tables", {})

                for privilege, granted in default_privs.items():
                    if granted:
                        await target_conn.execute(f"GRANT {privilege} ON {table_name} TO saascontrol_user")
                        table_permissions.append(f"GRANT {privilege} TO saascontrol_user")
                    else:
                        await target_conn.execute(f"REVOKE {privilege} ON {table_name} FROM saascontrol_user")
                        table_permissions.append(f"REVOKE {privilege} FROM saascontrol_user")

            permissions_applied[table_name] = table_permissions

        return permissions_applied

    async def create_environment_roles(self, target_conn, environment: str) -> List[str]:
        """Create environment-specific roles"""

        env_roles = {
            "development": [
                "saascontrol_dev_admin",
                "saascontrol_dev_user",
                "saascontrol_dev_readonly"
            ],
            "staging": [
                "saascontrol_stage_user",
                "saascontrol_stage_readonly",
                "saascontrol_stage_tester"
            ],
            "production": [
                "saascontrol_prod_readonly",
                "saascontrol_prod_monitor",
                "saascontrol_prod_backup"
            ]
        }

        roles_to_create = env_roles.get(environment, [])
        created_roles = []

        for role_name in roles_to_create:
            # Check if role exists
            role_exists = await target_conn.fetchval("""
                SELECT 1 FROM pg_roles WHERE rolname = $1
            """, role_name)

            if not role_exists:
                await target_conn.execute(f"CREATE ROLE {role_name}")
                created_roles.append(role_name)

                # Apply role-specific permissions
                await self.apply_role_permissions(target_conn, role_name, environment)

        return created_roles

    async def apply_role_permissions(self, conn, role_name: str, environment: str):
        """Apply permissions specific to each role"""

        if "readonly" in role_name:
            # Grant read-only access
            await conn.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {role_name}")
            await conn.execute(f"GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO {role_name}")

        elif "admin" in role_name and environment == "development":
            # Grant admin access in development
            await conn.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {role_name}")
            await conn.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {role_name}")

        elif "monitor" in role_name:
            # Grant monitoring access
            await conn.execute(f"GRANT SELECT ON pg_stat_activity TO {role_name}")
            await conn.execute(f"GRANT SELECT ON pg_stat_database TO {role_name}")

        elif "backup" in role_name:
            # Grant backup access
            await conn.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {role_name}")

if __name__ == "__main__":
    source_db_url = os.getenv("SOURCE_DATABASE_URL")
    target_db_url = os.getenv("TARGET_DATABASE_URL")
    environment = os.getenv("ENVIRONMENT")

    syncer = DatabasePermissionSyncer(source_db_url, target_db_url)
    result = asyncio.run(syncer.sync_permissions(environment))

    print(f"✅ Permission sync completed for {environment}")
    print(f"✅ Users synced: {len(result['users_synced'])}")
    print(f"✅ Table permissions: {len(result['table_permissions'])}")
    print(f"✅ Environment roles: {len(result['environment_roles'])}")
```

## 4. Data Consistency and Validation

### Cross-Environment Data Validation

```python
# scripts/validate-data-consistency.py
import asyncio
import asyncpg
import os
from typing import Dict, Any, List, Tuple
import hashlib
import logging

class DataConsistencyValidator:
    def __init__(self, source_db_url: str, target_db_url: str):
        self.source_db_url = source_db_url
        self.target_db_url = target_db_url
        self.logger = logging.getLogger(__name__)

    async def validate_consistency(self) -> Dict[str, Any]:
        """Validate data consistency between environments"""

        source_conn = await asyncpg.connect(self.source_db_url)
        target_conn = await asyncpg.connect(self.target_db_url)

        try:
            # Schema consistency check
            schema_consistency = await self.validate_schema_consistency(source_conn, target_conn)

            # Data integrity check (excluding sensitive data)
            data_integrity = await self.validate_data_integrity(source_conn, target_conn)

            # Reference consistency check
            reference_consistency = await self.validate_reference_consistency(target_conn)

            # Performance consistency check
            performance_consistency = await self.validate_performance_consistency(target_conn)

            return {
                "status": "success",
                "schema_consistency": schema_consistency,
                "data_integrity": data_integrity,
                "reference_consistency": reference_consistency,
                "performance_consistency": performance_consistency
            }

        finally:
            await source_conn.close()
            await target_conn.close()

    async def validate_schema_consistency(self, source_conn, target_conn) -> Dict[str, Any]:
        """Validate that schemas are consistent between environments"""

        # Compare table structures
        source_tables = await self.get_table_structure(source_conn)
        target_tables = await self.get_table_structure(target_conn)

        schema_issues = []

        for table_name, source_structure in source_tables.items():
            if table_name not in target_tables:
                schema_issues.append(f"Table {table_name} missing in target")
                continue

            target_structure = target_tables[table_name]

            # Compare columns
            source_columns = set(source_structure.keys())
            target_columns = set(target_structure.keys())

            missing_columns = source_columns - target_columns
            extra_columns = target_columns - source_columns

            if missing_columns:
                schema_issues.append(f"Table {table_name}: missing columns {missing_columns}")

            if extra_columns:
                schema_issues.append(f"Table {table_name}: extra columns {extra_columns}")

        return {
            "consistent": len(schema_issues) == 0,
            "issues": schema_issues,
            "tables_compared": len(source_tables)
        }

    async def get_table_structure(self, conn) -> Dict[str, Dict]:
        """Get table structure information"""

        query = """
            SELECT
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """

        rows = await conn.fetch(query)

        tables = {}
        for row in rows:
            table_name = row['table_name']
            if table_name not in tables:
                tables[table_name] = {}

            tables[table_name][row['column_name']] = {
                'data_type': row['data_type'],
                'is_nullable': row['is_nullable'],
                'column_default': row['column_default']
            }

        return tables

    async def validate_data_integrity(self, source_conn, target_conn) -> Dict[str, Any]:
        """Validate data integrity using statistical comparisons"""

        # Tables to validate (excluding sensitive ones)
        validation_tables = ['projects', 'data_sources', 'ai_tasks']

        integrity_results = {}

        for table_name in validation_tables:
            # Compare row counts
            source_count = await source_conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            target_count = await target_conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")

            # Calculate data distribution hash (for non-sensitive columns)
            source_hash = await self.calculate_data_hash(source_conn, table_name)
            target_hash = await self.calculate_data_hash(target_conn, table_name)

            integrity_results[table_name] = {
                "source_count": source_count,
                "target_count": target_count,
                "count_match": source_count == target_count,
                "distribution_match": source_hash == target_hash,
                "integrity_score": self.calculate_integrity_score(source_count, target_count, source_hash == target_hash)
            }

        return integrity_results

    async def calculate_data_hash(self, conn, table_name: str) -> str:
        """Calculate hash of data distribution for integrity checking"""

        # Get non-sensitive column distribution
        non_sensitive_columns = await self.get_non_sensitive_columns(conn, table_name)

        if not non_sensitive_columns:
            return "no_hashable_columns"

        # Create hash based on data distribution
        query = f"""
            SELECT
                COUNT(*) as total_rows,
                COUNT(DISTINCT {non_sensitive_columns[0]}) as distinct_values,
                MIN({non_sensitive_columns[0]}) as min_value,
                MAX({non_sensitive_columns[0]}) as max_value
            FROM {table_name}
        """

        result = await conn.fetchrow(query)

        # Create hash from distribution characteristics
        hash_input = f"{result['total_rows']}-{result['distinct_values']}-{result['min_value']}-{result['max_value']}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    async def get_non_sensitive_columns(self, conn, table_name: str) -> List[str]:
        """Get list of non-sensitive columns for hashing"""

        sensitive_patterns = ['email', 'phone', 'address', 'ssn', 'credit', 'password', 'token']

        query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = $1
            AND table_schema = 'public'
            AND data_type IN ('integer', 'bigint', 'smallint', 'timestamp', 'date')
        """

        columns = await conn.fetch(query, table_name)

        # Filter out potentially sensitive columns
        non_sensitive = []
        for col in columns:
            column_name = col['column_name'].lower()
            if not any(pattern in column_name for pattern in sensitive_patterns):
                non_sensitive.append(col['column_name'])

        return non_sensitive

    def calculate_integrity_score(self, source_count: int, target_count: int, distribution_match: bool) -> float:
        """Calculate integrity score between 0 and 1"""

        if source_count == 0 and target_count == 0:
            return 1.0

        if source_count == 0 or target_count == 0:
            return 0.0

        # Count similarity (0-0.7)
        count_similarity = min(source_count, target_count) / max(source_count, target_count) * 0.7

        # Distribution match (0-0.3)
        distribution_score = 0.3 if distribution_match else 0.0

        return count_similarity + distribution_score

if __name__ == "__main__":
    source_db_url = os.getenv("SOURCE_DATABASE_URL")
    target_db_url = os.getenv("TARGET_DATABASE_URL")

    validator = DataConsistencyValidator(source_db_url, target_db_url)
    result = asyncio.run(validator.validate_consistency())

    print("✅ Data consistency validation completed")
    print(f"✅ Schema consistent: {result['schema_consistency']['consistent']}")
    print(f"✅ Data integrity validated for {len(result['data_integrity'])} tables")

    # Check overall consistency
    all_consistent = (
        result['schema_consistency']['consistent'] and
        all(table['integrity_score'] > 0.8 for table in result['data_integrity'].values())
    )

    if all_consistent:
        print("✅ Overall consistency: PASSED")
    else:
        print("❌ Overall consistency: FAILED")
        exit(1)
```

## Summary

This environment data synchronization workflow provides:

1. **Automated Data Sanitization**: Production to staging with PII removal and anonymization
2. **Configuration Management**: Environment-specific PostgreSQL configurations with version control
3. **Permission Synchronization**: Role-based access control with environment-appropriate restrictions
4. **Data Consistency Validation**: Cross-environment integrity checks and validation
5. **Incremental Synchronization**: Efficient delta sync to minimize resource usage
6. **Security Compliance**: GDPR-compliant data handling with encryption and audit trails

The workflow ensures secure, efficient, and compliant data flow between the three environments while maintaining data privacy and regulatory compliance for the SaaS Control Deck platform.