/**
 * Next.js API Proxy Route for Authentication
 * Forwards authentication requests to the backend API Gateway
 * RELEVANT FILES: auth.ts, auth-context.tsx, backend auth endpoints
 */

import { NextRequest, NextResponse } from 'next/server';

// 统一后端服务的认证端点配置
const DEFAULT_BACKEND_BASE = 'http://localhost:8000/auth';
const BACKEND_AUTH_BASE_URL = (() => {
  const raw = process.env.BACKEND_API_URL || 'http://localhost:8000';
  const trimmed = raw.endsWith('/') ? raw.slice(0, -1) : raw;

  // 对于统一后端服务，认证端点直接是 /auth
  return `${trimmed}/auth`;
})();

function buildBackendUrl(request: NextRequest) {
  const incomingUrl = new URL(request.url);
  const authPath = incomingUrl.pathname.replace('/api/auth', '') || '/';
  const normalizedPath = authPath.startsWith('/') ? authPath : `/${authPath}`;
  return `${BACKEND_AUTH_BASE_URL}${normalizedPath}${incomingUrl.search}`;
}

export async function POST(request: NextRequest) {
  try {
    const backendUrl = buildBackendUrl(request);
    console.log(`[AUTH PROXY] POST request to: ${backendUrl}`);
    console.log(`[AUTH PROXY] Environment BACKEND_API_URL: ${process.env.BACKEND_API_URL}`);
    console.log(`[AUTH PROXY] Computed BACKEND_AUTH_BASE_URL: ${BACKEND_AUTH_BASE_URL}`);

    const requestBody = await request.text();
    console.log(`[AUTH PROXY] Request body: ${requestBody}`);

    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Forward any authorization headers
        ...(request.headers.get('authorization') && {
          Authorization: request.headers.get('authorization')!,
        }),
      },
      body: requestBody,
    });

    console.log(`[AUTH PROXY] Backend response status: ${response.status}`);

    const data = await response.json().catch(() => ({ detail: 'Invalid response format' }));
    console.log(`[AUTH PROXY] Backend response data:`, data);

    // Return the response with the same status code
    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error) {
    console.error('[AUTH PROXY] Error details:', {
      message: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
      url: buildBackendUrl(request)
    });

    return NextResponse.json(
      {
        detail: error instanceof Error ? error.message : 'Internal server error',
        error: 'Authentication proxy failed'
      },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const backendUrl = buildBackendUrl(request);
    console.log(`[AUTH PROXY] GET request to: ${backendUrl}`);

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Forward any authorization headers
        ...(request.headers.get('authorization') && {
          Authorization: request.headers.get('authorization')!,
        }),
      },
    });

    console.log(`[AUTH PROXY] Backend response status: ${response.status}`);

    const data = await response.json().catch(() => ({ detail: 'Invalid response format' }));
    console.log(`[AUTH PROXY] Backend response data:`, data);

    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error) {
    console.error('[AUTH PROXY] Error details:', {
      message: error instanceof Error ? error.message : 'Unknown error',
      stack: error instanceof Error ? error.stack : undefined,
      url: buildBackendUrl(request)
    });

    return NextResponse.json(
      {
        detail: error instanceof Error ? error.message : 'Internal server error',
        error: 'Authentication proxy failed'
      },
      { status: 500 }
    );
  }
}
