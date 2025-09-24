# Monitoring and Alerting Configuration
# SaaS Control Deck - Comprehensive Database Monitoring and Alerting System

## Overview

This document defines the comprehensive monitoring and alerting configuration for the SaaS Control Deck platform's database CI/CD workflows, providing real-time visibility, proactive alerting, and automated remediation capabilities across our three-environment PostgreSQL infrastructure.

## Monitoring Architecture

### Core Components
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert routing and management
- **PagerDuty**: Incident management and escalation
- **Slack**: Real-time team notifications
- **Custom Python Agents**: Database-specific monitoring

### Monitoring Scope
- **Database Health**: Connection pools, query performance, resource utilization
- **CI/CD Pipeline Health**: Migration success rates, deployment times, rollback frequency
- **Data Quality**: Integrity scores, completeness metrics, business rule compliance
- **Commercial Metrics**: Subscription health, quota utilization, revenue impact

## 1. Prometheus Configuration

### Database Metrics Collection

```yaml
# monitoring/prometheus/database-monitoring.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "database-alerts.yml"
  - "cicd-alerts.yml"
  - "quality-alerts.yml"
  - "commercial-alerts.yml"

scrape_configs:
  # Database Exporters
  - job_name: 'postgres-exporter-dev-pro1'
    static_configs:
      - targets: ['47.79.87.199:9187']
    params:
      environment: ['development']
      service: ['pro1']
    scrape_interval: 30s
    metrics_path: /metrics
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: postgres-exporter:9187

  - job_name: 'postgres-exporter-dev-pro2'
    static_configs:
      - targets: ['47.79.87.199:9187']
    params:
      environment: ['development']
      service: ['pro2']
    scrape_interval: 30s

  - job_name: 'postgres-exporter-staging-pro1'
    static_configs:
      - targets: ['47.79.87.199:9187']
    params:
      environment: ['staging']
      service: ['pro1']
    scrape_interval: 30s

  - job_name: 'postgres-exporter-staging-pro2'
    static_configs:
      - targets: ['47.79.87.199:9187']
    params:
      environment: ['staging']
      service: ['pro2']
    scrape_interval: 30s

  - job_name: 'postgres-exporter-prod-pro1'
    static_configs:
      - targets: ['47.79.87.199:9187']
    params:
      environment: ['production']
      service: ['pro1']
    scrape_interval: 15s  # More frequent for production

  - job_name: 'postgres-exporter-prod-pro2'
    static_configs:
      - targets: ['47.79.87.199:9187']
    params:
      environment: ['production']
      service: ['pro2']
    scrape_interval: 15s

  # Custom Data Quality Metrics
  - job_name: 'data-quality-pushgateway'
    static_configs:
      - targets: ['pushgateway:9091']
    honor_labels: true
    scrape_interval: 60s

  # GitHub Actions CI/CD Metrics
  - job_name: 'github-actions-exporter'
    static_configs:
      - targets: ['github-exporter:9090']
    scrape_interval: 300s  # 5 minutes

  # Commercial Metrics
  - job_name: 'commercial-metrics-pushgateway'
    static_configs:
      - targets: ['pushgateway:9091']
    honor_labels: true
    scrape_interval: 300s
    metrics_path: /metrics/commercial

  # Application Health Endpoints
  - job_name: 'backend-health-dev'
    static_configs:
      - targets: ['localhost:8000', 'localhost:8001', 'localhost:8002']
      - targets: ['localhost:8100', 'localhost:8101', 'localhost:8102']
    scrape_interval: 30s
    metrics_path: /metrics

  - job_name: 'backend-health-staging'
    static_configs:
      - targets: ['staging-api-gateway:8000', 'staging-data-service:8001', 'staging-ai-service:8002']
      - targets: ['staging-api-gateway:8100', 'staging-data-service:8101', 'staging-ai-service:8102']
    scrape_interval: 30s
    metrics_path: /metrics

  - job_name: 'backend-health-production'
    static_configs:
      - targets: ['prod-api-gateway:8000', 'prod-data-service:8001', 'prod-ai-service:8002']
      - targets: ['prod-api-gateway:8100', 'prod-data-service:8101', 'prod-ai-service:8102']
    scrape_interval: 15s
    metrics_path: /metrics

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Database Alert Rules

```yaml
# monitoring/prometheus/database-alerts.yml
groups:
  - name: database_health
    rules:
    # Connection Pool Alerts
    - alert: DatabaseConnectionsHigh
      expr: |
        (
          pg_stat_database_numbackends{datname!~"template.*|postgres"}
          / on(instance) pg_settings_max_connections
        ) * 100 > 80
      for: 5m
      labels:
        severity: warning
        team: backend
      annotations:
        summary: "High database connection usage on {{ $labels.instance }}"
        description: "Database {{ $labels.datname }} on {{ $labels.instance }} is using {{ $value }}% of available connections"

    - alert: DatabaseConnectionsCritical
      expr: |
        (
          pg_stat_database_numbackends{datname!~"template.*|postgres"}
          / on(instance) pg_settings_max_connections
        ) * 100 > 95
      for: 2m
      labels:
        severity: critical
        team: backend
      annotations:
        summary: "Critical database connection usage on {{ $labels.instance }}"
        description: "Database {{ $labels.datname }} on {{ $labels.instance }} is using {{ $value }}% of available connections"

    # Query Performance Alerts
    - alert: SlowQueriesHigh
      expr: |
        rate(pg_stat_statements_mean_time_ms[5m]) > 5000
      for: 10m
      labels:
        severity: warning
        team: backend
      annotations:
        summary: "High number of slow queries on {{ $labels.instance }}"
        description: "Average query time on {{ $labels.instance }} is {{ $value }}ms"

    - alert: DatabaseLockWaits
      expr: |
        pg_locks_count{mode="accessexclusivelock"} > 5
      for: 5m
      labels:
        severity: warning
        team: backend
      annotations:
        summary: "High number of lock waits on {{ $labels.instance }}"
        description: "{{ $value }} lock waits detected on {{ $labels.instance }}"

    # Replication Lag (if applicable)
    - alert: ReplicationLagHigh
      expr: |
        pg_replication_lag_seconds > 60
      for: 5m
      labels:
        severity: warning
        team: backend
      annotations:
        summary: "High replication lag on {{ $labels.instance }}"
        description: "Replication lag is {{ $value }} seconds on {{ $labels.instance }}"

    # Cache Hit Ratio
    - alert: CacheHitRatioLow
      expr: |
        (
          rate(pg_stat_database_blks_hit[5m])
          / (rate(pg_stat_database_blks_hit[5m]) + rate(pg_stat_database_blks_read[5m]))
        ) * 100 < 85
      for: 15m
      labels:
        severity: warning
        team: backend
      annotations:
        summary: "Low cache hit ratio on {{ $labels.instance }}"
        description: "Cache hit ratio is {{ $value }}% on database {{ $labels.datname }}"

  - name: data_quality_alerts
    rules:
    # Data Quality Score Alerts
    - alert: DataQualityScoreLow
      expr: |
        data_quality_score < 0.85
      for: 10m
      labels:
        severity: warning
        team: data
      annotations:
        summary: "Low data quality score in {{ $labels.environment }}/{{ $labels.service }}"
        description: "Data quality score for {{ $labels.dimension }} is {{ $value }} in {{ $labels.environment }}"

    - alert: DataQualityScoreCritical
      expr: |
        data_quality_score < 0.7
      for: 5m
      labels:
        severity: critical
        team: data
      annotations:
        summary: "Critical data quality score in {{ $labels.environment }}/{{ $labels.service }}"
        description: "Data quality score for {{ $labels.dimension }} is {{ $value }} in {{ $labels.environment }}"

    # Data Integrity Alerts
    - alert: ForeignKeyViolations
      expr: |
        data_quality_errors{error_type="foreign_key_violation"} > 0
      for: 1m
      labels:
        severity: critical
        team: data
      annotations:
        summary: "Foreign key violations detected in {{ $labels.environment }}"
        description: "{{ $value }} foreign key violations in {{ $labels.environment }}/{{ $labels.service }}"

    # Business Rule Violations
    - alert: BusinessRuleViolations
      expr: |
        data_quality_errors{error_type="business_rule_violation"} > 10
      for: 5m
      labels:
        severity: warning
        team: business
      annotations:
        summary: "Business rule violations in {{ $labels.environment }}"
        description: "{{ $value }} business rule violations in {{ $labels.environment }}"

  - name: cicd_pipeline_alerts
    rules:
    # Migration Failure Alerts
    - alert: DatabaseMigrationFailed
      expr: |
        github_workflow_run_conclusion{workflow_name=~".*migration.*", conclusion="failure"} > 0
      for: 1m
      labels:
        severity: critical
        team: devops
      annotations:
        summary: "Database migration failed"
        description: "Migration workflow {{ $labels.workflow_name }} failed in {{ $labels.repository }}"

    # Deployment Time Alerts
    - alert: DeploymentTimeTooLong
      expr: |
        github_workflow_run_duration_seconds{workflow_name=~".*deployment.*"} > 1800
      for: 1m
      labels:
        severity: warning
        team: devops
      annotations:
        summary: "Long deployment time detected"
        description: "Deployment {{ $labels.workflow_name }} took {{ $value }} seconds"

    # Sync Failure Alerts
    - alert: DataSyncFailed
      expr: |
        github_workflow_run_conclusion{workflow_name=~".*sync.*", conclusion="failure"} > 0
      for: 1m
      labels:
        severity: critical
        team: data
      annotations:
        summary: "Data synchronization failed"
        description: "Data sync workflow {{ $labels.workflow_name }} failed"

  - name: commercial_alerts
    rules:
    # Quota Utilization Alerts
    - alert: QuotaUtilizationHigh
      expr: |
        (subscription_quota_used / subscription_quota_limit) * 100 > 90
      for: 15m
      labels:
        severity: warning
        team: commercial
      annotations:
        summary: "High quota utilization for {{ $labels.subscription_tier }}"
        description: "Quota utilization is {{ $value }}% for {{ $labels.subscription_tier }} users"

    # Revenue Impact Alerts
    - alert: ConversionRateDropped
      expr: |
        rate(subscription_conversions[1h]) < 0.02
      for: 30m
      labels:
        severity: warning
        team: commercial
      annotations:
        summary: "Conversion rate below threshold"
        description: "Subscription conversion rate is {{ $value }}% over the last hour"

    # Feature Usage Alerts
    - alert: FeatureUsageDropped
      expr: |
        rate(feature_usage_total[1h]) < 0.5 * rate(feature_usage_total[24h] offset 24h)
      for: 30m
      labels:
        severity: warning
        team: product
      annotations:
        summary: "Feature usage dropped significantly"
        description: "Usage of {{ $labels.feature_name }} dropped by {{ $value }}% compared to yesterday"
```

## 2. AlertManager Configuration

### Alert Routing and Management

```yaml
# monitoring/alertmanager/alertmanager.yml
global:
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@saascontrol.com'

templates:
  - '/etc/alertmanager/templates/*.tmpl'

route:
  group_by: ['alertname', 'environment', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    # Critical Production Alerts
    - match:
        severity: critical
        environment: production
      receiver: 'production-critical'
      group_wait: 5s
      repeat_interval: 5m

    # Database Team Alerts
    - match:
        team: backend
      receiver: 'database-team'
      routes:
        - match:
            severity: critical
          receiver: 'database-team-critical'

    # Data Quality Team Alerts
    - match:
        team: data
      receiver: 'data-quality-team'
      routes:
        - match:
            severity: critical
          receiver: 'data-quality-critical'

    # DevOps Team Alerts
    - match:
        team: devops
      receiver: 'devops-team'
      routes:
        - match:
            alertname: DatabaseMigrationFailed
          receiver: 'migration-failure'

    # Commercial Team Alerts
    - match:
        team: commercial
      receiver: 'commercial-team'

    # Development Environment (Lower Priority)
    - match:
        environment: development
      receiver: 'development-alerts'
      group_wait: 30s
      repeat_interval: 6h

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts-general'
        title: 'SaaS Control Deck Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

  - name: 'production-critical'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
        description: '{{ .GroupLabels.alertname }} - {{ .CommonAnnotations.summary }}'
    slack_configs:
      - channel: '#alerts-critical'
        title: '🚨 CRITICAL PRODUCTION ALERT'
        text: |
          {{ range .Alerts }}
          *Alert:* {{ .Annotations.summary }}
          *Environment:* {{ .Labels.environment }}
          *Service:* {{ .Labels.service }}
          *Description:* {{ .Annotations.description }}
          {{ end }}
        send_resolved: true

  - name: 'database-team'
    slack_configs:
      - channel: '#database-alerts'
        title: 'Database Alert - {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          *Alert:* {{ .Annotations.summary }}
          *Environment:* {{ .Labels.environment }}
          *Instance:* {{ .Labels.instance }}
          *Description:* {{ .Annotations.description }}
          {{ end }}

  - name: 'database-team-critical'
    pagerduty_configs:
      - service_key: 'DATABASE_TEAM_PAGERDUTY_KEY'
        description: 'Critical Database Alert: {{ .CommonAnnotations.summary }}'
    slack_configs:
      - channel: '#database-critical'
        title: '🔴 Critical Database Alert'
        text: |
          {{ range .Alerts }}
          *CRITICAL DATABASE ISSUE*
          *Alert:* {{ .Annotations.summary }}
          *Environment:* {{ .Labels.environment }}
          *Instance:* {{ .Labels.instance }}
          *Description:* {{ .Annotations.description }}
          {{ end }}

  - name: 'data-quality-team'
    slack_configs:
      - channel: '#data-quality'
        title: 'Data Quality Alert'
        text: |
          {{ range .Alerts }}
          *Quality Issue:* {{ .Annotations.summary }}
          *Environment:* {{ .Labels.environment }}
          *Dimension:* {{ .Labels.dimension }}
          *Score:* {{ .Labels.value }}
          {{ end }}

  - name: 'data-quality-critical'
    email_configs:
      - to: 'data-team@saascontrol.com'
        subject: 'CRITICAL: Data Quality Issue'
        body: |
          Critical data quality alert:
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Environment: {{ .Labels.environment }}
          Description: {{ .Annotations.description }}
          {{ end }}
    slack_configs:
      - channel: '#data-quality-critical'
        title: '🔴 Critical Data Quality Alert'
        text: |
          {{ range .Alerts }}
          *CRITICAL DATA QUALITY ISSUE*
          *Alert:* {{ .Annotations.summary }}
          *Environment:* {{ .Labels.environment }}
          *Dimension:* {{ .Labels.dimension }}
          {{ end }}

  - name: 'devops-team'
    slack_configs:
      - channel: '#devops'
        title: 'DevOps Alert'
        text: |
          {{ range .Alerts }}
          *CI/CD Alert:* {{ .Annotations.summary }}
          *Workflow:* {{ .Labels.workflow_name }}
          *Repository:* {{ .Labels.repository }}
          {{ end }}

  - name: 'migration-failure'
    pagerduty_configs:
      - service_key: 'MIGRATION_PAGERDUTY_KEY'
        description: 'Database Migration Failed: {{ .CommonAnnotations.summary }}'
    slack_configs:
      - channel: '#database-migrations'
        title: '🚨 Database Migration Failed'
        text: |
          {{ range .Alerts }}
          *MIGRATION FAILURE*
          *Workflow:* {{ .Labels.workflow_name }}
          *Repository:* {{ .Labels.repository }}
          *Environment:* {{ .Labels.environment }}

          Please check the GitHub Actions workflow immediately.
          {{ end }}

  - name: 'commercial-team'
    slack_configs:
      - channel: '#commercial-alerts'
        title: 'Commercial Alert'
        text: |
          {{ range .Alerts }}
          *Commercial Issue:* {{ .Annotations.summary }}
          *Metric:* {{ .Labels.alertname }}
          *Value:* {{ .Labels.value }}
          {{ end }}

  - name: 'development-alerts'
    slack_configs:
      - channel: '#dev-alerts'
        title: 'Development Environment Alert'
        text: |
          {{ range .Alerts }}
          Development alert: {{ .Annotations.summary }}
          {{ end }}

inhibit_rules:
  # Inhibit warning alerts when critical alerts are firing
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['environment', 'service', 'instance']

  # Inhibit database connection warnings when connection critical is firing
  - source_match:
      alertname: 'DatabaseConnectionsCritical'
    target_match:
      alertname: 'DatabaseConnectionsHigh'
    equal: ['instance']
```

## 3. Grafana Dashboard Configuration

### Database Monitoring Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "SaaS Control Deck - Database Monitoring",
    "tags": ["database", "postgresql", "monitoring"],
    "style": "dark",
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Database Connections by Environment",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends{datname!~\"template.*|postgres\"}",
            "legendFormat": "{{environment}}-{{service}} - {{datname}}",
            "refId": "A"
          }
        ],
        "yAxes": [
          {
            "label": "Connections",
            "min": 0
          }
        ],
        "alert": {
          "conditions": [
            {
              "query": {
                "queryType": "",
                "refId": "A"
              },
              "reducer": {
                "type": "last",
                "params": []
              },
              "evaluator": {
                "params": [80],
                "type": "gt"
              }
            }
          ],
          "executionErrorState": "alerting",
          "for": "5m",
          "frequency": "10s",
          "handler": 1,
          "name": "Database Connections High",
          "noDataState": "no_data",
          "notifications": []
        }
      },
      {
        "id": 2,
        "title": "Query Performance by Environment",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(pg_stat_statements_total_time_ms[5m]) / rate(pg_stat_statements_calls[5m])",
            "legendFormat": "{{environment}}-{{service}} - Avg Query Time",
            "refId": "A"
          }
        ],
        "yAxes": [
          {
            "label": "Milliseconds",
            "min": 0
          }
        ]
      },
      {
        "id": 3,
        "title": "Data Quality Scores",
        "type": "stat",
        "targets": [
          {
            "expr": "data_quality_score",
            "legendFormat": "{{environment}}-{{service}}-{{dimension}}",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {
              "mode": "thresholds"
            },
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 0.7},
                {"color": "green", "value": 0.85}
              ]
            },
            "min": 0,
            "max": 1
          }
        }
      },
      {
        "id": 4,
        "title": "CI/CD Pipeline Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(github_workflow_run_conclusion{conclusion=\"success\"}[1d]) / rate(github_workflow_run_conclusion[1d]) * 100",
            "legendFormat": "{{workflow_name}}",
            "refId": "A"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 85},
                {"color": "green", "value": 95}
              ]
            }
          }
        }
      },
      {
        "id": 5,
        "title": "Commercial Metrics",
        "type": "row",
        "panels": [
          {
            "id": 51,
            "title": "Subscription Conversion Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(subscription_conversions[1h]) * 100",
                "legendFormat": "{{subscription_tier}}",
                "refId": "A"
              }
            ]
          },
          {
            "id": 52,
            "title": "Quota Utilization",
            "type": "graph",
            "targets": [
              {
                "expr": "(subscription_quota_used / subscription_quota_limit) * 100",
                "legendFormat": "{{subscription_tier}} - {{environment}}",
                "refId": "A"
              }
            ]
          }
        ]
      }
    ],
    "time": {
      "from": "now-6h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

## 4. Custom Monitoring Scripts

### Database Health Monitor

```python
# scripts/monitoring/database-health-monitor.py
import asyncio
import asyncpg
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import logging
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

class DatabaseHealthMonitor:
    def __init__(self, database_url: str, environment: str, service: str):
        self.database_url = database_url
        self.environment = environment
        self.service = service
        self.logger = logging.getLogger(__name__)

        # Prometheus metrics
        self.registry = CollectorRegistry()
        self.connection_gauge = Gauge('database_connections_active',
                                    'Active database connections',
                                    ['environment', 'service', 'database'],
                                    registry=self.registry)
        self.query_time_gauge = Gauge('database_avg_query_time_ms',
                                    'Average query time in milliseconds',
                                    ['environment', 'service'],
                                    registry=self.registry)
        self.cache_hit_ratio_gauge = Gauge('database_cache_hit_ratio',
                                         'Database cache hit ratio',
                                         ['environment', 'service', 'database'],
                                         registry=self.registry)

    async def monitor_health(self) -> Dict[str, Any]:
        """Monitor database health and publish metrics"""

        conn = await asyncpg.connect(self.database_url)

        try:
            health_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "environment": self.environment,
                "service": self.service,
                "metrics": {}
            }

            # Connection metrics
            connection_stats = await self.get_connection_stats(conn)
            health_data["metrics"]["connections"] = connection_stats

            # Query performance metrics
            query_stats = await self.get_query_stats(conn)
            health_data["metrics"]["queries"] = query_stats

            # Cache performance metrics
            cache_stats = await self.get_cache_stats(conn)
            health_data["metrics"]["cache"] = cache_stats

            # Database size metrics
            size_stats = await self.get_size_stats(conn)
            health_data["metrics"]["size"] = size_stats

            # Update Prometheus metrics
            await self.update_prometheus_metrics(health_data["metrics"])

            # Push to Prometheus Gateway
            await self.push_metrics_to_prometheus()

            return health_data

        finally:
            await conn.close()

    async def get_connection_stats(self, conn) -> Dict[str, Any]:
        """Get database connection statistics"""

        query = """
        SELECT
            datname,
            numbackends as active_connections,
            xact_commit as transactions_committed,
            xact_rollback as transactions_rolled_back,
            blks_read,
            blks_hit,
            tup_returned,
            tup_fetched,
            tup_inserted,
            tup_updated,
            tup_deleted
        FROM pg_stat_database
        WHERE datname NOT IN ('template0', 'template1', 'postgres')
        """

        results = await conn.fetch(query)

        connection_stats = {}
        for row in results:
            db_name = row['datname']
            connection_stats[db_name] = dict(row)

            # Update Prometheus gauge
            self.connection_gauge.labels(
                environment=self.environment,
                service=self.service,
                database=db_name
            ).set(row['active_connections'])

        return connection_stats

    async def get_query_stats(self, conn) -> Dict[str, Any]:
        """Get query performance statistics"""

        # Check if pg_stat_statements is available
        extension_check = await conn.fetchval("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
            )
        """)

        if not extension_check:
            return {"error": "pg_stat_statements extension not available"}

        query = """
        SELECT
            calls,
            total_time,
            mean_time,
            min_time,
            max_time,
            stddev_time,
            rows as total_rows
        FROM pg_stat_statements
        WHERE calls > 10  -- Only include frequently called queries
        ORDER BY mean_time DESC
        LIMIT 10
        """

        try:
            results = await conn.fetch(query)

            if results:
                avg_query_time = sum(row['mean_time'] for row in results) / len(results)

                # Update Prometheus gauge
                self.query_time_gauge.labels(
                    environment=self.environment,
                    service=self.service
                ).set(avg_query_time)

                return {
                    "average_query_time_ms": avg_query_time,
                    "total_queries": sum(row['calls'] for row in results),
                    "slowest_queries": [dict(row) for row in results[:5]]
                }
            else:
                return {"average_query_time_ms": 0, "total_queries": 0}

        except Exception as e:
            self.logger.warning(f"Error getting query stats: {e}")
            return {"error": str(e)}

    async def get_cache_stats(self, conn) -> Dict[str, Any]:
        """Get database cache statistics"""

        query = """
        SELECT
            datname,
            blks_read,
            blks_hit,
            CASE
                WHEN (blks_read + blks_hit) = 0 THEN 0
                ELSE (blks_hit::float / (blks_read + blks_hit)::float) * 100
            END as cache_hit_ratio
        FROM pg_stat_database
        WHERE datname NOT IN ('template0', 'template1', 'postgres')
        """

        results = await conn.fetch(query)

        cache_stats = {}
        for row in results:
            db_name = row['datname']
            cache_stats[db_name] = {
                "blocks_read": row['blks_read'],
                "blocks_hit": row['blks_hit'],
                "cache_hit_ratio": row['cache_hit_ratio']
            }

            # Update Prometheus gauge
            self.cache_hit_ratio_gauge.labels(
                environment=self.environment,
                service=self.service,
                database=db_name
            ).set(row['cache_hit_ratio'])

        return cache_stats

    async def get_size_stats(self, conn) -> Dict[str, Any]:
        """Get database size statistics"""

        query = """
        SELECT
            datname,
            pg_database_size(datname) as size_bytes,
            pg_size_pretty(pg_database_size(datname)) as size_pretty
        FROM pg_database
        WHERE datname NOT IN ('template0', 'template1', 'postgres')
        """

        results = await conn.fetch(query)

        size_stats = {}
        for row in results:
            size_stats[row['datname']] = {
                "size_bytes": row['size_bytes'],
                "size_pretty": row['size_pretty']
            }

        return size_stats

    async def update_prometheus_metrics(self, metrics: Dict[str, Any]):
        """Update Prometheus metrics with current data"""

        # Metrics are updated in individual methods above
        # This method can be extended for additional custom metrics
        pass

    async def push_metrics_to_prometheus(self):
        """Push metrics to Prometheus Gateway"""

        prometheus_gateway = os.getenv("PROMETHEUS_PUSHGATEWAY_URL")
        if prometheus_gateway:
            try:
                push_to_gateway(
                    prometheus_gateway,
                    job=f'database_health_{self.environment}_{self.service}',
                    registry=self.registry
                )
                self.logger.info("Successfully pushed metrics to Prometheus")
            except Exception as e:
                self.logger.error(f"Failed to push metrics to Prometheus: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Database Health Monitor')
    parser.add_argument('--database-url', required=True)
    parser.add_argument('--environment', required=True)
    parser.add_argument('--service', required=True)

    args = parser.parse_args()

    monitor = DatabaseHealthMonitor(args.database_url, args.environment, args.service)
    result = asyncio.run(monitor.monitor_health())

    print(json.dumps(result, indent=2))
```

## 5. Notification Templates

### Slack Notification Templates

```python
# scripts/notifications/slack-templates.py
from datetime import datetime
from typing import Dict, Any, List

class SlackNotificationTemplates:

    @staticmethod
    def database_migration_success(migration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Template for successful database migration notification"""

        return {
            "channel": "#database-migrations",
            "username": "Migration Bot",
            "icon_emoji": ":white_check_mark:",
            "attachments": [
                {
                    "color": "good",
                    "title": "✅ Database Migration Completed Successfully",
                    "fields": [
                        {
                            "title": "Environment",
                            "value": migration_data.get("environment", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Service",
                            "value": migration_data.get("service", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Duration",
                            "value": f"{migration_data.get('duration_seconds', 0):.2f} seconds",
                            "short": True
                        },
                        {
                            "title": "Tables Affected",
                            "value": str(migration_data.get("tables_affected", 0)),
                            "short": True
                        }
                    ],
                    "footer": "SaaS Control Deck Migration System",
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }

    @staticmethod
    def data_quality_alert(quality_data: Dict[str, Any]) -> Dict[str, Any]:
        """Template for data quality alert notification"""

        severity_colors = {
            "critical": "danger",
            "warning": "warning",
            "info": "good"
        }

        severity_icons = {
            "critical": "🚨",
            "warning": "⚠️",
            "info": "ℹ️"
        }

        severity = quality_data.get("severity", "info")

        return {
            "channel": "#data-quality",
            "username": "Data Quality Monitor",
            "icon_emoji": ":bar_chart:",
            "attachments": [
                {
                    "color": severity_colors.get(severity, "good"),
                    "title": f"{severity_icons.get(severity, '')} Data Quality Alert",
                    "fields": [
                        {
                            "title": "Environment",
                            "value": quality_data.get("environment", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Service",
                            "value": quality_data.get("service", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Quality Score",
                            "value": f"{quality_data.get('quality_score', 0):.3f}",
                            "short": True
                        },
                        {
                            "title": "Dimension",
                            "value": quality_data.get("dimension", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Issues Found",
                            "value": str(quality_data.get("issues_count", 0)),
                            "short": True
                        },
                        {
                            "title": "Threshold",
                            "value": str(quality_data.get("threshold", "N/A")),
                            "short": True
                        }
                    ],
                    "text": quality_data.get("description", "Data quality issue detected"),
                    "footer": "SaaS Control Deck Data Quality System",
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }

    @staticmethod
    def commercial_metrics_update(commercial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Template for commercial metrics update notification"""

        return {
            "channel": "#commercial-metrics",
            "username": "Commercial Analytics Bot",
            "icon_emoji": ":chart_with_upwards_trend:",
            "attachments": [
                {
                    "color": "good",
                    "title": "📊 Commercial Metrics Update",
                    "fields": [
                        {
                            "title": "Environment",
                            "value": commercial_data.get("environment", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Conversion Rate",
                            "value": f"{commercial_data.get('conversion_rate', 0):.2f}%",
                            "short": True
                        },
                        {
                            "title": "Active Subscriptions",
                            "value": str(commercial_data.get("active_subscriptions", 0)),
                            "short": True
                        },
                        {
                            "title": "Revenue Impact",
                            "value": f"${commercial_data.get('revenue_impact', 0):,.2f}",
                            "short": True
                        }
                    ],
                    "footer": "SaaS Control Deck Commercial System",
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }

    @staticmethod
    def cicd_pipeline_failure(pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """Template for CI/CD pipeline failure notification"""

        return {
            "channel": "#cicd-alerts",
            "username": "CI/CD Monitor",
            "icon_emoji": ":x:",
            "attachments": [
                {
                    "color": "danger",
                    "title": "❌ CI/CD Pipeline Failed",
                    "fields": [
                        {
                            "title": "Workflow",
                            "value": pipeline_data.get("workflow_name", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Environment",
                            "value": pipeline_data.get("environment", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Branch",
                            "value": pipeline_data.get("branch", "Unknown"),
                            "short": True
                        },
                        {
                            "title": "Failure Reason",
                            "value": pipeline_data.get("failure_reason", "Unknown"),
                            "short": False
                        }
                    ],
                    "actions": [
                        {
                            "type": "button",
                            "text": "View Workflow",
                            "url": pipeline_data.get("workflow_url", "#")
                        }
                    ],
                    "footer": "SaaS Control Deck CI/CD System",
                    "ts": int(datetime.utcnow().timestamp())
                }
            ]
        }
```

## Summary

This monitoring and alerting configuration provides:

1. **Comprehensive Prometheus Monitoring**: Database health, CI/CD pipelines, data quality, and commercial metrics
2. **Intelligent AlertManager Routing**: Environment-based routing with appropriate escalation
3. **Rich Grafana Dashboards**: Visual monitoring with customizable alerts
4. **Custom Monitoring Scripts**: Specialized database health monitoring with Prometheus integration
5. **Professional Notification Templates**: Structured Slack notifications for different event types
6. **Multi-Environment Support**: Separate monitoring configurations for development, staging, and production
7. **Automated Remediation Triggers**: Integration points for auto-remediation workflows

The configuration ensures comprehensive visibility into the SaaS Control Deck platform's database operations while providing timely alerts and actionable insights for maintaining optimal performance and reliability.