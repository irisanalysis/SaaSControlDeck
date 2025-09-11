import { NextRequest, NextResponse } from 'next/server';

// Prometheus指标格式
interface PrometheusMetric {
  name: string;
  help: string;
  type: 'counter' | 'gauge' | 'histogram' | 'summary';
  value: number;
  labels?: Record<string, string>;
}

// 应用指标接口
interface AppMetrics {
  requests_total: number;
  request_duration_seconds: number;
  active_connections: number;
  errors_total: number;
  memory_usage_bytes: number;
  uptime_seconds: number;
}

// 全局指标存储 (在实际应用中应该使用Redis或数据库)
let metricsStore: AppMetrics = {
  requests_total: 0,
  request_duration_seconds: 0,
  active_connections: 0,
  errors_total: 0,
  memory_usage_bytes: 0,
  uptime_seconds: 0,
};

// 获取系统指标
function getSystemMetrics(): Partial<AppMetrics> {
  const metrics: Partial<AppMetrics> = {};

  try {
    // 内存使用 (如果在Node.js运行时中)
    if (typeof process !== 'undefined' && process.memoryUsage) {
      const memUsage = process.memoryUsage();
      metrics.memory_usage_bytes = memUsage.heapUsed;
    }

    // 运行时间
    if (typeof process !== 'undefined' && process.uptime) {
      metrics.uptime_seconds = process.uptime();
    } else {
      // Edge Runtime 估算
      metrics.uptime_seconds = Date.now() / 1000;
    }

  } catch (error) {
    console.warn('获取系统指标失败:', error);
  }

  return metrics;
}

// 格式化为Prometheus格式
function formatPrometheusMetrics(metrics: AppMetrics): string {
  const prometheusMetrics: PrometheusMetric[] = [
    {
      name: 'http_requests_total',
      help: 'Total number of HTTP requests',
      type: 'counter',
      value: metrics.requests_total,
      labels: { app: 'saas-control-deck-frontend' },
    },
    {
      name: 'http_request_duration_seconds',
      help: 'HTTP request duration in seconds',
      type: 'gauge',
      value: metrics.request_duration_seconds,
      labels: { app: 'saas-control-deck-frontend' },
    },
    {
      name: 'http_active_connections',
      help: 'Number of active HTTP connections',
      type: 'gauge',
      value: metrics.active_connections,
      labels: { app: 'saas-control-deck-frontend' },
    },
    {
      name: 'http_errors_total',
      help: 'Total number of HTTP errors',
      type: 'counter',
      value: metrics.errors_total,
      labels: { app: 'saas-control-deck-frontend' },
    },
    {
      name: 'process_memory_usage_bytes',
      help: 'Process memory usage in bytes',
      type: 'gauge',
      value: metrics.memory_usage_bytes,
      labels: { app: 'saas-control-deck-frontend' },
    },
    {
      name: 'process_uptime_seconds',
      help: 'Process uptime in seconds',
      type: 'gauge',
      value: metrics.uptime_seconds,
      labels: { app: 'saas-control-deck-frontend' },
    },
  ];

  return prometheusMetrics
    .map(metric => {
      const labels = metric.labels
        ? `{${Object.entries(metric.labels).map(([k, v]) => `${k}="${v}"`).join(',')}}`
        : '';
      
      return [
        `# HELP ${metric.name} ${metric.help}`,
        `# TYPE ${metric.name} ${metric.type}`,
        `${metric.name}${labels} ${metric.value}`,
      ].join('\n');
    })
    .join('\n\n');
}

// 增加请求计数
function incrementRequestCounter() {
  metricsStore.requests_total += 1;
}

// 记录请求时长
function recordRequestDuration(duration: number) {
  metricsStore.request_duration_seconds = duration;
}

// 增加错误计数
function incrementErrorCounter() {
  metricsStore.errors_total += 1;
}

// GET /api/metrics - Prometheus指标端点
export async function GET(request: NextRequest): Promise<NextResponse> {
  const startTime = Date.now();

  try {
    // 增加请求计数
    incrementRequestCounter();

    // 获取当前系统指标
    const systemMetrics = getSystemMetrics();
    
    // 更新指标存储
    const currentMetrics: AppMetrics = {
      ...metricsStore,
      ...systemMetrics,
    };

    // 记录这次请求的处理时间
    const duration = (Date.now() - startTime) / 1000;
    recordRequestDuration(duration);

    // 检查请求格式
    const { searchParams } = new URL(request.url);
    const format = searchParams.get('format') || 'prometheus';

    if (format === 'json') {
      // JSON格式响应
      return NextResponse.json({
        timestamp: new Date().toISOString(),
        metrics: currentMetrics,
        meta: {
          version: process.env.npm_package_version || '1.0.0',
          environment: process.env.NODE_ENV || 'development',
          app: 'saas-control-deck-frontend',
        },
      });
    }

    // Prometheus格式响应 (默认)
    const prometheusOutput = formatPrometheusMetrics(currentMetrics);

    return new NextResponse(prometheusOutput, {
      status: 200,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
      },
    });

  } catch (error) {
    console.error('指标收集失败:', error);
    incrementErrorCounter();

    return NextResponse.json(
      {
        error: 'Failed to collect metrics',
        message: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString(),
      },
      { status: 500 }
    );
  }
}

// POST /api/metrics - 自定义指标上报
export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();
    
    // 验证输入
    if (!body.metric || !body.value) {
      return NextResponse.json(
        { error: 'Missing required fields: metric, value' },
        { status: 400 }
      );
    }

    // 处理自定义指标 (这里可以扩展)
    const { metric, value, labels } = body;

    // 简单的指标更新逻辑
    switch (metric) {
      case 'active_connections':
        metricsStore.active_connections = value;
        break;
      case 'error_count':
        metricsStore.errors_total += value;
        break;
      default:
        console.warn(`未知指标类型: ${metric}`);
    }

    return NextResponse.json({
      success: true,
      message: `Metric ${metric} updated`,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('指标更新失败:', error);
    
    return NextResponse.json(
      {
        error: 'Failed to update metrics',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}

// PUT /api/metrics/reset - 重置指标 (仅用于测试)
export async function PUT(request: NextRequest): Promise<NextResponse> {
  try {
    // 只在非生产环境允许重置
    if (process.env.NODE_ENV === 'production') {
      return NextResponse.json(
        { error: 'Metrics reset not allowed in production' },
        { status: 403 }
      );
    }

    // 重置指标
    metricsStore = {
      requests_total: 0,
      request_duration_seconds: 0,
      active_connections: 0,
      errors_total: 0,
      memory_usage_bytes: 0,
      uptime_seconds: 0,
    };

    return NextResponse.json({
      success: true,
      message: 'Metrics reset successfully',
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('指标重置失败:', error);
    
    return NextResponse.json(
      {
        error: 'Failed to reset metrics',
        message: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}