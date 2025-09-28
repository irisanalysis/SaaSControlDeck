/**
 * /frontend/src/components/guards/browser-extension-guard.tsx
 * 浏览器扩展冲突防护组件，检测和隔离第三方扩展可能产生的错误
 * 提供错误边界保护和用户友好提示，确保SaaS Control Deck核心功能不受影响
 * RELEVANT FILES: /frontend/src/app/layout.tsx, /frontend/src/lib/utils/extension-detector.ts, /frontend/src/hooks/use-error-boundary.tsx
 */

"use client";

import React, { useEffect, useState, ReactNode } from 'react';
import { AlertTriangle, X, Shield, RefreshCw } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface ExtensionError {
  message: string;
  source: string;
  timestamp: number;
  type: 'fetch_error' | 'script_error' | 'network_error';
}

interface BrowserExtensionGuardProps {
  children: ReactNode;
}

export function BrowserExtensionGuard({ children }: BrowserExtensionGuardProps) {
  const [extensionErrors, setExtensionErrors] = useState<ExtensionError[]>([]);
  const [showWarning, setShowWarning] = useState(false);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);

    // 检测第三方扩展错误的监听器
    const handleExtensionError = (event: ErrorEvent) => {
      const error = event.error || {};
      const message = event.message || '';
      const source = event.filename || 'unknown';

      // 检测是否是浏览器扩展相关的错误
      const isExtensionError =
        source.includes('content_script') ||
        source.includes('chrome-extension') ||
        source.includes('moz-extension') ||
        source.includes('safari-extension') ||
        message.includes('fetchError: Failed to fetch') ||
        (source === '' && message.includes('Failed to fetch')); // 匿名脚本中的fetch错误

      if (isExtensionError) {
        const extensionError: ExtensionError = {
          message: message,
          source: source,
          timestamp: Date.now(),
          type: message.includes('fetch') ? 'fetch_error' : 'script_error'
        };

        setExtensionErrors(prev => {
          // 避免重复错误
          const isDuplicate = prev.some(err =>
            err.message === extensionError.message &&
            err.source === extensionError.source &&
            (Date.now() - err.timestamp) < 5000 // 5秒内的重复错误
          );

          if (!isDuplicate) {
            console.warn('🛡️ 浏览器扩展错误已被隔离:', extensionError);
            return [...prev.slice(-4), extensionError]; // 保留最近5个错误
          }
          return prev;
        });

        setShowWarning(true);

        // 5秒后自动隐藏警告
        setTimeout(() => setShowWarning(false), 5000);

        // 阻止错误传播到应用层
        event.preventDefault();
        event.stopPropagation();
        return false;
      }
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason;

      // 检测是否是扩展相关的Promise rejection
      if (reason && typeof reason === 'object') {
        const message = reason.message || reason.toString();
        if (message.includes('Failed to fetch') ||
            message.includes('content_script') ||
            message.includes('extension')) {

          const extensionError: ExtensionError = {
            message: message,
            source: 'extension_promise',
            timestamp: Date.now(),
            type: 'network_error'
          };

          setExtensionErrors(prev => [...prev.slice(-4), extensionError]);
          setShowWarning(true);
          setTimeout(() => setShowWarning(false), 5000);

          console.warn('🛡️ 扩展Promise rejection已被隔离:', extensionError);

          // 阻止Promise rejection传播
          event.preventDefault();
          return false;
        }
      }
    };

    // 添加错误监听器
    window.addEventListener('error', handleExtensionError, true);
    window.addEventListener('unhandledrejection', handleUnhandledRejection, true);

    // 初始化时检查是否有扩展相关的全局错误
    if (window.console && window.console.error) {
      const originalConsoleError = window.console.error;
      window.console.error = (...args: any[]) => {
        const message = args.join(' ');
        if (message.includes('content_script') ||
            message.includes('Failed to fetch') ||
            message.includes('extension')) {
          console.warn('🛡️ 控制台扩展错误已被过滤:', message);
          return; // 不显示扩展相关的控制台错误
        }
        originalConsoleError.apply(console, args);
      };
    }

    return () => {
      window.removeEventListener('error', handleExtensionError, true);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection, true);
    };
  }, []);

  const dismissWarning = () => {
    setShowWarning(false);
  };

  const clearAllErrors = () => {
    setExtensionErrors([]);
    setShowWarning(false);
  };

  // 服务端渲染时直接返回children
  if (!isClient) {
    return <>{children}</>;
  }

  return (
    <>
      {children}

      {/* 浮动警告提示 */}
      {showWarning && extensionErrors.length > 0 && (
        <div className="fixed top-4 right-4 z-50 max-w-md">
          <Alert className="border-yellow-200 bg-yellow-50 text-yellow-800 shadow-lg">
            <Shield className="h-4 w-4" />
            <AlertTitle className="flex items-center justify-between">
              <span>浏览器扩展警告</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={dismissWarning}
                className="h-4 w-4 p-0 text-yellow-600 hover:text-yellow-800"
              >
                <X className="h-3 w-3" />
              </Button>
            </AlertTitle>
            <AlertDescription className="text-sm">
              检测到浏览器扩展错误，但不会影响应用功能。错误已被自动隔离。
              <div className="mt-2 text-xs text-yellow-600">
                最新错误: {extensionErrors[extensionErrors.length - 1]?.message.slice(0, 50)}...
              </div>
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* 开发模式下的详细错误信息 */}
      {process.env.NODE_ENV === 'development' && extensionErrors.length > 0 && (
        <div className="fixed bottom-4 left-4 z-40 max-w-sm">
          <Card className="border-amber-200 bg-amber-50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-600" />
                  扩展错误监控 ({extensionErrors.length})
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearAllErrors}
                  className="h-6 w-6 p-0"
                >
                  <RefreshCw className="h-3 w-3" />
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-1 text-xs text-amber-700 max-h-32 overflow-y-auto">
                {extensionErrors.slice(-3).map((error, index) => (
                  <div key={`${error.timestamp}-${index}`} className="p-1 bg-amber-100 rounded">
                    <div className="font-mono text-xs">
                      {error.type}: {error.message.slice(0, 40)}...
                    </div>
                    <div className="text-amber-500 text-xs">
                      来源: {error.source || 'unknown'}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </>
  );
}