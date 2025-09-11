import { NextRequest, NextResponse } from 'next/server';

// 基础健康检查接口
interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  version: string;
  environment: string;
  uptime: number;
  services?: ServiceHealth[];
  system?: SystemHealth;
}

interface ServiceHealth {
  name: string;
  status: 'up' | 'down' | 'degraded';
  responseTime?: number;
  lastCheck: string;
  error?: string;
}

interface SystemHealth {
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  cpu: {
    usage: number;
  };
  disk: {
    used: number;
    total: number;
    percentage: number;
  };
}

// 检查外部服务健康状态
async function checkExternalServices(): Promise<ServiceHealth[]> {
  const services: ServiceHealth[] = [];
  const checkStartTime = Date.now();

  // 检查SaaS Control Deck后端微服务
  // Backend Pro1 - 主要服务集群
  const backendPro1Services = [
    { name: 'backend-pro1-api', port: 8000, service: 'API Gateway' },
    { name: 'backend-pro1-data', port: 8001, service: 'Data Service' },
    { name: 'backend-pro1-ai', port: 8002, service: 'AI Service' },
  ];

  // Backend Pro2 - 扩展服务集群
  const backendPro2Services = [
    { name: 'backend-pro2-api', port: 8100, service: 'API Gateway' },
    { name: 'backend-pro2-data', port: 8101, service: 'Data Service' },
    { name: 'backend-pro2-ai', port: 8102, service: 'AI Service' },
  ];

  const allBackendServices = [...backendPro1Services, ...backendPro2Services];

  for (const { name, port, service } of allBackendServices) {
    const serviceStartTime = Date.now();
    try {
      const response = await fetch(`http://localhost:${port}/health`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(3000), // 3秒超时，针对微服务优化
      });

      services.push({
        name,
        status: response.ok ? 'up' : 'down',
        responseTime: Date.now() - serviceStartTime,
        lastCheck: new Date().toISOString(),
        error: response.ok ? undefined : `${service} HTTP ${response.status}`,
      });
    } catch (error) {
      services.push({
        name,
        status: 'down',
        responseTime: Date.now() - serviceStartTime,
        lastCheck: new Date().toISOString(),
        error: `${service}: ${error instanceof Error ? error.message : 'Connection failed'}`,
      });
    }
  }

  // 检查AI服务 (如果配置了)
  if (process.env.GOOGLE_GENAI_API_KEY) {
    try {
      // 这里可以添加对Google AI API的健康检查
      services.push({
        name: 'google-ai',
        status: 'up',
        lastCheck: new Date().toISOString(),
      });
    } catch (error) {
      services.push({
        name: 'google-ai',
        status: 'down',
        lastCheck: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  }

  return services;
}

// 获取系统信息 (在Edge Runtime中受限)
function getSystemHealth(): SystemHealth | undefined {
  try {
    // 在Node.js运行时中可以获取更多系统信息
    // 在Edge Runtime中这些API可能不可用
    if (typeof process !== 'undefined' && process.memoryUsage) {
      const memUsage = process.memoryUsage();
      return {
        memory: {
          used: memUsage.heapUsed,
          total: memUsage.heapTotal,
          percentage: (memUsage.heapUsed / memUsage.heapTotal) * 100,
        },
        cpu: {
          usage: 0, // CPU使用率需要第三方库获取
        },
        disk: {
          used: 0,
          total: 0,
          percentage: 0,
        },
      };
    }
  } catch (error) {
    console.warn('无法获取系统健康信息:', error);
  }
  return undefined;
}

// 计算应用程序运行时间
function getUptime(): number {
  if (typeof process !== 'undefined' && process.uptime) {
    return process.uptime();
  }
  // 如果在Edge Runtime中，返回一个估算值
  return Date.now() / 1000;
}

// GET /api/health - 基础健康检查
export async function GET(request: NextRequest): Promise<NextResponse> {
  const startTime = Date.now();

  try {
    // 检查查询参数
    const { searchParams } = new URL(request.url);
    const detailed = searchParams.get('detailed') === 'true';

    const baseHealth: HealthStatus = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      uptime: getUptime(),
    };

    // 如果请求详细信息
    if (detailed) {
      const services = await checkExternalServices();
      const system = getSystemHealth();

      // 根据服务状态确定整体健康状态
      const hasUnhealthyServices = services.some(service => service.status === 'down');
      const hasDegradedServices = services.some(service => service.status === 'degraded');

      baseHealth.status = hasUnhealthyServices 
        ? 'unhealthy' 
        : hasDegradedServices 
        ? 'degraded' 
        : 'healthy';

      baseHealth.services = services;
      if (system) {
        baseHealth.system = system;
      }
    }

    const responseTime = Date.now() - startTime;

    // 根据响应时间和状态决定HTTP状态码
    const httpStatus = baseHealth.status === 'healthy' ? 200 : 
                      baseHealth.status === 'degraded' ? 200 : 503;

    return NextResponse.json(
      {
        ...baseHealth,
        responseTime: `${responseTime}ms`,
      },
      { 
        status: httpStatus,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
        },
      }
    );

  } catch (error) {
    console.error('健康检查失败:', error);

    return NextResponse.json(
      {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        version: process.env.npm_package_version || '1.0.0',
        environment: process.env.NODE_ENV || 'development',
        uptime: getUptime(),
        error: error instanceof Error ? error.message : 'Unknown error',
        responseTime: `${Date.now() - startTime}ms`,
      },
      { 
        status: 503,
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0',
        },
      }
    );
  }
}