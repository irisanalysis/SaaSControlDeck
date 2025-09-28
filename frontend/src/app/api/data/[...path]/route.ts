/**
 * Next.js API Proxy Route for Data Upload
 * Forwards data upload requests to the Unified Backend Service
 * RELEVANT FILES: data-sources.ts, use-data-source-upload.ts, unified_backend_simple.py
 */

import { NextRequest, NextResponse } from 'next/server';

// 统一后端服务端点配置（FastAPI统一后端运行在8000端口）
// 支持所有数据管理API，包括上传、预览和管理功能
const BACKEND_BASE_URL = process.env.BACKEND_API_URL || 'http://localhost:8000';

async function proxyToBackend(request: NextRequest, method: string) {
  try {
    const url = new URL(request.url);
    // 处理路径映射：
    // /api/data/upload/file -> /upload/file
    // /api/data/sources -> /data/sources
    let path = url.pathname.replace('/api/data', '');

    // 特殊处理：对于data相关的端点，需要保留/data前缀
    if (path.startsWith('/sources') || path.startsWith('/stats')) {
      path = '/data' + path;
    }
    const backendUrl = `${BACKEND_BASE_URL}${path}${url.search}`;

    console.log(`[Data Proxy] ${method} ${path} -> ${backendUrl}`);

    // 准备请求头
    const headers: HeadersInit = {};

    // 转发Authorization头
    const auth = request.headers.get('authorization');
    if (auth) {
      headers.Authorization = auth;
    }

    // 准备请求体
    let body: any = null;
    const contentType = request.headers.get('content-type');

    if (method === 'GET') {
      // GET 请求不需要body
      headers['Content-Type'] = 'application/json';
    } else if (contentType?.includes('multipart/form-data')) {
      // 对于文件上传，直接转发FormData
      body = await request.formData();
      // FormData会自动设置正确的Content-Type，包括boundary
      // 不要手动设置Content-Type
    } else {
      // 对于JSON请求
      body = await request.text();
      headers['Content-Type'] = 'application/json';
    }

    console.log(`[Data Proxy] Headers:`, headers);
    console.log(`[Data Proxy] Body type:`, typeof body);

    // 发送请求到后端
    const response = await fetch(backendUrl, {
      method,
      headers,
      body,
    });

    console.log(`[Data Proxy] Response status: ${response.status}`);

    // 处理响应
    const responseText = await response.text();
    let responseData;

    try {
      responseData = JSON.parse(responseText);
    } catch {
      responseData = { message: responseText };
    }

    return NextResponse.json(responseData, {
      status: response.status,
      headers: {
        'Content-Type': 'application/json',
      },
    });

  } catch (error) {
    console.error(`[Data Proxy] ${method} Error:`, error);
    return NextResponse.json(
      {
        error: 'Proxy error',
        message: error instanceof Error ? error.message : String(error),
        details: String(error)
      },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  return proxyToBackend(request, 'GET');
}

export async function POST(request: NextRequest) {
  return proxyToBackend(request, 'POST');
}

export async function PUT(request: NextRequest) {
  return proxyToBackend(request, 'PUT');
}

export async function DELETE(request: NextRequest) {
  return proxyToBackend(request, 'DELETE');
}