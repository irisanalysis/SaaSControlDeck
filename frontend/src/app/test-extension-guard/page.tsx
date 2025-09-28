/**
 * /frontend/src/app/test-extension-guard/page.tsx
 * 测试页面用于验证浏览器扩展错误防护系统的工作状态
 * 仅在开发环境下可用，帮助开发者测试扩展冲突检测功能
 * RELEVANT FILES: /frontend/src/components/guards/browser-extension-guard.tsx, /frontend/src/hooks/use-extension-compatibility.tsx
 */

"use client";

import React, { useState } from 'react';
import { AlertTriangle, Shield, TestTube, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useExtensionCompatibility } from '@/hooks/use-extension-compatibility';

function TestExtensionGuardPage() {
  const [testResults, setTestResults] = useState<string[]>([]);
  const { errorCount, lastError, clearErrors } = useExtensionCompatibility();

  // 模拟扩展错误的测试函数
  const simulateExtensionError = () => {
    // 创建一个模拟的扩展错误
    const mockError = new ErrorEvent('error', {
      message: 'fetchError: Failed to fetch',
      filename: 'content_script.js:7167:27147',
      error: new Error('Failed to fetch')
    });

    // 分发事件
    window.dispatchEvent(mockError);

    setTestResults(prev => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] 模拟扩展错误已触发`
    ]);
  };

  const simulateFetchError = () => {
    // 模拟Promise rejection (类似于fetch失败)
    const mockPromiseRejection = new PromiseRejectionEvent('unhandledrejection', {
      promise: Promise.reject(new Error('Failed to fetch')),
      reason: new Error('Failed to fetch')
    });

    window.dispatchEvent(mockPromiseRejection);

    setTestResults(prev => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] 模拟网络错误已触发`
    ]);
  };

  const simulateContentScriptError = () => {
    // 模拟content_script相关错误
    const mockError = new ErrorEvent('error', {
      message: 'Uncaught (in promise) TypeError: Cannot read property of undefined',
      filename: 'chrome-extension://abc123/content_script.js',
      error: new Error('Extension script error')
    });

    window.dispatchEvent(mockError);

    setTestResults(prev => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] 模拟content_script错误已触发`
    ]);
  };

  const clearTestResults = () => {
    setTestResults([]);
    clearErrors();
  };

  // 仅在开发环境下显示此页面
  if (process.env.NODE_ENV === 'production') {
    return (
      <div className="container mx-auto py-6">
        <Alert className="border-yellow-200 bg-yellow-50">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>访问受限</AlertTitle>
          <AlertDescription>
            此测试页面仅在开发环境下可用。
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">扩展防护系统测试</h1>
          <p className="text-muted-foreground">
            测试浏览器扩展错误检测和隔离功能
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={clearTestResults} variant="outline" size="sm">
            清除结果
          </Button>
        </div>
      </div>

      {/* 当前状态 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-blue-600" />
              <div>
                <div className="text-2xl font-bold">{errorCount}</div>
                <p className="text-xs text-muted-foreground">已捕获的扩展错误</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <TestTube className="w-5 h-5 text-green-600" />
              <div>
                <div className="text-2xl font-bold">{testResults.length}</div>
                <p className="text-xs text-muted-foreground">模拟测试次数</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Zap className="w-5 h-5 text-yellow-600" />
              <div>
                <div className="text-2xl font-bold">
                  {lastError ? '有错误' : '正常'}
                </div>
                <p className="text-xs text-muted-foreground">防护系统状态</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 最近错误显示 */}
      {lastError && (
        <Alert className="border-yellow-200 bg-yellow-50">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>最近捕获的错误</AlertTitle>
          <AlertDescription>
            <div className="mt-2 font-mono text-sm bg-yellow-100 p-2 rounded">
              {lastError}
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* 测试按钮 */}
      <Card>
        <CardHeader>
          <CardTitle>错误模拟测试</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              onClick={simulateExtensionError}
              variant="outline"
              className="flex flex-col items-center gap-2 h-auto py-4"
            >
              <AlertTriangle className="w-6 h-6 text-red-500" />
              <div className="text-center">
                <div className="font-semibold">扩展脚本错误</div>
                <div className="text-xs text-muted-foreground">
                  模拟content_script.js错误
                </div>
              </div>
            </Button>

            <Button
              onClick={simulateFetchError}
              variant="outline"
              className="flex flex-col items-center gap-2 h-auto py-4"
            >
              <Zap className="w-6 h-6 text-orange-500" />
              <div className="text-center">
                <div className="font-semibold">网络请求错误</div>
                <div className="text-xs text-muted-foreground">
                  模拟Failed to fetch错误
                </div>
              </div>
            </Button>

            <Button
              onClick={simulateContentScriptError}
              variant="outline"
              className="flex flex-col items-center gap-2 h-auto py-4"
            >
              <Shield className="w-6 h-6 text-blue-500" />
              <div className="text-center">
                <div className="font-semibold">扩展注入错误</div>
                <div className="text-xs text-muted-foreground">
                  模拟扩展DOM操作错误
                </div>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 测试结果日志 */}
      <Card>
        <CardHeader>
          <CardTitle>测试日志</CardTitle>
        </CardHeader>
        <CardContent>
          {testResults.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              暂无测试记录，点击上方按钮开始测试
            </div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {testResults.map((result, index) => (
                <div
                  key={index}
                  className="p-2 bg-gray-50 rounded text-sm font-mono"
                >
                  {result}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 说明信息 */}
      <Alert>
        <Shield className="h-4 w-4" />
        <AlertTitle>测试说明</AlertTitle>
        <AlertDescription>
          <ul className="mt-2 space-y-1 text-sm">
            <li>• 此页面用于测试扩展错误防护系统是否正常工作</li>
            <li>• 模拟的错误会被自动捕获和隔离，不会影响应用功能</li>
            <li>• 在开发者工具Console中可以看到防护系统的日志信息</li>
            <li>• 生产环境下此测试页面不可访问</li>
          </ul>
        </AlertDescription>
      </Alert>
    </div>
  );
}

export default TestExtensionGuardPage;