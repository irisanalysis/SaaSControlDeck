# Commercial Deployment Workflows
# SaaS Control Deck - Subscription Tier Management and Feature Control

## Overview

This document defines commercial deployment workflows for the SaaS Control Deck platform, enabling automated management of subscription tiers, feature flags, usage monitoring, and billing integration across our three-environment infrastructure.

## Subscription Architecture

### Tier Structure
- **Free Tier**: Basic features, 1,000 API calls/month, limited data sources
- **Professional Tier**: Advanced features, 10,000 API calls/month, multiple data sources
- **Enterprise Tier**: Full features, unlimited API calls, priority support, custom integrations

### Feature Flag System
- **Dynamic Feature Control**: Real-time feature enabling/disabling
- **A/B Testing Support**: Gradual feature rollout capabilities
- **Usage-Based Limiting**: Automatic quota enforcement
- **Commercial Integration**: Billing system synchronization

## 1. Feature Flag Management Workflow

### Dynamic Feature Control System

```yaml
# .github/workflows/commercial-deployment.yml
name: Commercial Feature Deployment

on:
  push:
    branches: [main]
    paths:
      - 'config/features/**'
      - 'backend/*/features/**'
      - 'frontend/src/features/**'

  workflow_dispatch:
    inputs:
      deployment_type:
        description: 'Deployment type'
        required: true
        default: 'feature-flags'
        type: choice
        options:
        - feature-flags
        - subscription-update
        - billing-sync
        - usage-quota-update

      target_environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options:
        - staging
        - production

      rollout_strategy:
        description: 'Rollout strategy'
        required: true
        default: 'gradual'
        type: choice
        options:
        - immediate
        - gradual
        - canary
        - blue-green

jobs:
  validate-commercial-changes:
    runs-on: ubuntu-latest
    outputs:
      deployment-approved: ${{ steps.validate.outputs.approved }}
      affected-features: ${{ steps.validate.outputs.features }}

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Validate commercial configuration
      id: validate
      run: |
        # Validate feature flag configuration
        python scripts/validate-feature-config.py \
          --config-dir config/features/ \
          --environment ${{ github.event.inputs.target_environment || 'staging' }}

        # Check for breaking changes
        python scripts/check-subscription-compatibility.py \
          --previous-commit HEAD~1 \
          --current-commit HEAD

        echo "approved=true" >> $GITHUB_OUTPUT
        echo "features=$(python scripts/extract-affected-features.py)" >> $GITHUB_OUTPUT

    - name: Generate deployment plan
      env:
        DEPLOYMENT_TYPE: ${{ github.event.inputs.deployment_type || 'feature-flags' }}
        ROLLOUT_STRATEGY: ${{ github.event.inputs.rollout_strategy || 'gradual' }}
      run: |
        python scripts/generate-commercial-deployment-plan.py \
          --deployment-type $DEPLOYMENT_TYPE \
          --rollout-strategy $ROLLOUT_STRATEGY \
          --affected-features '${{ steps.validate.outputs.features }}' \
          --output-file deployment-plan.json

  deploy-feature-flags:
    needs: validate-commercial-changes
    if: needs.validate-commercial-changes.outputs.deployment-approved == 'true'
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.target_environment || 'staging' }}

    strategy:
      matrix:
        service: [pro1, pro2]

    steps:
    - name: Setup Python Environment
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install deployment dependencies
      run: |
        pip install asyncpg redis pydantic

    - name: Deploy feature flags
      env:
        DATABASE_URL: ${{ secrets[format('{0}_{1}_DATABASE_URL', upper(github.event.inputs.target_environment), upper(matrix.service))] }}
        REDIS_URL: ${{ secrets[format('{0}_REDIS_URL', upper(github.event.inputs.target_environment))] }}
        ROLLOUT_STRATEGY: ${{ github.event.inputs.rollout_strategy || 'gradual' }}
      run: |
        python scripts/deploy-feature-flags.py \
          --database-url $DATABASE_URL \
          --redis-url $REDIS_URL \
          --service ${{ matrix.service }} \
          --environment ${{ github.event.inputs.target_environment || 'staging' }} \
          --rollout-strategy $ROLLOUT_STRATEGY \
          --config-file config/features/feature-flags.yaml

    - name: Validate feature flag deployment
      env:
        DATABASE_URL: ${{ secrets[format('{0}_{1}_DATABASE_URL', upper(github.event.inputs.target_environment), upper(matrix.service))] }}
      run: |
        python scripts/validate-feature-deployment.py \
          --database-url $DATABASE_URL \
          --service ${{ matrix.service }} \
          --environment ${{ github.event.inputs.target_environment || 'staging' }}

  update-subscription-quotas:
    needs: deploy-feature-flags
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.target_environment || 'staging' }}

    steps:
    - name: Sync subscription quotas
      env:
        DATABASE_URL: ${{ secrets[format('{0}_PRO1_DATABASE_URL', upper(github.event.inputs.target_environment))] }}
        BILLING_API_KEY: ${{ secrets.BILLING_API_KEY }}
      run: |
        python scripts/sync-subscription-quotas.py \
          --database-url $DATABASE_URL \
          --billing-api-key $BILLING_API_KEY \
          --environment ${{ github.event.inputs.target_environment || 'staging' }}

    - name: Update usage monitoring
      env:
        DATABASE_URL: ${{ secrets[format('{0}_PRO1_DATABASE_URL', upper(github.event.inputs.target_environment))] }}
        PROMETHEUS_URL: ${{ secrets.PROMETHEUS_URL }}
      run: |
        python scripts/update-usage-monitoring.py \
          --database-url $DATABASE_URL \
          --prometheus-url $PROMETHEUS_URL \
          --environment ${{ github.event.inputs.target_environment || 'staging' }}

  canary-deployment:
    needs: validate-commercial-changes
    if: github.event.inputs.rollout_strategy == 'canary'
    runs-on: ubuntu-latest
    environment: production

    steps:
    - name: Deploy to canary environment
      env:
        CANARY_DATABASE_URL: ${{ secrets.CANARY_PRO1_DATABASE_URL }}
        CANARY_REDIS_URL: ${{ secrets.CANARY_REDIS_URL }}
      run: |
        python scripts/canary-deployment.py \
          --database-url $CANARY_DATABASE_URL \
          --redis-url $CANARY_REDIS_URL \
          --canary-percentage 5 \
          --config-file config/features/feature-flags.yaml

    - name: Monitor canary metrics
      env:
        PROMETHEUS_URL: ${{ secrets.PROMETHEUS_URL }}
        CANARY_DURATION_MINUTES: 30
      run: |
        python scripts/monitor-canary-deployment.py \
          --prometheus-url $PROMETHEUS_URL \
          --duration-minutes $CANARY_DURATION_MINUTES \
          --success-threshold 99.5

    - name: Promote or rollback canary
      env:
        PROD_DATABASE_URL: ${{ secrets.PROD_PRO1_DATABASE_URL }}
        CANARY_DATABASE_URL: ${{ secrets.CANARY_PRO1_DATABASE_URL }}
      run: |
        python scripts/canary-promotion.py \
          --prod-db $PROD_DATABASE_URL \
          --canary-db $CANARY_DATABASE_URL \
          --metrics-file /tmp/canary-metrics.json
```

### Feature Flag Deployment Engine

```python
# scripts/deploy-feature-flags.py
import asyncio
import asyncpg
import redis.asyncio as redis
import yaml
import json
import os
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

class FeatureFlagDeployer:
    def __init__(self, database_url: str, redis_url: str, service: str, environment: str):
        self.database_url = database_url
        self.redis_url = redis_url
        self.service = service
        self.environment = environment
        self.logger = logging.getLogger(__name__)

    async def deploy_feature_flags(self, config_file: str, rollout_strategy: str) -> Dict[str, Any]:
        """Deploy feature flags with specified rollout strategy"""

        # Load feature flag configuration
        with open(config_file, 'r') as f:
            feature_config = yaml.safe_load(f)

        # Connect to database and Redis
        db_conn = await asyncpg.connect(self.database_url)
        redis_conn = await redis.from_url(self.redis_url)

        try:
            deployment_start = datetime.utcnow()

            # Create feature flags table if not exists
            await self.ensure_feature_flags_table(db_conn)

            # Deploy features based on strategy
            if rollout_strategy == "immediate":
                result = await self.immediate_deployment(db_conn, redis_conn, feature_config)
            elif rollout_strategy == "gradual":
                result = await self.gradual_deployment(db_conn, redis_conn, feature_config)
            elif rollout_strategy == "canary":
                result = await self.canary_deployment(db_conn, redis_conn, feature_config)
            else:
                raise ValueError(f"Unknown rollout strategy: {rollout_strategy}")

            deployment_end = datetime.utcnow()
            result["deployment_duration"] = (deployment_end - deployment_start).total_seconds()
            result["deployment_timestamp"] = deployment_end.isoformat()

            return result

        finally:
            await db_conn.close()
            await redis_conn.close()

    async def ensure_feature_flags_table(self, conn):
        """Ensure feature flags table exists"""

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS feature_flags (
                id SERIAL PRIMARY KEY,
                feature_name VARCHAR(255) NOT NULL UNIQUE,
                environment VARCHAR(50) NOT NULL,
                service VARCHAR(50) NOT NULL,
                enabled BOOLEAN DEFAULT FALSE,
                rollout_percentage INTEGER DEFAULT 0,
                target_users TEXT[], -- Array of user IDs for targeted rollout
                subscription_tiers TEXT[], -- Array of subscription tiers
                config_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT valid_rollout_percentage CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100)
            )
        """)

        # Create index for fast lookups
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_feature_flags_lookup
            ON feature_flags(feature_name, environment, service)
        """)

    async def immediate_deployment(self, db_conn, redis_conn, feature_config: Dict) -> Dict[str, Any]:
        """Deploy all feature flags immediately"""

        features_deployed = []
        features_updated = []

        for feature_name, config in feature_config.get("features", {}).items():
            # Check if feature exists
            existing_feature = await db_conn.fetchrow("""
                SELECT id, enabled, rollout_percentage
                FROM feature_flags
                WHERE feature_name = $1 AND environment = $2 AND service = $3
            """, feature_name, self.environment, self.service)

            feature_data = {
                "feature_name": feature_name,
                "environment": self.environment,
                "service": self.service,
                "enabled": config.get("enabled", False),
                "rollout_percentage": config.get("rollout_percentage", 100),
                "subscription_tiers": config.get("subscription_tiers", []),
                "config_data": json.dumps(config.get("config", {}))
            }

            if existing_feature:
                # Update existing feature
                await db_conn.execute("""
                    UPDATE feature_flags
                    SET enabled = $1, rollout_percentage = $2, subscription_tiers = $3,
                        config_data = $4, updated_at = CURRENT_TIMESTAMP
                    WHERE feature_name = $5 AND environment = $6 AND service = $7
                """,
                feature_data["enabled"],
                feature_data["rollout_percentage"],
                feature_data["subscription_tiers"],
                feature_data["config_data"],
                feature_name,
                self.environment,
                self.service
                )
                features_updated.append(feature_name)
            else:
                # Insert new feature
                await db_conn.execute("""
                    INSERT INTO feature_flags (
                        feature_name, environment, service, enabled, rollout_percentage,
                        subscription_tiers, config_data
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                feature_data["feature_name"],
                feature_data["environment"],
                feature_data["service"],
                feature_data["enabled"],
                feature_data["rollout_percentage"],
                feature_data["subscription_tiers"],
                feature_data["config_data"]
                )
                features_deployed.append(feature_name)

            # Update Redis cache
            await self.update_redis_cache(redis_conn, feature_name, feature_data)

        return {
            "strategy": "immediate",
            "features_deployed": features_deployed,
            "features_updated": features_updated,
            "total_features": len(features_deployed) + len(features_updated)
        }

    async def gradual_deployment(self, db_conn, redis_conn, feature_config: Dict) -> Dict[str, Any]:
        """Deploy feature flags with gradual rollout"""

        deployment_phases = [
            {"percentage": 5, "duration_minutes": 15},
            {"percentage": 25, "duration_minutes": 30},
            {"percentage": 50, "duration_minutes": 45},
            {"percentage": 100, "duration_minutes": 0}
        ]

        features_in_rollout = []

        for feature_name, config in feature_config.get("features", {}).items():
            if not config.get("enabled", False):
                continue

            # Start gradual rollout
            rollout_id = await self.start_gradual_rollout(
                db_conn, feature_name, config, deployment_phases
            )

            features_in_rollout.append({
                "feature_name": feature_name,
                "rollout_id": rollout_id,
                "phases": deployment_phases
            })

            # Update Redis with initial phase
            initial_phase = deployment_phases[0]
            feature_data = {
                "feature_name": feature_name,
                "environment": self.environment,
                "service": self.service,
                "enabled": True,
                "rollout_percentage": initial_phase["percentage"],
                "subscription_tiers": config.get("subscription_tiers", []),
                "config_data": json.dumps(config.get("config", {}))
            }

            await self.update_redis_cache(redis_conn, feature_name, feature_data)

        return {
            "strategy": "gradual",
            "features_in_rollout": features_in_rollout,
            "total_features": len(features_in_rollout)
        }

    async def start_gradual_rollout(self, db_conn, feature_name: str, config: Dict, phases: List[Dict]) -> str:
        """Start gradual rollout process"""

        # Create rollout tracking record
        rollout_id = await db_conn.fetchval("""
            INSERT INTO feature_rollouts (
                feature_name, environment, service, rollout_phases,
                current_phase, status, created_at
            ) VALUES ($1, $2, $3, $4, 0, 'active', CURRENT_TIMESTAMP)
            RETURNING id
        """,
        feature_name, self.environment, self.service, json.dumps(phases)
        )

        # Create or update feature flag with initial percentage
        await db_conn.execute("""
            INSERT INTO feature_flags (
                feature_name, environment, service, enabled, rollout_percentage,
                subscription_tiers, config_data
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (feature_name, environment, service)
            DO UPDATE SET
                enabled = EXCLUDED.enabled,
                rollout_percentage = EXCLUDED.rollout_percentage,
                subscription_tiers = EXCLUDED.subscription_tiers,
                config_data = EXCLUDED.config_data,
                updated_at = CURRENT_TIMESTAMP
        """,
        feature_name,
        self.environment,
        self.service,
        True,
        phases[0]["percentage"],
        config.get("subscription_tiers", []),
        json.dumps(config.get("config", {}))
        )

        return str(rollout_id)

    async def update_redis_cache(self, redis_conn, feature_name: str, feature_data: Dict):
        """Update Redis cache with feature flag data"""

        cache_key = f"feature_flag:{self.environment}:{self.service}:{feature_name}"

        # Cache feature flag data
        await redis_conn.setex(
            cache_key,
            3600,  # 1 hour TTL
            json.dumps({
                "enabled": feature_data["enabled"],
                "rollout_percentage": feature_data["rollout_percentage"],
                "subscription_tiers": feature_data["subscription_tiers"],
                "config": json.loads(feature_data["config_data"]) if isinstance(feature_data["config_data"], str) else feature_data["config_data"]
            })
        )

        # Update feature list cache
        features_list_key = f"feature_flags:{self.environment}:{self.service}"
        await redis_conn.sadd(features_list_key, feature_name)
        await redis_conn.expire(features_list_key, 3600)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deploy Feature Flags')
    parser.add_argument('--database-url', required=True)
    parser.add_argument('--redis-url', required=True)
    parser.add_argument('--service', required=True)
    parser.add_argument('--environment', required=True)
    parser.add_argument('--rollout-strategy', default='gradual')
    parser.add_argument('--config-file', required=True)

    args = parser.parse_args()

    deployer = FeatureFlagDeployer(
        args.database_url, args.redis_url, args.service, args.environment
    )

    result = asyncio.run(deployer.deploy_feature_flags(args.config_file, args.rollout_strategy))

    print(f"✅ Feature flag deployment completed")
    print(f"✅ Strategy: {result['strategy']}")
    print(f"✅ Features processed: {result['total_features']}")
    print(f"✅ Duration: {result['deployment_duration']:.2f} seconds")
```

## 2. Subscription Management and Billing Integration

### Usage Monitoring and Quota Enforcement

```python
# scripts/sync-subscription-quotas.py
import asyncio
import asyncpg
import aiohttp
import os
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

class SubscriptionQuotaManager:
    def __init__(self, database_url: str, billing_api_key: str, environment: str):
        self.database_url = database_url
        self.billing_api_key = billing_api_key
        self.environment = environment
        self.logger = logging.getLogger(__name__)

        # Subscription tier configurations
        self.tier_config = {
            "free": {
                "api_quota_limit": 1000,
                "data_sources_limit": 3,
                "ai_tasks_per_day": 10,
                "storage_limit_mb": 100,
                "features": ["basic_analytics", "standard_support"]
            },
            "professional": {
                "api_quota_limit": 10000,
                "data_sources_limit": 25,
                "ai_tasks_per_day": 100,
                "storage_limit_mb": 1000,
                "features": [
                    "basic_analytics", "advanced_analytics", "custom_dashboards",
                    "priority_support", "api_access", "data_export"
                ]
            },
            "enterprise": {
                "api_quota_limit": 100000,
                "data_sources_limit": -1,  # Unlimited
                "ai_tasks_per_day": -1,    # Unlimited
                "storage_limit_mb": -1,    # Unlimited
                "features": [
                    "basic_analytics", "advanced_analytics", "custom_dashboards",
                    "priority_support", "api_access", "data_export",
                    "white_label", "sso_integration", "custom_integrations",
                    "dedicated_support", "sla_guarantee"
                ]
            }
        }

    async def sync_subscription_quotas(self) -> Dict[str, Any]:
        """Sync subscription quotas with billing system"""

        conn = await asyncpg.connect(self.database_url)

        try:
            sync_start = datetime.utcnow()

            # Get all users with their current subscription info
            users = await conn.fetch("""
                SELECT
                    id, email, username, subscription_tier,
                    api_quota_used, api_quota_limit,
                    billing_customer_id, subscription_status,
                    created_at, updated_at
                FROM users
                ORDER BY id
            """)

            sync_results = {
                "users_processed": 0,
                "quotas_updated": 0,
                "billing_synced": 0,
                "errors": [],
                "tier_distribution": {"free": 0, "professional": 0, "enterprise": 0}
            }

            # Process each user
            for user in users:
                try:
                    # Sync with billing system if customer ID exists
                    if user['billing_customer_id']:
                        billing_info = await self.fetch_billing_info(user['billing_customer_id'])
                        if billing_info:
                            await self.update_user_from_billing(conn, user, billing_info)
                            sync_results["billing_synced"] += 1

                    # Update quotas based on subscription tier
                    await self.update_user_quotas(conn, user)
                    sync_results["quotas_updated"] += 1

                    # Track tier distribution
                    tier = user['subscription_tier'] or 'free'
                    sync_results["tier_distribution"][tier] += 1

                    sync_results["users_processed"] += 1

                except Exception as e:
                    error_msg = f"Error processing user {user['id']}: {str(e)}"
                    self.logger.error(error_msg)
                    sync_results["errors"].append(error_msg)

            # Update subscription tier statistics
            await self.update_tier_statistics(conn, sync_results["tier_distribution"])

            # Enforce usage quotas
            quota_enforcement = await self.enforce_usage_quotas(conn)
            sync_results["quota_enforcement"] = quota_enforcement

            sync_end = datetime.utcnow()
            sync_results["sync_duration"] = (sync_end - sync_start).total_seconds()
            sync_results["sync_timestamp"] = sync_end.isoformat()

            return sync_results

        finally:
            await conn.close()

    async def fetch_billing_info(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Fetch billing information from external billing system"""

        billing_api_url = os.getenv("BILLING_API_URL", "https://billing-api.saascontrol.com")

        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    "Authorization": f"Bearer {self.billing_api_key}",
                    "Content-Type": "application/json"
                }

                async with session.get(
                    f"{billing_api_url}/customers/{customer_id}/subscription",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        self.logger.warning(f"Failed to fetch billing info for {customer_id}: {response.status}")
                        return None

            except Exception as e:
                self.logger.error(f"Error fetching billing info for {customer_id}: {e}")
                return None

    async def update_user_from_billing(self, conn, user: Dict, billing_info: Dict):
        """Update user information from billing system"""

        # Map billing status to subscription tier
        tier_mapping = {
            "free": "free",
            "pro": "professional",
            "premium": "professional",
            "enterprise": "enterprise",
            "business": "enterprise"
        }

        billing_tier = billing_info.get("plan_name", "free").lower()
        subscription_tier = tier_mapping.get(billing_tier, "free")
        subscription_status = billing_info.get("status", "active")

        # Update user subscription information
        await conn.execute("""
            UPDATE users
            SET
                subscription_tier = $1,
                subscription_status = $2,
                billing_period_start = $3,
                billing_period_end = $4,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $5
        """,
        subscription_tier,
        subscription_status,
        billing_info.get("period_start"),
        billing_info.get("period_end"),
        user['id']
        )

    async def update_user_quotas(self, conn, user: Dict):
        """Update user quotas based on subscription tier"""

        tier = user['subscription_tier'] or 'free'
        tier_limits = self.tier_config.get(tier, self.tier_config['free'])

        # Update quota limits
        await conn.execute("""
            UPDATE users
            SET
                api_quota_limit = $1,
                data_sources_limit = $2,
                ai_tasks_daily_limit = $3,
                storage_limit_mb = $4,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = $5
        """,
        tier_limits["api_quota_limit"],
        tier_limits["data_sources_limit"],
        tier_limits["ai_tasks_per_day"],
        tier_limits["storage_limit_mb"],
        user['id']
        )

        # Update user features
        await self.update_user_features(conn, user['id'], tier_limits["features"])

    async def update_user_features(self, conn, user_id: int, features: List[str]):
        """Update user feature access"""

        # Remove old features
        await conn.execute("DELETE FROM user_features WHERE user_id = $1", user_id)

        # Add new features
        for feature in features:
            await conn.execute("""
                INSERT INTO user_features (user_id, feature_name, enabled, granted_at)
                VALUES ($1, $2, true, CURRENT_TIMESTAMP)
            """, user_id, feature)

    async def enforce_usage_quotas(self, conn) -> Dict[str, Any]:
        """Enforce usage quotas and handle overages"""

        enforcement_results = {
            "users_over_quota": [],
            "api_calls_blocked": 0,
            "accounts_suspended": 0,
            "warnings_sent": 0
        }

        # Find users over their API quota
        over_quota_users = await conn.fetch("""
            SELECT
                id, username, email, subscription_tier,
                api_quota_used, api_quota_limit,
                (api_quota_used::float / api_quota_limit::float * 100) as usage_percentage
            FROM users
            WHERE api_quota_used > api_quota_limit
            AND subscription_status = 'active'
        """)

        for user in over_quota_users:
            user_info = {
                "user_id": user['id'],
                "username": user['username'],
                "tier": user['subscription_tier'],
                "usage_percentage": user['usage_percentage']
            }

            # Handle overage based on subscription tier
            if user['subscription_tier'] == 'free':
                # Suspend API access for free tier
                await conn.execute("""
                    UPDATE users
                    SET api_access_suspended = true, suspension_reason = 'quota_exceeded'
                    WHERE id = $1
                """, user['id'])
                enforcement_results["accounts_suspended"] += 1

            elif user['subscription_tier'] == 'professional':
                # Send warning for professional tier
                await self.send_quota_warning(user)
                enforcement_results["warnings_sent"] += 1

            # Enterprise tier gets unlimited, so no enforcement

            enforcement_results["users_over_quota"].append(user_info)

        # Check AI task daily limits
        today = datetime.utcnow().date()
        over_ai_limit_users = await conn.fetch("""
            SELECT
                u.id, u.username, u.subscription_tier, u.ai_tasks_daily_limit,
                COUNT(at.id) as tasks_today
            FROM users u
            LEFT JOIN ai_tasks at ON u.id = at.user_id
                AND DATE(at.created_at) = $1
            WHERE u.ai_tasks_daily_limit > 0
            GROUP BY u.id, u.username, u.subscription_tier, u.ai_tasks_daily_limit
            HAVING COUNT(at.id) > u.ai_tasks_daily_limit
        """, today)

        for user in over_ai_limit_users:
            # Suspend AI task creation
            await conn.execute("""
                UPDATE users
                SET ai_tasks_suspended = true, suspension_reason = 'daily_limit_exceeded'
                WHERE id = $1
            """, user['id'])

        return enforcement_results

    async def send_quota_warning(self, user: Dict):
        """Send quota warning email to user"""

        # This would integrate with your email service
        warning_data = {
            "user_id": user['id'],
            "email": user['email'],
            "usage_percentage": user['usage_percentage'],
            "tier": user['subscription_tier']
        }

        # Log warning (in real implementation, send actual email)
        self.logger.info(f"Quota warning sent to user {user['id']}: {warning_data}")

    async def update_tier_statistics(self, conn, tier_distribution: Dict[str, int]):
        """Update subscription tier statistics"""

        for tier, count in tier_distribution.items():
            await conn.execute("""
                INSERT INTO subscription_statistics (
                    environment, tier, user_count, recorded_at
                ) VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (environment, tier, DATE(recorded_at))
                DO UPDATE SET
                    user_count = EXCLUDED.user_count,
                    updated_at = CURRENT_TIMESTAMP
            """, self.environment, tier, count)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sync Subscription Quotas')
    parser.add_argument('--database-url', required=True)
    parser.add_argument('--billing-api-key', required=True)
    parser.add_argument('--environment', required=True)

    args = parser.parse_args()

    manager = SubscriptionQuotaManager(
        args.database_url, args.billing_api_key, args.environment
    )

    result = asyncio.run(manager.sync_subscription_quotas())

    print(f"✅ Subscription quota sync completed")
    print(f"✅ Users processed: {result['users_processed']}")
    print(f"✅ Quotas updated: {result['quotas_updated']}")
    print(f"✅ Billing synced: {result['billing_synced']}")
    print(f"✅ Tier distribution: {result['tier_distribution']}")

    if result['errors']:
        print(f"⚠️ Errors encountered: {len(result['errors'])}")
        for error in result['errors'][:5]:  # Show first 5 errors
            print(f"   {error}")
```

## 3. A/B Testing and Gradual Rollout

### A/B Testing Framework

```python
# scripts/ab-testing-manager.py
import asyncio
import asyncpg
import redis.asyncio as redis
import json
import hashlib
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

class ABTestingManager:
    def __init__(self, database_url: str, redis_url: str, environment: str):
        self.database_url = database_url
        self.redis_url = redis_url
        self.environment = environment
        self.logger = logging.getLogger(__name__)

    async def create_ab_test(self, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create new A/B test"""

        conn = await asyncpg.connect(self.database_url)
        redis_conn = await redis.from_url(self.redis_url)

        try:
            # Validate test configuration
            self.validate_test_config(test_config)

            # Create A/B test record
            test_id = await conn.fetchval("""
                INSERT INTO ab_tests (
                    test_name, description, feature_name,
                    variants, traffic_allocation, target_criteria,
                    start_date, end_date, environment, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'active')
                RETURNING id
            """,
            test_config["test_name"],
            test_config["description"],
            test_config["feature_name"],
            json.dumps(test_config["variants"]),
            json.dumps(test_config["traffic_allocation"]),
            json.dumps(test_config.get("target_criteria", {})),
            test_config["start_date"],
            test_config["end_date"],
            self.environment
            )

            # Set up Redis routing for the test
            await self.setup_redis_routing(redis_conn, test_id, test_config)

            # Initialize metrics tracking
            await self.initialize_test_metrics(conn, test_id, test_config["variants"])

            return {
                "test_id": test_id,
                "status": "created",
                "test_name": test_config["test_name"],
                "variants": test_config["variants"],
                "traffic_allocation": test_config["traffic_allocation"]
            }

        finally:
            await conn.close()
            await redis_conn.close()

    def validate_test_config(self, config: Dict[str, Any]):
        """Validate A/B test configuration"""

        required_fields = ["test_name", "feature_name", "variants", "traffic_allocation", "start_date", "end_date"]

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")

        # Validate traffic allocation sums to 100%
        total_allocation = sum(config["traffic_allocation"].values())
        if abs(total_allocation - 100) > 0.01:
            raise ValueError(f"Traffic allocation must sum to 100%, got {total_allocation}")

        # Validate variants exist in traffic allocation
        for variant in config["variants"]:
            if variant["name"] not in config["traffic_allocation"]:
                raise ValueError(f"Variant {variant['name']} missing from traffic allocation")

    async def setup_redis_routing(self, redis_conn, test_id: int, config: Dict[str, Any]):
        """Setup Redis routing for A/B test"""

        test_key = f"ab_test:{self.environment}:{config['feature_name']}"

        # Store test configuration
        test_data = {
            "test_id": test_id,
            "test_name": config["test_name"],
            "variants": config["variants"],
            "traffic_allocation": config["traffic_allocation"],
            "target_criteria": config.get("target_criteria", {}),
            "status": "active"
        }

        await redis_conn.setex(test_key, 86400, json.dumps(test_data))  # 24 hour TTL

    async def assign_user_to_variant(self, user_id: int, feature_name: str) -> Optional[Dict[str, Any]]:
        """Assign user to A/B test variant"""

        redis_conn = await redis.from_url(self.redis_url)

        try:
            test_key = f"ab_test:{self.environment}:{feature_name}"
            test_data = await redis_conn.get(test_key)

            if not test_data:
                return None

            test_config = json.loads(test_data)

            # Check if user meets target criteria
            if not await self.user_meets_criteria(user_id, test_config.get("target_criteria", {})):
                return None

            # Use consistent hashing for variant assignment
            variant = self.hash_user_to_variant(user_id, test_config["traffic_allocation"])

            # Find variant configuration
            variant_config = None
            for v in test_config["variants"]:
                if v["name"] == variant:
                    variant_config = v
                    break

            if not variant_config:
                return None

            # Record assignment
            await self.record_variant_assignment(user_id, test_config["test_id"], variant)

            return {
                "test_id": test_config["test_id"],
                "test_name": test_config["test_name"],
                "variant": variant,
                "config": variant_config.get("config", {})
            }

        finally:
            await redis_conn.close()

    def hash_user_to_variant(self, user_id: int, traffic_allocation: Dict[str, float]) -> str:
        """Use consistent hashing to assign user to variant"""

        # Create consistent hash based on user ID
        hash_input = f"{user_id}:{self.environment}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16) % 100

        # Find variant based on cumulative allocation
        cumulative = 0
        for variant, allocation in traffic_allocation.items():
            cumulative += allocation
            if hash_value < cumulative:
                return variant

        # Fallback to first variant
        return list(traffic_allocation.keys())[0]

    async def user_meets_criteria(self, user_id: int, criteria: Dict[str, Any]) -> bool:
        """Check if user meets targeting criteria"""

        if not criteria:
            return True

        conn = await asyncpg.connect(self.database_url)

        try:
            # Get user information
            user = await conn.fetchrow("""
                SELECT subscription_tier, created_at, last_login_at
                FROM users
                WHERE id = $1
            """, user_id)

            if not user:
                return False

            # Check subscription tier criteria
            if "subscription_tiers" in criteria:
                if user['subscription_tier'] not in criteria["subscription_tiers"]:
                    return False

            # Check user age criteria (days since registration)
            if "min_user_age_days" in criteria:
                user_age = (datetime.utcnow() - user['created_at']).days
                if user_age < criteria["min_user_age_days"]:
                    return False

            # Check activity criteria
            if "min_last_login_days" in criteria and user['last_login_at']:
                days_since_login = (datetime.utcnow() - user['last_login_at']).days
                if days_since_login > criteria["min_last_login_days"]:
                    return False

            return True

        finally:
            await conn.close()

    async def record_variant_assignment(self, user_id: int, test_id: int, variant: str):
        """Record user variant assignment"""

        conn = await asyncpg.connect(self.database_url)

        try:
            await conn.execute("""
                INSERT INTO ab_test_assignments (
                    test_id, user_id, variant, assigned_at
                ) VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (test_id, user_id)
                DO UPDATE SET
                    variant = EXCLUDED.variant,
                    assigned_at = EXCLUDED.assigned_at
            """, test_id, user_id, variant)

        finally:
            await conn.close()

    async def track_conversion(self, user_id: int, feature_name: str, event_type: str, event_data: Dict = None):
        """Track conversion event for A/B test"""

        conn = await asyncpg.connect(self.database_url)

        try:
            # Get user's current test assignment
            assignment = await conn.fetchrow("""
                SELECT ata.test_id, ata.variant, at.feature_name
                FROM ab_test_assignments ata
                JOIN ab_tests at ON ata.test_id = at.id
                WHERE ata.user_id = $1 AND at.feature_name = $2 AND at.status = 'active'
                ORDER BY ata.assigned_at DESC
                LIMIT 1
            """, user_id, feature_name)

            if assignment:
                # Record conversion event
                await conn.execute("""
                    INSERT INTO ab_test_events (
                        test_id, user_id, variant, event_type, event_data, recorded_at
                    ) VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                """,
                assignment['test_id'],
                user_id,
                assignment['variant'],
                event_type,
                json.dumps(event_data or {})
                )

        finally:
            await conn.close()

    async def get_test_results(self, test_id: int) -> Dict[str, Any]:
        """Get A/B test results and statistical analysis"""

        conn = await asyncpg.connect(self.database_url)

        try:
            # Get test information
            test_info = await conn.fetchrow("""
                SELECT test_name, feature_name, variants, start_date, end_date, status
                FROM ab_tests
                WHERE id = $1
            """, test_id)

            if not test_info:
                raise ValueError(f"Test {test_id} not found")

            # Get assignment statistics
            assignment_stats = await conn.fetch("""
                SELECT variant, COUNT(*) as assignments
                FROM ab_test_assignments
                WHERE test_id = $1
                GROUP BY variant
            """, test_id)

            # Get conversion statistics
            conversion_stats = await conn.fetch("""
                SELECT
                    variant,
                    event_type,
                    COUNT(*) as event_count,
                    COUNT(DISTINCT user_id) as unique_users
                FROM ab_test_events
                WHERE test_id = $1
                GROUP BY variant, event_type
            """, test_id)

            # Calculate conversion rates
            variant_results = {}
            for assignment in assignment_stats:
                variant = assignment['variant']
                assignments = assignment['assignments']

                conversions = sum(
                    conv['event_count'] for conv in conversion_stats
                    if conv['variant'] == variant and conv['event_type'] == 'conversion'
                )

                conversion_rate = (conversions / assignments * 100) if assignments > 0 else 0

                variant_results[variant] = {
                    "assignments": assignments,
                    "conversions": conversions,
                    "conversion_rate": conversion_rate
                }

            return {
                "test_id": test_id,
                "test_name": test_info['test_name'],
                "feature_name": test_info['feature_name'],
                "status": test_info['status'],
                "start_date": test_info['start_date'].isoformat(),
                "end_date": test_info['end_date'].isoformat(),
                "variant_results": variant_results,
                "statistical_significance": await self.calculate_statistical_significance(variant_results)
            }

        finally:
            await conn.close()

    async def calculate_statistical_significance(self, variant_results: Dict) -> Dict[str, Any]:
        """Calculate statistical significance of A/B test results"""

        variants = list(variant_results.keys())
        if len(variants) < 2:
            return {"significant": False, "confidence": 0}

        # Simple chi-square test implementation
        # In production, use proper statistical library like scipy
        control_variant = variants[0]
        test_variant = variants[1]

        control = variant_results[control_variant]
        test = variant_results[test_variant]

        # Calculate z-score for conversion rate difference
        p1 = control['conversion_rate'] / 100
        p2 = test['conversion_rate'] / 100
        n1 = control['assignments']
        n2 = test['assignments']

        if n1 < 30 or n2 < 30:  # Insufficient sample size
            return {"significant": False, "confidence": 0, "reason": "insufficient_sample_size"}

        # Pooled proportion
        p_pool = (control['conversions'] + test['conversions']) / (n1 + n2)

        # Standard error
        se = (p_pool * (1 - p_pool) * (1/n1 + 1/n2)) ** 0.5

        if se == 0:
            return {"significant": False, "confidence": 0, "reason": "zero_standard_error"}

        # Z-score
        z_score = abs(p2 - p1) / se

        # Approximate confidence level (simplified)
        if z_score > 2.58:  # 99% confidence
            confidence = 99
        elif z_score > 1.96:  # 95% confidence
            confidence = 95
        elif z_score > 1.64:  # 90% confidence
            confidence = 90
        else:
            confidence = 0

        return {
            "significant": confidence >= 95,
            "confidence": confidence,
            "z_score": z_score,
            "control_variant": control_variant,
            "test_variant": test_variant,
            "improvement": ((p2 - p1) / p1 * 100) if p1 > 0 else 0
        }

if __name__ == "__main__":
    # Example usage
    test_config = {
        "test_name": "New Dashboard Layout",
        "description": "Test new dashboard layout vs current",
        "feature_name": "dashboard_layout",
        "variants": [
            {"name": "control", "config": {"layout": "current"}},
            {"name": "new_layout", "config": {"layout": "grid_v2"}}
        ],
        "traffic_allocation": {"control": 50, "new_layout": 50},
        "target_criteria": {"subscription_tiers": ["professional", "enterprise"]},
        "start_date": datetime.utcnow(),
        "end_date": datetime.utcnow() + timedelta(days=30)
    }

    # This would be called from the workflow
    print("A/B Testing Manager ready for deployment")
```

## Summary

This commercial deployment workflow provides:

1. **Feature Flag Management**: Dynamic feature control with gradual rollout strategies
2. **Subscription Management**: Automated quota enforcement and billing integration
3. **A/B Testing Framework**: Statistical testing with conversion tracking
4. **Usage Monitoring**: Real-time quota enforcement and overage handling
5. **Billing Integration**: Automatic synchronization with external billing systems
6. **Commercial Analytics**: Tier distribution tracking and revenue optimization

The workflow ensures seamless commercial operations while maintaining the flexibility needed for rapid feature development and testing in the SaaS Control Deck platform.