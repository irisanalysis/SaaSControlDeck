# Data Quality Monitoring Workflows
# SaaS Control Deck - Automated Data Quality Assurance

## Overview

This document defines comprehensive data quality monitoring workflows for the SaaS Control Deck platform, providing real-time monitoring, automated alerting, and self-healing capabilities for our three-environment PostgreSQL infrastructure.

## Data Quality Framework

### Quality Dimensions
1. **Completeness**: Data presence and coverage
2. **Accuracy**: Data correctness and validity
3. **Consistency**: Data uniformity across systems
4. **Timeliness**: Data freshness and currency
5. **Integrity**: Referential and structural integrity
6. **Compliance**: Regulatory and business rule adherence

### Monitoring Scope
- **Database Health**: Connection pools, query performance, resource utilization
- **Data Integrity**: Foreign key violations, constraint violations, orphaned records
- **Business Logic**: AI task processing, user quota enforcement, billing accuracy
- **Security Compliance**: Audit trail completeness, access pattern anomalies

## 1. Real-Time Monitoring Infrastructure

### Continuous Data Quality Assessment

```yaml
# .github/workflows/data-quality-monitoring.yml
name: Data Quality Monitoring

on:
  schedule:
    # Run every 15 minutes for real-time monitoring
    - cron: '*/15 * * * *'
    # Comprehensive daily report at 6 AM UTC
    - cron: '0 6 * * *'

  workflow_dispatch:
    inputs:
      monitoring_scope:
        description: 'Monitoring scope'
        required: true
        default: 'all'
        type: choice
        options:
        - all
        - integrity
        - performance
        - compliance
        - business-rules

      environment:
        description: 'Target environment'
        required: true
        default: 'all'
        type: choice
        options:
        - all
        - development
        - staging
        - production

jobs:
  data-quality-assessment:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        environment: ${{ fromJSON(github.event.inputs.environment == 'all' && '["development", "staging", "production"]' || format('["{0}"]', github.event.inputs.environment)) }}
        service: [pro1, pro2]

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Setup Python Environment
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install monitoring dependencies
      run: |
        pip install asyncpg pandas numpy prometheus-client slack-sdk

    - name: Execute data quality checks
      env:
        DATABASE_URL: ${{ secrets[format('{0}_{1}_DATABASE_URL', upper(matrix.environment), upper(matrix.service))] }}
        PROMETHEUS_GATEWAY: ${{ secrets.PROMETHEUS_PUSHGATEWAY_URL }}
        SLACK_WEBHOOK: ${{ secrets.SLACK_DATA_QUALITY_WEBHOOK }}
      run: |
        python scripts/data-quality-monitor.py \
          --environment ${{ matrix.environment }} \
          --service ${{ matrix.service }} \
          --scope ${{ github.event.inputs.monitoring_scope || 'all' }} \
          --database-url $DATABASE_URL

    - name: Generate quality report
      if: github.event.schedule == '0 6 * * *'
      env:
        DATABASE_URL: ${{ secrets[format('{0}_{1}_DATABASE_URL', upper(matrix.environment), upper(matrix.service))] }}
      run: |
        python scripts/generate-quality-report.py \
          --environment ${{ matrix.environment }} \
          --service ${{ matrix.service }} \
          --report-type daily \
          --database-url $DATABASE_URL \
          --output-dir reports/data-quality/

    - name: Upload quality metrics to Prometheus
      env:
        PROMETHEUS_GATEWAY: ${{ secrets.PROMETHEUS_PUSHGATEWAY_URL }}
      run: |
        python scripts/push-quality-metrics.py \
          --environment ${{ matrix.environment }} \
          --service ${{ matrix.service }} \
          --metrics-file /tmp/quality-metrics.json \
          --prometheus-gateway $PROMETHEUS_GATEWAY

  anomaly-detection:
    needs: data-quality-assessment
    runs-on: ubuntu-latest

    strategy:
      matrix:
        environment: [development, staging, production]

    steps:
    - name: AI-powered anomaly detection
      env:
        DATABASE_URL: ${{ secrets[format('{0}_PRO1_DATABASE_URL', upper(matrix.environment))] }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        python scripts/ai-anomaly-detection.py \
          --environment ${{ matrix.environment }} \
          --database-url $DATABASE_URL \
          --lookback-hours 24

    - name: Trend analysis and prediction
      env:
        DATABASE_URL: ${{ secrets[format('{0}_PRO1_DATABASE_URL', upper(matrix.environment))] }}
      run: |
        python scripts/quality-trend-analysis.py \
          --environment ${{ matrix.environment }} \
          --database-url $DATABASE_URL \
          --forecast-days 7
```

### Comprehensive Data Quality Monitor

```python
# scripts/data-quality-monitor.py
import asyncio
import asyncpg
import json
import os
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging
import pandas as pd
import numpy as np
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

class DataQualityMonitor:
    def __init__(self, database_url: str, environment: str, service: str):
        self.database_url = database_url
        self.environment = environment
        self.service = service
        self.logger = logging.getLogger(__name__)

        # Prometheus metrics
        self.registry = CollectorRegistry()
        self.quality_score_gauge = Gauge('data_quality_score', 'Overall data quality score',
                                       ['environment', 'service', 'dimension'], registry=self.registry)
        self.error_count_gauge = Gauge('data_quality_errors', 'Data quality error count',
                                     ['environment', 'service', 'error_type'], registry=self.registry)

    async def execute_quality_assessment(self, scope: str) -> Dict[str, Any]:
        """Execute comprehensive data quality assessment"""

        conn = await asyncpg.connect(self.database_url)

        try:
            assessment_start = datetime.utcnow()

            # Initialize results
            results = {
                "environment": self.environment,
                "service": self.service,
                "assessment_timestamp": assessment_start.isoformat(),
                "scope": scope,
                "quality_dimensions": {},
                "alerts": [],
                "recommendations": []
            }

            # Execute quality checks based on scope
            if scope in ['all', 'integrity']:
                results["quality_dimensions"]["integrity"] = await self.assess_data_integrity(conn)

            if scope in ['all', 'completeness']:
                results["quality_dimensions"]["completeness"] = await self.assess_data_completeness(conn)

            if scope in ['all', 'accuracy']:
                results["quality_dimensions"]["accuracy"] = await self.assess_data_accuracy(conn)

            if scope in ['all', 'consistency']:
                results["quality_dimensions"]["consistency"] = await self.assess_data_consistency(conn)

            if scope in ['all', 'timeliness']:
                results["quality_dimensions"]["timeliness"] = await self.assess_data_timeliness(conn)

            if scope in ['all', 'performance']:
                results["quality_dimensions"]["performance"] = await self.assess_performance_quality(conn)

            if scope in ['all', 'compliance']:
                results["quality_dimensions"]["compliance"] = await self.assess_compliance_quality(conn)

            if scope in ['all', 'business-rules']:
                results["quality_dimensions"]["business_rules"] = await self.assess_business_rules(conn)

            # Calculate overall quality score
            results["overall_quality_score"] = self.calculate_overall_score(results["quality_dimensions"])

            # Generate alerts and recommendations
            results["alerts"] = await self.generate_quality_alerts(results["quality_dimensions"])
            results["recommendations"] = await self.generate_recommendations(results["quality_dimensions"])

            # Push metrics to Prometheus
            await self.push_quality_metrics(results)

            # Save results
            await self.save_quality_results(conn, results)

            assessment_end = datetime.utcnow()
            results["assessment_duration_seconds"] = (assessment_end - assessment_start).total_seconds()

            return results

        finally:
            await conn.close()

    async def assess_data_integrity(self, conn) -> Dict[str, Any]:
        """Assess data integrity including foreign keys, constraints, and orphaned records"""

        integrity_results = {
            "score": 0.0,
            "checks": {},
            "violations": [],
            "orphaned_records": {}
        }

        # Check foreign key violations
        fk_violations = await self.check_foreign_key_violations(conn)
        integrity_results["checks"]["foreign_key_violations"] = len(fk_violations)
        integrity_results["violations"].extend(fk_violations)

        # Check constraint violations
        constraint_violations = await self.check_constraint_violations(conn)
        integrity_results["checks"]["constraint_violations"] = len(constraint_violations)
        integrity_results["violations"].extend(constraint_violations)

        # Check for orphaned records
        orphaned_records = await self.detect_orphaned_records(conn)
        integrity_results["orphaned_records"] = orphaned_records

        # Check data type consistency
        type_consistency = await self.check_data_type_consistency(conn)
        integrity_results["checks"]["type_consistency_score"] = type_consistency

        # Calculate integrity score
        total_violations = len(fk_violations) + len(constraint_violations)
        orphaned_count = sum(orphaned_records.values())

        # Score calculation (0-1 scale)
        violation_penalty = min(total_violations * 0.1, 0.5)  # Max 0.5 penalty for violations
        orphaned_penalty = min(orphaned_count * 0.01, 0.3)   # Max 0.3 penalty for orphaned records
        type_penalty = (1.0 - type_consistency) * 0.2         # Max 0.2 penalty for type issues

        integrity_results["score"] = max(0.0, 1.0 - violation_penalty - orphaned_penalty - type_penalty)

        return integrity_results

    async def check_foreign_key_violations(self, conn) -> List[Dict[str, Any]]:
        """Check for foreign key constraint violations"""

        violations = []

        # Get all foreign key constraints
        fk_query = """
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                tc.constraint_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE constraint_type = 'FOREIGN KEY'
        """

        foreign_keys = await conn.fetch(fk_query)

        for fk in foreign_keys:
            # Check for violations
            violation_query = f"""
                SELECT COUNT(*) as violation_count
                FROM {fk['table_name']} t1
                LEFT JOIN {fk['foreign_table_name']} t2
                    ON t1.{fk['column_name']} = t2.{fk['foreign_column_name']}
                WHERE t1.{fk['column_name']} IS NOT NULL
                AND t2.{fk['foreign_column_name']} IS NULL
            """

            try:
                result = await conn.fetchrow(violation_query)
                if result['violation_count'] > 0:
                    violations.append({
                        "type": "foreign_key_violation",
                        "table": fk['table_name'],
                        "column": fk['column_name'],
                        "foreign_table": fk['foreign_table_name'],
                        "foreign_column": fk['foreign_column_name'],
                        "violation_count": result['violation_count'],
                        "constraint_name": fk['constraint_name']
                    })
            except Exception as e:
                self.logger.warning(f"Error checking FK constraint {fk['constraint_name']}: {e}")

        return violations

    async def assess_data_completeness(self, conn) -> Dict[str, Any]:
        """Assess data completeness including null values and missing required data"""

        completeness_results = {
            "score": 0.0,
            "table_completeness": {},
            "critical_missing_data": [],
            "null_analysis": {}
        }

        # Get all tables
        tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """)

        table_scores = []

        for table_row in tables:
            table_name = table_row['table_name']

            # Analyze null values in table
            null_analysis = await self.analyze_table_completeness(conn, table_name)
            completeness_results["table_completeness"][table_name] = null_analysis

            table_scores.append(null_analysis["completeness_score"])

            # Check for critical missing data
            critical_missing = await self.detect_critical_missing_data(conn, table_name)
            if critical_missing:
                completeness_results["critical_missing_data"].extend(critical_missing)

        # Calculate overall completeness score
        if table_scores:
            completeness_results["score"] = sum(table_scores) / len(table_scores)

        return completeness_results

    async def analyze_table_completeness(self, conn, table_name: str) -> Dict[str, Any]:
        """Analyze completeness for a specific table"""

        # Get table structure
        columns = await conn.fetch("""
            SELECT column_name, is_nullable, data_type
            FROM information_schema.columns
            WHERE table_name = $1
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """, table_name)

        if not columns:
            return {"completeness_score": 1.0, "column_analysis": {}}

        # Get total row count
        total_rows = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")

        if total_rows == 0:
            return {"completeness_score": 1.0, "column_analysis": {}, "total_rows": 0}

        column_analysis = {}
        column_scores = []

        for column in columns:
            column_name = column['column_name']
            is_nullable = column['is_nullable'] == 'YES'

            # Count null values
            null_count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NULL")

            null_percentage = (null_count / total_rows) * 100

            # Calculate column completeness score
            if is_nullable:
                # For nullable columns, some nulls are acceptable
                column_score = max(0.0, 1.0 - (null_percentage / 100) * 0.5)
            else:
                # For non-nullable columns, any nulls are problematic
                column_score = max(0.0, 1.0 - (null_percentage / 100))

            column_analysis[column_name] = {
                "null_count": null_count,
                "null_percentage": null_percentage,
                "is_nullable": is_nullable,
                "completeness_score": column_score
            }

            column_scores.append(column_score)

        # Calculate table completeness score
        table_score = sum(column_scores) / len(column_scores) if column_scores else 1.0

        return {
            "completeness_score": table_score,
            "column_analysis": column_analysis,
            "total_rows": total_rows
        }

    async def assess_data_accuracy(self, conn) -> Dict[str, Any]:
        """Assess data accuracy using business rules and data validation"""

        accuracy_results = {
            "score": 0.0,
            "validation_results": {},
            "accuracy_issues": [],
            "outlier_analysis": {}
        }

        # Email validation
        email_accuracy = await self.validate_email_accuracy(conn)
        accuracy_results["validation_results"]["email_validation"] = email_accuracy

        # Phone number validation
        phone_accuracy = await self.validate_phone_accuracy(conn)
        accuracy_results["validation_results"]["phone_validation"] = phone_accuracy

        # AI task accuracy validation
        ai_accuracy = await self.validate_ai_task_accuracy(conn)
        accuracy_results["validation_results"]["ai_task_validation"] = ai_accuracy

        # Numerical data outlier detection
        outlier_analysis = await self.detect_numerical_outliers(conn)
        accuracy_results["outlier_analysis"] = outlier_analysis

        # Calculate overall accuracy score
        validation_scores = [result["accuracy_score"] for result in accuracy_results["validation_results"].values()]
        if validation_scores:
            accuracy_results["score"] = sum(validation_scores) / len(validation_scores)

        return accuracy_results

    async def validate_email_accuracy(self, conn) -> Dict[str, Any]:
        """Validate email address accuracy"""

        email_query = """
            SELECT
                COUNT(*) as total_emails,
                COUNT(CASE WHEN email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN 1 END) as valid_emails
            FROM users
            WHERE email IS NOT NULL
        """

        result = await conn.fetchrow(email_query)

        if result['total_emails'] == 0:
            return {"accuracy_score": 1.0, "total_emails": 0, "valid_emails": 0}

        accuracy_score = result['valid_emails'] / result['total_emails']

        return {
            "accuracy_score": accuracy_score,
            "total_emails": result['total_emails'],
            "valid_emails": result['valid_emails'],
            "invalid_emails": result['total_emails'] - result['valid_emails']
        }

    async def assess_performance_quality(self, conn) -> Dict[str, Any]:
        """Assess database performance quality"""

        performance_results = {
            "score": 0.0,
            "query_performance": {},
            "connection_health": {},
            "resource_utilization": {}
        }

        # Query performance analysis
        slow_queries = await conn.fetch("""
            SELECT
                query,
                calls,
                total_time,
                mean_time,
                min_time,
                max_time
            FROM pg_stat_statements
            WHERE mean_time > 1000  -- Queries slower than 1 second
            ORDER BY mean_time DESC
            LIMIT 10
        """)

        performance_results["query_performance"] = {
            "slow_query_count": len(slow_queries),
            "slowest_queries": [dict(q) for q in slow_queries]
        }

        # Connection health
        connection_stats = await conn.fetchrow("""
            SELECT
                COUNT(*) as total_connections,
                COUNT(CASE WHEN state = 'active' THEN 1 END) as active_connections,
                COUNT(CASE WHEN state = 'idle' THEN 1 END) as idle_connections,
                COUNT(CASE WHEN state = 'idle in transaction' THEN 1 END) as idle_in_transaction
            FROM pg_stat_activity
        """)

        performance_results["connection_health"] = dict(connection_stats)

        # Database size and growth
        db_stats = await conn.fetchrow("""
            SELECT
                pg_database_size(current_database()) as database_size_bytes,
                numbackends as backends,
                xact_commit as transactions_committed,
                xact_rollback as transactions_rolled_back,
                blks_read as blocks_read,
                blks_hit as blocks_hit
            FROM pg_stat_database
            WHERE datname = current_database()
        """)

        performance_results["resource_utilization"] = dict(db_stats)

        # Calculate performance score
        performance_score = 1.0

        # Penalize for too many slow queries
        slow_query_penalty = min(len(slow_queries) * 0.05, 0.3)
        performance_score -= slow_query_penalty

        # Penalize for high connection usage (assuming max 150 connections)
        max_connections = 150
        connection_usage = connection_stats['total_connections'] / max_connections
        if connection_usage > 0.8:
            performance_score -= (connection_usage - 0.8) * 0.5

        # Cache hit ratio penalty
        if db_stats['blks_read'] + db_stats['blks_hit'] > 0:
            cache_hit_ratio = db_stats['blks_hit'] / (db_stats['blks_read'] + db_stats['blks_hit'])
            if cache_hit_ratio < 0.9:
                performance_score -= (0.9 - cache_hit_ratio) * 0.3

        performance_results["score"] = max(0.0, performance_score)

        return performance_results

    async def assess_business_rules(self, conn) -> Dict[str, Any]:
        """Assess business rule compliance"""

        business_results = {
            "score": 0.0,
            "rule_violations": [],
            "quota_compliance": {},
            "billing_accuracy": {}
        }

        # User quota compliance
        quota_violations = await conn.fetch("""
            SELECT
                id,
                username,
                subscription_tier,
                api_quota_used,
                api_quota_limit,
                (api_quota_used::float / api_quota_limit::float) as usage_ratio
            FROM users
            WHERE api_quota_used > api_quota_limit
        """)

        business_results["quota_compliance"] = {
            "violations": len(quota_violations),
            "violating_users": [dict(v) for v in quota_violations]
        }

        # AI task business rules
        ai_task_violations = await self.check_ai_task_business_rules(conn)
        business_results["rule_violations"].extend(ai_task_violations)

        # Subscription tier compliance
        tier_violations = await self.check_subscription_tier_compliance(conn)
        business_results["rule_violations"].extend(tier_violations)

        # Calculate business rules score
        total_violations = len(quota_violations) + len(ai_task_violations) + len(tier_violations)
        violation_penalty = min(total_violations * 0.1, 0.8)
        business_results["score"] = max(0.0, 1.0 - violation_penalty)

        return business_results

    async def check_ai_task_business_rules(self, conn) -> List[Dict[str, Any]]:
        """Check AI task business rule compliance"""

        violations = []

        # Check for tasks without proper project association
        orphaned_tasks = await conn.fetch("""
            SELECT id, task_type, created_at
            FROM ai_tasks
            WHERE project_id IS NULL
            OR project_id NOT IN (SELECT id FROM projects)
        """)

        for task in orphaned_tasks:
            violations.append({
                "type": "orphaned_ai_task",
                "task_id": task['id'],
                "task_type": task['task_type'],
                "created_at": task['created_at'].isoformat()
            })

        # Check for tasks with invalid processing times
        invalid_times = await conn.fetch("""
            SELECT id, task_type, processing_time_ms, status
            FROM ai_tasks
            WHERE status = 'completed'
            AND (processing_time_ms IS NULL OR processing_time_ms < 0 OR processing_time_ms > 600000)
        """)

        for task in invalid_times:
            violations.append({
                "type": "invalid_processing_time",
                "task_id": task['id'],
                "task_type": task['task_type'],
                "processing_time_ms": task['processing_time_ms'],
                "status": task['status']
            })

        return violations

    def calculate_overall_score(self, quality_dimensions: Dict[str, Dict]) -> float:
        """Calculate overall quality score from individual dimensions"""

        # Weights for different quality dimensions
        weights = {
            "integrity": 0.25,
            "completeness": 0.20,
            "accuracy": 0.20,
            "consistency": 0.15,
            "timeliness": 0.10,
            "performance": 0.05,
            "compliance": 0.03,
            "business_rules": 0.02
        }

        weighted_score = 0.0
        total_weight = 0.0

        for dimension, weight in weights.items():
            if dimension in quality_dimensions:
                score = quality_dimensions[dimension].get("score", 0.0)
                weighted_score += score * weight
                total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0

    async def generate_quality_alerts(self, quality_dimensions: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Generate alerts based on quality assessment results"""

        alerts = []

        # Critical thresholds
        critical_threshold = 0.7
        warning_threshold = 0.85

        for dimension, results in quality_dimensions.items():
            score = results.get("score", 1.0)

            if score < critical_threshold:
                alerts.append({
                    "severity": "critical",
                    "dimension": dimension,
                    "score": score,
                    "message": f"Data quality {dimension} score ({score:.2f}) is below critical threshold ({critical_threshold})",
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif score < warning_threshold:
                alerts.append({
                    "severity": "warning",
                    "dimension": dimension,
                    "score": score,
                    "message": f"Data quality {dimension} score ({score:.2f}) is below warning threshold ({warning_threshold})",
                    "timestamp": datetime.utcnow().isoformat()
                })

        return alerts

    async def push_quality_metrics(self, results: Dict[str, Any]):
        """Push quality metrics to Prometheus"""

        # Push dimension scores
        for dimension, dimension_results in results["quality_dimensions"].items():
            score = dimension_results.get("score", 0.0)
            self.quality_score_gauge.labels(
                environment=self.environment,
                service=self.service,
                dimension=dimension
            ).set(score)

        # Push error counts
        for alert in results["alerts"]:
            self.error_count_gauge.labels(
                environment=self.environment,
                service=self.service,
                error_type=alert["dimension"]
            ).inc()

        # Push to Prometheus Gateway
        prometheus_gateway = os.getenv("PROMETHEUS_GATEWAY")
        if prometheus_gateway:
            try:
                push_to_gateway(
                    prometheus_gateway,
                    job=f'data_quality_{self.environment}_{self.service}',
                    registry=self.registry
                )
            except Exception as e:
                self.logger.error(f"Failed to push metrics to Prometheus: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Data Quality Monitor')
    parser.add_argument('--environment', required=True)
    parser.add_argument('--service', required=True)
    parser.add_argument('--scope', default='all')
    parser.add_argument('--database-url', required=True)

    args = parser.parse_args()

    monitor = DataQualityMonitor(args.database_url, args.environment, args.service)
    result = asyncio.run(monitor.execute_quality_assessment(args.scope))

    # Save results to file for GitHub Actions artifact
    with open('/tmp/quality-metrics.json', 'w') as f:
        json.dump(result, f, indent=2)

    print(f"✅ Data quality assessment completed for {args.environment}-{args.service}")
    print(f"✅ Overall quality score: {result['overall_quality_score']:.3f}")
    print(f"✅ Alerts generated: {len(result['alerts'])}")

    # Exit with error code if quality is below critical threshold
    if result['overall_quality_score'] < 0.7:
        print("❌ Data quality below critical threshold")
        exit(1)