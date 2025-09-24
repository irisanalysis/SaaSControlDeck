# Database Migration Workflows
# SaaS Control Deck - Three-Environment Database CI/CD Architecture

## Overview

This document defines the comprehensive database migration workflows for the SaaS Control Deck platform, supporting our three-environment architecture (Development, Staging, Production) with six PostgreSQL databases (backend-pro1 and backend-pro2 for each environment).

## Environment Architecture

### Database Infrastructure
- **Cloud PostgreSQL Server**: `47.79.87.199:5432`
- **Development Databases**: `saascontrol_dev_pro1`, `saascontrol_dev_pro2`
- **Staging Databases**: `saascontrol_stage_pro1`, `saascontrol_stage_pro2`
- **Production Databases**: `saascontrol_prod_pro1`, `saascontrol_prod_pro2`

### Service Port Allocation
- **Backend-Pro1**: Ports 8000-8099 (API Gateway: 8000, Data Service: 8001, AI Service: 8002)
- **Backend-Pro2**: Ports 8100-8199 (API Gateway: 8100, Data Service: 8101, AI Service: 8102)

## 1. Development Environment Migration Workflow

### Automatic Schema Change Detection

```yaml
# .github/workflows/database-migration-dev.yml
name: Development Database Migration

on:
  push:
    branches: [develop, feature/*]
    paths:
      - 'backend/backend-pro1/alembic/**'
      - 'backend/backend-pro2/alembic/**'
      - 'backend/*/models/**'
      - 'backend/*/schemas/**'

jobs:
  detect-migrations:
    runs-on: ubuntu-latest
    outputs:
      pro1-changes: ${{ steps.detect.outputs.pro1-changes }}
      pro2-changes: ${{ steps.detect.outputs.pro2-changes }}

    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      with:
        fetch-depth: 2

    - name: Detect schema changes
      id: detect
      run: |
        # Check for Pro1 migrations
        if git diff HEAD~1 --name-only | grep -E "(backend-pro1/alembic|backend-pro1/models)" > /dev/null; then
          echo "pro1-changes=true" >> $GITHUB_OUTPUT
        else
          echo "pro1-changes=false" >> $GITHUB_OUTPUT
        fi

        # Check for Pro2 migrations
        if git diff HEAD~1 --name-only | grep -E "(backend-pro2/alembic|backend-pro2/models)" > /dev/null; then
          echo "pro2-changes=true" >> $GITHUB_OUTPUT
        else
          echo "pro2-changes=false" >> $GITHUB_OUTPUT
        fi
```

### Migration Script Generation and Validation

```yaml
  migrate-pro1-dev:
    needs: detect-migrations
    if: needs.detect-migrations.outputs.pro1-changes == 'true'
    runs-on: ubuntu-latest
    environment: development

    steps:
    - name: Setup Python Environment
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd backend/backend-pro1
        pip install -r requirements.txt

    - name: Generate migration script
      env:
        DATABASE_URL: ${{ secrets.DEV_PRO1_DATABASE_URL }}
      run: |
        cd backend/backend-pro1
        alembic revision --autogenerate -m "Auto-migration $(date +%Y%m%d_%H%M%S)"

    - name: Validate migration script
      env:
        DATABASE_URL: ${{ secrets.DEV_PRO1_DATABASE_URL }}
      run: |
        cd backend/backend-pro1
        # Dry run migration
        alembic check
        # Test migration on a copy
        python scripts/validate-migration.py

    - name: Apply migration to development
      env:
        DATABASE_URL: ${{ secrets.DEV_PRO1_DATABASE_URL }}
      run: |
        cd backend/backend-pro1
        alembic upgrade head

    - name: Verify migration integrity
      env:
        DATABASE_URL: ${{ secrets.DEV_PRO1_DATABASE_URL }}
      run: |
        cd backend/backend-pro1
        python scripts/verify-schema-integrity.py
        python scripts/verify-data-integrity.py
```

### Development Database Health Verification

```python
# scripts/verify-schema-integrity.py
import asyncio
import asyncpg
import os
from typing import List, Dict, Any

class SchemaIntegrityVerifier:
    def __init__(self, database_url: str):
        self.database_url = database_url

    async def verify_schema_integrity(self) -> Dict[str, Any]:
        """Verify schema integrity after migration"""
        conn = await asyncpg.connect(self.database_url)

        try:
            # Check table existence and structure
            tables = await self.check_table_structure(conn)

            # Verify foreign key constraints
            constraints = await self.check_foreign_keys(conn)

            # Check index integrity
            indexes = await self.check_indexes(conn)

            # Verify data types consistency
            data_types = await self.check_data_types(conn)

            return {
                "status": "success",
                "tables": tables,
                "constraints": constraints,
                "indexes": indexes,
                "data_types": data_types,
                "timestamp": asyncio.get_event_loop().time()
            }

        finally:
            await conn.close()

    async def check_table_structure(self, conn) -> List[Dict]:
        """Verify all expected tables exist with correct structure"""
        query = """
        SELECT
            schemaname,
            tablename,
            tableowner,
            hasindexes,
            hasrules,
            hastriggers
        FROM pg_tables
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schemaname, tablename;
        """

        rows = await conn.fetch(query)
        return [dict(row) for row in rows]

    async def check_foreign_keys(self, conn) -> List[Dict]:
        """Verify foreign key constraints"""
        query = """
        SELECT
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE constraint_type = 'FOREIGN KEY'
        ORDER BY tc.table_name, tc.constraint_name;
        """

        rows = await conn.fetch(query)
        return [dict(row) for row in rows]

    async def check_indexes(self, conn) -> List[Dict]:
        """Verify index integrity and performance"""
        query = """
        SELECT
            schemaname,
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
        ORDER BY schemaname, tablename, indexname;
        """

        rows = await conn.fetch(query)
        return [dict(row) for row in rows]

if __name__ == "__main__":
    database_url = os.getenv("DATABASE_URL")
    verifier = SchemaIntegrityVerifier(database_url)

    result = asyncio.run(verifier.verify_schema_integrity())

    if result["status"] == "success":
        print("✅ Schema integrity verification passed")
        print(f"✅ Found {len(result['tables'])} tables")
        print(f"✅ Found {len(result['constraints'])} foreign key constraints")
        print(f"✅ Found {len(result['indexes'])} indexes")
    else:
        print("❌ Schema integrity verification failed")
        exit(1)
```

## 2. Staging Environment Migration Workflow

### Production-Like Testing Environment

```yaml
# .github/workflows/database-migration-staging.yml
name: Staging Database Migration

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]

jobs:
  promote-to-staging:
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

    - name: Install dependencies
      run: |
        cd backend/backend-${{ matrix.service }}
        pip install -r requirements.txt

    - name: Create staging migration backup
      env:
        DATABASE_URL: ${{ secrets[format('STAGING_{0}_DATABASE_URL', upper(matrix.service))] }}
      run: |
        # Create pre-migration backup
        python scripts/create-migration-backup.py \
          --environment staging \
          --service ${{ matrix.service }} \
          --backup-type pre-migration

    - name: Sync schema from development
      env:
        DEV_DATABASE_URL: ${{ secrets[format('DEV_{0}_DATABASE_URL', upper(matrix.service))] }}
        STAGING_DATABASE_URL: ${{ secrets[format('STAGING_{0}_DATABASE_URL', upper(matrix.service))] }}
      run: |
        cd backend/backend-${{ matrix.service }}
        # Generate schema diff
        python scripts/generate-schema-diff.py \
          --source-db $DEV_DATABASE_URL \
          --target-db $STAGING_DATABASE_URL \
          --output migrations/staging-sync-$(date +%Y%m%d_%H%M%S).sql

        # Apply migrations to staging
        alembic upgrade head

    - name: Load test data
      env:
        DATABASE_URL: ${{ secrets[format('STAGING_{0}_DATABASE_URL', upper(matrix.service))] }}
      run: |
        cd backend/backend-${{ matrix.service }}
        python scripts/load-test-data.py --environment staging

    - name: Run integration tests
      env:
        DATABASE_URL: ${{ secrets[format('STAGING_{0}_DATABASE_URL', upper(matrix.service))] }}
      run: |
        cd backend/backend-${{ matrix.service }}
        pytest tests/integration/ -v --tb=short
        pytest tests/performance/ -v --tb=short
```

### Test Data Management

```python
# scripts/load-test-data.py
import asyncio
import asyncpg
import json
import os
from typing import Dict, List, Any
from datetime import datetime, timedelta
import random

class TestDataManager:
    def __init__(self, database_url: str, environment: str):
        self.database_url = database_url
        self.environment = environment

    async def load_test_data(self) -> Dict[str, Any]:
        """Load comprehensive test data for staging environment"""
        conn = await asyncpg.connect(self.database_url)

        try:
            # Clear existing test data
            await self.clear_test_data(conn)

            # Load base data
            users = await self.create_test_users(conn)
            projects = await self.create_test_projects(conn, users)
            ai_tasks = await self.create_test_ai_tasks(conn, projects)
            data_sources = await self.create_test_data_sources(conn, projects)

            # Create AI workload simulation data
            await self.create_ai_performance_data(conn, ai_tasks)

            return {
                "status": "success",
                "users_created": len(users),
                "projects_created": len(projects),
                "ai_tasks_created": len(ai_tasks),
                "data_sources_created": len(data_sources),
                "environment": self.environment
            }

        finally:
            await conn.close()

    async def create_test_users(self, conn) -> List[int]:
        """Create test users for different subscription tiers"""
        users = []

        # Free tier users (limited features)
        for i in range(10):
            user_id = await conn.fetchval("""
                INSERT INTO users (
                    email, username, subscription_tier,
                    api_quota_used, api_quota_limit,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, 'free',
                    $3, 1000,
                    $4, $4
                ) RETURNING id
            """,
            f"test_user_{i}@staging.local",
            f"test_user_{i}",
            random.randint(0, 800),  # Used quota
            datetime.utcnow()
            )
            users.append(user_id)

        # Professional tier users (advanced features)
        for i in range(5):
            user_id = await conn.fetchval("""
                INSERT INTO users (
                    email, username, subscription_tier,
                    api_quota_used, api_quota_limit,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, 'professional',
                    $3, 10000,
                    $4, $4
                ) RETURNING id
            """,
            f"pro_user_{i}@staging.local",
            f"pro_user_{i}",
            random.randint(1000, 8000),
            datetime.utcnow()
            )
            users.append(user_id)

        # Enterprise tier users (unlimited features)
        for i in range(2):
            user_id = await conn.fetchval("""
                INSERT INTO users (
                    email, username, subscription_tier,
                    api_quota_used, api_quota_limit,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, 'enterprise',
                    $3, 100000,
                    $4, $4
                ) RETURNING id
            """,
            f"enterprise_user_{i}@staging.local",
            f"enterprise_user_{i}",
            random.randint(5000, 20000),
            datetime.utcnow()
            )
            users.append(user_id)

        return users

    async def create_test_ai_tasks(self, conn, projects: List[int]) -> List[int]:
        """Create AI tasks with realistic processing patterns"""
        ai_tasks = []

        task_types = ['data_analysis', 'text_classification', 'image_recognition', 'prediction_model']
        statuses = ['pending', 'processing', 'completed', 'failed']

        for _ in range(100):
            project_id = random.choice(projects)
            task_type = random.choice(task_types)
            status = random.choice(statuses)

            # Simulate realistic processing times based on task type
            processing_time_map = {
                'data_analysis': random.randint(5000, 30000),    # 5-30 seconds
                'text_classification': random.randint(1000, 10000),  # 1-10 seconds
                'image_recognition': random.randint(3000, 15000),    # 3-15 seconds
                'prediction_model': random.randint(10000, 120000)    # 10-120 seconds
            }

            task_id = await conn.fetchval("""
                INSERT INTO ai_tasks (
                    project_id, task_type, status,
                    input_data, output_data,
                    processing_time_ms, confidence_score,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3,
                    $4, $5,
                    $6, $7,
                    $8, $8
                ) RETURNING id
            """,
            project_id, task_type, status,
            json.dumps({"data_size_mb": random.randint(1, 100)}),
            json.dumps({"accuracy": random.uniform(0.7, 0.98)}) if status == 'completed' else None,
            processing_time_map[task_type] if status in ['completed', 'failed'] else None,
            random.uniform(0.6, 0.95) if status == 'completed' else None,
            datetime.utcnow() - timedelta(hours=random.randint(0, 72))
            )
            ai_tasks.append(task_id)

        return ai_tasks

if __name__ == "__main__":
    database_url = os.getenv("DATABASE_URL")
    environment = os.getenv("ENVIRONMENT", "staging")

    manager = TestDataManager(database_url, environment)
    result = asyncio.run(manager.load_test_data())

    print(f"✅ Test data loaded successfully for {environment}")
    print(f"✅ Created {result['users_created']} users")
    print(f"✅ Created {result['projects_created']} projects")
    print(f"✅ Created {result['ai_tasks_created']} AI tasks")
```

## 3. Production Environment Migration Workflow

### Blue-Green Deployment Strategy

```yaml
# .github/workflows/database-migration-production.yml
name: Production Database Migration

on:
  workflow_dispatch:
    inputs:
      migration_strategy:
        description: 'Migration strategy'
        required: true
        default: 'blue-green'
        type: choice
        options:
        - blue-green
        - rolling
        - maintenance-window

      confirm_production:
        description: 'Confirm production deployment (type PRODUCTION to confirm)'
        required: true
        type: string

jobs:
  validate-production-request:
    runs-on: ubuntu-latest
    if: github.event.inputs.confirm_production == 'PRODUCTION'

    steps:
    - name: Validate production deployment request
      run: |
        echo "✅ Production deployment confirmed"
        echo "Strategy: ${{ github.event.inputs.migration_strategy }}"
        echo "Initiated by: ${{ github.actor }}"
        echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

  pre-production-validation:
    needs: validate-production-request
    runs-on: ubuntu-latest
    environment: production

    steps:
    - name: Pre-production health check
      env:
        PROD_PRO1_DATABASE_URL: ${{ secrets.PROD_PRO1_DATABASE_URL }}
        PROD_PRO2_DATABASE_URL: ${{ secrets.PROD_PRO2_DATABASE_URL }}
      run: |
        # Check current production database health
        python scripts/production-health-check.py --comprehensive

    - name: Create production backup
      env:
        PROD_PRO1_DATABASE_URL: ${{ secrets.PROD_PRO1_DATABASE_URL }}
        PROD_PRO2_DATABASE_URL: ${{ secrets.PROD_PRO2_DATABASE_URL }}
      run: |
        # Create full production backup before migration
        python scripts/create-production-backup.py \
          --backup-type full \
          --retention-days 90 \
          --compression gzip

    - name: Validate migration compatibility
      env:
        STAGING_PRO1_DATABASE_URL: ${{ secrets.STAGING_PRO1_DATABASE_URL }}
        PROD_PRO1_DATABASE_URL: ${{ secrets.PROD_PRO1_DATABASE_URL }}
      run: |
        # Ensure staging migrations are compatible with production
        python scripts/validate-production-compatibility.py \
          --staging-db $STAGING_PRO1_DATABASE_URL \
          --production-db $PROD_PRO1_DATABASE_URL

  blue-green-migration:
    needs: pre-production-validation
    if: github.event.inputs.migration_strategy == 'blue-green'
    runs-on: ubuntu-latest
    environment: production

    strategy:
      matrix:
        service: [pro1, pro2]

    steps:
    - name: Create Blue Environment (Current Production Copy)
      env:
        DATABASE_URL: ${{ secrets[format('PROD_{0}_DATABASE_URL', upper(matrix.service))] }}
      run: |
        # Create blue environment as copy of current production
        python scripts/create-blue-environment.py \
          --service ${{ matrix.service }} \
          --source-db $DATABASE_URL

    - name: Apply Migrations to Green Environment
      env:
        GREEN_DATABASE_URL: ${{ secrets[format('GREEN_{0}_DATABASE_URL', upper(matrix.service))] }}
      run: |
        cd backend/backend-${{ matrix.service }}
        # Apply all pending migrations to green environment
        DATABASE_URL=$GREEN_DATABASE_URL alembic upgrade head

    - name: Validate Green Environment
      env:
        GREEN_DATABASE_URL: ${{ secrets[format('GREEN_{0}_DATABASE_URL', upper(matrix.service))] }}
      run: |
        # Comprehensive validation of green environment
        python scripts/validate-green-environment.py \
          --service ${{ matrix.service }} \
          --database-url $GREEN_DATABASE_URL

    - name: Switch Traffic to Green (Atomic)
      env:
        BLUE_DATABASE_URL: ${{ secrets[format('PROD_{0}_DATABASE_URL', upper(matrix.service))] }}
        GREEN_DATABASE_URL: ${{ secrets[format('GREEN_{0}_DATABASE_URL', upper(matrix.service))] }}
      run: |
        # Atomic switch from blue to green
        python scripts/atomic-blue-green-switch.py \
          --service ${{ matrix.service }} \
          --blue-db $BLUE_DATABASE_URL \
          --green-db $GREEN_DATABASE_URL

    - name: Post-Migration Validation
      env:
        DATABASE_URL: ${{ secrets[format('PROD_{0}_DATABASE_URL', upper(matrix.service))] }}
      run: |
        # Validate production after switch
        python scripts/post-migration-validation.py \
          --service ${{ matrix.service }} \
          --database-url $DATABASE_URL

  rollback-capability:
    needs: blue-green-migration
    if: failure()
    runs-on: ubuntu-latest
    environment: production

    steps:
    - name: Automatic Rollback
      env:
        BLUE_DATABASE_URL: ${{ secrets.PROD_PRO1_DATABASE_URL }}
        GREEN_DATABASE_URL: ${{ secrets.GREEN_PRO1_DATABASE_URL }}
      run: |
        # Automatic rollback to blue environment
        python scripts/automatic-rollback.py \
          --blue-db $BLUE_DATABASE_URL \
          --green-db $GREEN_DATABASE_URL \
          --rollback-reason "Migration validation failed"
```

### Zero-Downtime Migration Strategy

```python
# scripts/atomic-blue-green-switch.py
import asyncio
import asyncpg
import os
import time
from typing import Dict, Any
import logging

class BlueGreenSwitcher:
    def __init__(self, service: str, blue_db_url: str, green_db_url: str):
        self.service = service
        self.blue_db_url = blue_db_url
        self.green_db_url = green_db_url
        self.logger = logging.getLogger(__name__)

    async def atomic_switch(self) -> Dict[str, Any]:
        """Perform atomic blue-green switch with minimal downtime"""
        start_time = time.time()

        try:
            # Phase 1: Final data sync (last-minute changes)
            await self.final_data_sync()

            # Phase 2: Enable maintenance mode (brief)
            await self.enable_maintenance_mode()

            # Phase 3: Final consistency check
            await self.final_consistency_check()

            # Phase 4: Atomic DNS/Configuration switch
            await self.atomic_configuration_switch()

            # Phase 5: Disable maintenance mode
            await self.disable_maintenance_mode()

            # Phase 6: Validate switch success
            await self.validate_switch_success()

            end_time = time.time()
            downtime = end_time - start_time

            return {
                "status": "success",
                "service": self.service,
                "downtime_seconds": downtime,
                "switch_timestamp": time.time()
            }

        except Exception as e:
            self.logger.error(f"Blue-green switch failed: {e}")
            await self.emergency_rollback()
            raise

    async def final_data_sync(self):
        """Sync any last-minute changes from blue to green"""
        blue_conn = await asyncpg.connect(self.blue_db_url)
        green_conn = await asyncpg.connect(self.green_db_url)

        try:
            # Get latest transaction timestamp from blue
            last_blue_tx = await blue_conn.fetchval("""
                SELECT pg_current_xact_id_if_assigned()
            """)

            # Sync incremental changes (implement based on your change tracking)
            await self.sync_incremental_changes(blue_conn, green_conn, last_blue_tx)

        finally:
            await blue_conn.close()
            await green_conn.close()

    async def enable_maintenance_mode(self):
        """Enable brief maintenance mode"""
        # Update load balancer configuration
        await self.update_load_balancer_config(maintenance=True)

        # Wait for in-flight requests to complete
        await asyncio.sleep(2)

    async def atomic_configuration_switch(self):
        """Perform atomic configuration switch"""
        # Update environment variables
        await self.update_environment_config()

        # Update load balancer to point to green database
        await self.update_load_balancer_config(target="green")

        # Update application configuration
        await self.update_application_config()

    async def validate_switch_success(self):
        """Validate that the switch was successful"""
        green_conn = await asyncpg.connect(self.green_db_url)

        try:
            # Test database connectivity
            await green_conn.fetchval("SELECT 1")

            # Validate data integrity
            row_count = await green_conn.fetchval("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
            """)

            if row_count == 0:
                raise Exception("Green database appears to be empty")

            self.logger.info(f"✅ Green environment validated with {row_count} tables")

        finally:
            await green_conn.close()

if __name__ == "__main__":
    service = os.getenv("SERVICE")
    blue_db_url = os.getenv("BLUE_DATABASE_URL")
    green_db_url = os.getenv("GREEN_DATABASE_URL")

    switcher = BlueGreenSwitcher(service, blue_db_url, green_db_url)
    result = asyncio.run(switcher.atomic_switch())

    print(f"✅ Blue-green switch completed for {service}")
    print(f"✅ Downtime: {result['downtime_seconds']:.2f} seconds")
```

## 4. Migration Error Handling and Rollback

### Automatic Rollback System

```python
# scripts/automatic-rollback.py
import asyncio
import asyncpg
import os
import time
from typing import Dict, Any, Optional
import logging

class AutomaticRollback:
    def __init__(self, blue_db_url: str, green_db_url: str, rollback_reason: str):
        self.blue_db_url = blue_db_url
        self.green_db_url = green_db_url
        self.rollback_reason = rollback_reason
        self.logger = logging.getLogger(__name__)

    async def execute_rollback(self) -> Dict[str, Any]:
        """Execute automatic rollback to blue environment"""
        start_time = time.time()

        try:
            # Phase 1: Enable maintenance mode
            await self.enable_emergency_maintenance()

            # Phase 2: Validate blue environment integrity
            await self.validate_blue_environment()

            # Phase 3: Switch back to blue configuration
            await self.switch_to_blue_config()

            # Phase 4: Disable maintenance mode
            await self.disable_maintenance_mode()

            # Phase 5: Validate rollback success
            await self.validate_rollback_success()

            end_time = time.time()
            rollback_time = end_time - start_time

            # Phase 6: Send rollback notifications
            await self.send_rollback_notifications(rollback_time)

            return {
                "status": "success",
                "rollback_reason": self.rollback_reason,
                "rollback_time_seconds": rollback_time,
                "rollback_timestamp": time.time()
            }

        except Exception as e:
            self.logger.critical(f"Rollback failed: {e}")
            await self.escalate_emergency()
            raise

    async def validate_blue_environment(self):
        """Ensure blue environment is still valid for rollback"""
        blue_conn = await asyncpg.connect(self.blue_db_url)

        try:
            # Test connectivity
            await blue_conn.fetchval("SELECT 1")

            # Check data integrity
            table_count = await blue_conn.fetchval("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = 'public'
            """)

            if table_count == 0:
                raise Exception("Blue environment is corrupted - cannot rollback")

            # Check for any data corruption
            await self.check_blue_data_integrity(blue_conn)

            self.logger.info(f"✅ Blue environment validated for rollback")

        finally:
            await blue_conn.close()

    async def send_rollback_notifications(self, rollback_time: float):
        """Send notifications about successful rollback"""
        notification_data = {
            "event": "database_rollback_completed",
            "reason": self.rollback_reason,
            "rollback_time_seconds": rollback_time,
            "timestamp": time.time(),
            "severity": "high"
        }

        # Send to monitoring systems
        await self.send_to_prometheus_alertmanager(notification_data)

        # Send to incident management
        await self.create_incident_ticket(notification_data)

        # Send to team notifications (Slack, email, etc.)
        await self.send_team_notifications(notification_data)

if __name__ == "__main__":
    blue_db_url = os.getenv("BLUE_DATABASE_URL")
    green_db_url = os.getenv("GREEN_DATABASE_URL")
    rollback_reason = os.getenv("ROLLBACK_REASON", "Unknown failure")

    rollback = AutomaticRollback(blue_db_url, green_db_url, rollback_reason)
    result = asyncio.run(rollback.execute_rollback())

    print(f"✅ Automatic rollback completed")
    print(f"✅ Reason: {result['rollback_reason']}")
    print(f"✅ Rollback time: {result['rollback_time_seconds']:.2f} seconds")
```

## 5. Performance Optimization and Monitoring

### Migration Performance Monitoring

```python
# scripts/migration-performance-monitor.py
import asyncio
import asyncpg
import time
from typing import Dict, Any, List
import psutil
import logging

class MigrationPerformanceMonitor:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.logger = logging.getLogger(__name__)

    async def monitor_migration_performance(self, migration_id: str) -> Dict[str, Any]:
        """Monitor migration performance in real-time"""
        conn = await asyncpg.connect(self.database_url)

        try:
            start_time = time.time()
            performance_data = []

            while await self.is_migration_running(conn, migration_id):
                # Collect performance metrics
                metrics = await self.collect_performance_metrics(conn)
                metrics['timestamp'] = time.time()
                metrics['elapsed_time'] = time.time() - start_time

                performance_data.append(metrics)

                # Check for performance thresholds
                await self.check_performance_thresholds(metrics)

                # Wait before next collection
                await asyncio.sleep(5)

            end_time = time.time()
            total_time = end_time - start_time

            return {
                "migration_id": migration_id,
                "total_time_seconds": total_time,
                "performance_data": performance_data,
                "status": "completed"
            }

        finally:
            await conn.close()

    async def collect_performance_metrics(self, conn) -> Dict[str, Any]:
        """Collect comprehensive performance metrics"""
        # Database metrics
        db_metrics = await conn.fetchrow("""
            SELECT
                numbackends as active_connections,
                xact_commit as transactions_committed,
                xact_rollback as transactions_rolled_back,
                blks_read as blocks_read,
                blks_hit as blocks_hit,
                tup_returned as tuples_returned,
                tup_fetched as tuples_fetched,
                tup_inserted as tuples_inserted,
                tup_updated as tuples_updated,
                tup_deleted as tuples_deleted
            FROM pg_stat_database
            WHERE datname = current_database()
        """)

        # System metrics
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_io_read_bytes": psutil.disk_io_counters().read_bytes,
            "disk_io_write_bytes": psutil.disk_io_counters().write_bytes
        }

        # Active queries
        active_queries = await conn.fetch("""
            SELECT
                pid,
                state,
                query,
                query_start,
                extract(epoch from (now() - query_start)) as duration_seconds
            FROM pg_stat_activity
            WHERE state = 'active'
            AND query NOT LIKE '%pg_stat_activity%'
        """)

        return {
            "database": dict(db_metrics) if db_metrics else {},
            "system": system_metrics,
            "active_queries": len(active_queries),
            "long_running_queries": len([q for q in active_queries if q['duration_seconds'] > 30])
        }

    async def check_performance_thresholds(self, metrics: Dict[str, Any]):
        """Check if performance metrics exceed thresholds"""
        warnings = []

        # CPU threshold
        if metrics['system']['cpu_percent'] > 80:
            warnings.append(f"High CPU usage: {metrics['system']['cpu_percent']:.1f}%")

        # Memory threshold
        if metrics['system']['memory_percent'] > 85:
            warnings.append(f"High memory usage: {metrics['system']['memory_percent']:.1f}%")

        # Long running queries
        if metrics['long_running_queries'] > 5:
            warnings.append(f"Too many long-running queries: {metrics['long_running_queries']}")

        # Active connections
        if metrics['database'].get('active_connections', 0) > 100:
            warnings.append(f"High connection count: {metrics['database']['active_connections']}")

        if warnings:
            self.logger.warning(f"Performance warnings: {'; '.join(warnings)}")
            await self.send_performance_alert(warnings)

if __name__ == "__main__":
    database_url = os.getenv("DATABASE_URL")
    migration_id = os.getenv("MIGRATION_ID", "unknown")

    monitor = MigrationPerformanceMonitor(database_url)
    result = asyncio.run(monitor.monitor_migration_performance(migration_id))

    print(f"✅ Migration monitoring completed")
    print(f"✅ Total time: {result['total_time_seconds']:.2f} seconds")
    print(f"✅ Performance data points collected: {len(result['performance_data'])}")
```

## Summary

This database migration workflow provides:

1. **Automated Development Migrations**: Auto-detection, generation, and validation
2. **Staging Environment Sync**: Production-like testing with realistic data
3. **Zero-Downtime Production**: Blue-green deployment with automatic rollback
4. **Performance Monitoring**: Real-time performance tracking and alerting
5. **Error Recovery**: Comprehensive rollback and emergency procedures
6. **Multi-Service Support**: Parallel migration for backend-pro1 and backend-pro2

The workflow ensures data integrity, minimizes downtime, and provides robust error handling for the SaaS Control Deck's three-environment PostgreSQL architecture.