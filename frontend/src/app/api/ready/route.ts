import { NextRequest, NextResponse } from 'next/server';

// 就绪检查接口 - 用于确定应用是否准备好接收流量
interface ReadinessStatus {
  ready: boolean;
  timestamp: string;
  checks: ReadinessCheck[];
  version: string;
  environment: string;
}

interface ReadinessCheck {
  name: string;
  status: 'pass' | 'fail';
  responseTime?: number;
  error?: string;
  required: boolean;
}

// 检查必需的依赖服务
async function checkDependencies(): Promise<ReadinessCheck[]> {
  const checks: ReadinessCheck[] = [];

  // 1. 检查后端API连接
  const backendCheck = await checkBackendAPI();
  checks.push(backendCheck);

  // 2. 检查环境变量
  const envCheck = checkEnvironmentVariables();
  checks.push(envCheck);

  // 3. 检查AI服务配置
  const aiCheck = checkAIConfiguration();
  checks.push(aiCheck);

  // 4. 检查前端构建资源
  const assetsCheck = checkStaticAssets();
  checks.push(assetsCheck);

  return checks;
}

// 检查后端API可达性
async function checkBackendAPI(): Promise<ReadinessCheck> {
  const startTime = Date.now();
  
  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL;
    
    if (!backendUrl) {
      return {
        name: 'backend-api-config',
        status: 'fail',
        error: 'NEXT_PUBLIC_API_URL 未配置',
        required: true,
        responseTime: Date.now() - startTime,
      };
    }

    const response = await fetch(`${backendUrl}/ready`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(3000), // 3秒超时
    });

    if (!response.ok) {
      return {
        name: 'backend-api',
        status: 'fail',
        error: `后端API返回 ${response.status}`,
        required: true,
        responseTime: Date.now() - startTime,
      };
    }

    return {
      name: 'backend-api',
      status: 'pass',
      required: true,
      responseTime: Date.now() - startTime,
    };

  } catch (error) {
    return {
      name: 'backend-api',
      status: 'fail',
      error: error instanceof Error ? error.message : '连接失败',
      required: true,
      responseTime: Date.now() - startTime,
    };
  }
}

// 检查必需的环境变量
function checkEnvironmentVariables(): ReadinessCheck {
  const requiredVars = [
    'NEXT_PUBLIC_API_URL',
    'NODE_ENV',
  ];

  const optionalVars = [
    'NEXT_PUBLIC_GENKIT_ENV',
    'GOOGLE_GENAI_API_KEY',
  ];

  const missingRequired = requiredVars.filter(varName => !process.env[varName]);
  const missingOptional = optionalVars.filter(varName => !process.env[varName]);

  if (missingRequired.length > 0) {
    return {
      name: 'environment-variables',
      status: 'fail',
      error: `缺少必需环境变量: ${missingRequired.join(', ')}`,
      required: true,
    };
  }

  let warning = '';
  if (missingOptional.length > 0) {
    warning = `可选环境变量未设置: ${missingOptional.join(', ')}`;
  }

  return {
    name: 'environment-variables',
    status: 'pass',
    error: warning || undefined,
    required: true,
  };
}

// 检查AI服务配置
function checkAIConfiguration(): ReadinessCheck {
  const genkitEnv = process.env.NEXT_PUBLIC_GENKIT_ENV;
  const googleAIKey = process.env.GOOGLE_GENAI_API_KEY;

  // 生产环境必须配置AI服务
  if (process.env.NODE_ENV === 'production') {
    if (!googleAIKey) {
      return {
        name: 'ai-configuration',
        status: 'fail',
        error: '生产环境缺少 GOOGLE_GENAI_API_KEY',
        required: true,
      };
    }
  }

  // 开发环境AI配置是可选的
  if (!googleAIKey && !genkitEnv) {
    return {
      name: 'ai-configuration',
      status: 'pass',
      error: 'AI服务配置缺失，某些功能可能不可用',
      required: false,
    };
  }

  return {
    name: 'ai-configuration',
    status: 'pass',
    required: false,
  };
}

// 检查静态资源
function checkStaticAssets(): ReadinessCheck {
  try {
    // 在Next.js中，这个检查主要确保构建过程完成
    // 检查关键的环境配置
    const isProduction = process.env.NODE_ENV === 'production';
    
    if (isProduction) {
      // 在生产环境中，确保必要的优化配置存在
      const hasOptimizations = process.env.NEXT_TELEMETRY_DISABLED;
      
      return {
        name: 'static-assets',
        status: 'pass',
        error: hasOptimizations ? undefined : '建议禁用遥测以提高性能',
        required: false,
      };
    }

    return {
      name: 'static-assets',
      status: 'pass',
      required: false,
    };

  } catch (error) {
    return {
      name: 'static-assets',
      status: 'fail',
      error: error instanceof Error ? error.message : '静态资源检查失败',
      required: false,
    };
  }
}

// GET /api/ready - 就绪检查
export async function GET(request: NextRequest): Promise<NextResponse> {
  const startTime = Date.now();

  try {
    const checks = await checkDependencies();
    
    // 确定整体就绪状态
    const failedRequiredChecks = checks.filter(check => check.required && check.status === 'fail');
    const ready = failedRequiredChecks.length === 0;

    const status: ReadinessStatus = {
      ready,
      timestamp: new Date().toISOString(),
      checks,
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
    };

    // 根据就绪状态决定HTTP状态码
    const httpStatus = ready ? 200 : 503;

    return NextResponse.json(
      {
        ...status,
        responseTime: `${Date.now() - startTime}ms`,
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
    console.error('就绪检查失败:', error);

    return NextResponse.json(
      {
        ready: false,
        timestamp: new Date().toISOString(),
        checks: [{
          name: 'readiness-check',
          status: 'fail' as const,
          error: error instanceof Error ? error.message : 'Unknown error',
          required: true,
        }],
        version: process.env.npm_package_version || '1.0.0',
        environment: process.env.NODE_ENV || 'development',
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