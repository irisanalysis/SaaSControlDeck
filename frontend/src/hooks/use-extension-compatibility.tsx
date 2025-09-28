/**
 * /frontend/src/hooks/use-extension-compatibility.tsx
 * React Hook用于监控浏览器扩展兼容性，提供实时错误检测和用户指导
 * 集成到应用组件中，提供智能的扩展冲突处理
 * RELEVANT FILES: /frontend/src/components/guards/browser-extension-guard.tsx, /frontend/src/lib/utils/extension-detector.ts
 */

"use client";

import { useState, useEffect, useCallback } from 'react';
import {
  ExtensionInfo,
  BrowserInfo,
  detectBrowserExtensions,
  getBrowserInfo,
  analyzeExtensionRisks,
  isExtensionRelatedError
} from '@/lib/utils/extension-detector';

interface UseExtensionCompatibilityReturn {
  browser: BrowserInfo;
  extensions: ExtensionInfo[];
  errorCount: number;
  hasHighRiskExtensions: boolean;
  lastError: string | null;
  isMonitoring: boolean;
  startMonitoring: () => void;
  stopMonitoring: () => void;
  clearErrors: () => void;
  generateReport: () => string;
}

/**
 * 监控浏览器扩展兼容性的React Hook
 */
export function useExtensionCompatibility(): UseExtensionCompatibilityReturn {
  const [browser, setBrowser] = useState<BrowserInfo>({
    name: 'Unknown',
    version: 'Unknown',
    vendor: 'Unknown',
    is_extension_capable: false
  });

  const [extensions, setExtensions] = useState<ExtensionInfo[]>([]);
  const [errorCount, setErrorCount] = useState(0);
  const [lastError, setLastError] = useState<string | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);

  // 初始化检测
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setBrowser(getBrowserInfo());
      setExtensions(detectBrowserExtensions());
    }
  }, []);

  // 错误监听器
  const handleExtensionError = useCallback((event: ErrorEvent) => {
    if (isExtensionRelatedError(event.message)) {
      setErrorCount(prev => prev + 1);
      setLastError(event.message);

      console.warn('🛡️ 扩展相关错误已记录:', {
        message: event.message,
        source: event.filename,
        timestamp: new Date().toISOString()
      });

      // 阻止错误传播到应用层
      event.preventDefault();
      event.stopPropagation();
      return false;
    }
  }, []);

  const handleUnhandledRejection = useCallback((event: PromiseRejectionEvent) => {
    const reason = event.reason;
    if (reason && typeof reason === 'object' && reason.message) {
      if (isExtensionRelatedError(reason.message)) {
        setErrorCount(prev => prev + 1);
        setLastError(reason.message);

        console.warn('🛡️ 扩展Promise rejection已记录:', reason.message);

        // 阻止Promise rejection传播
        event.preventDefault();
        return false;
      }
    }
  }, []);

  // 开始监控
  const startMonitoring = useCallback(() => {
    if (typeof window !== 'undefined' && !isMonitoring) {
      window.addEventListener('error', handleExtensionError, true);
      window.addEventListener('unhandledrejection', handleUnhandledRejection, true);
      setIsMonitoring(true);
      console.log('🔍 浏览器扩展监控已启动');
    }
  }, [isMonitoring, handleExtensionError, handleUnhandledRejection]);

  // 停止监控
  const stopMonitoring = useCallback(() => {
    if (typeof window !== 'undefined' && isMonitoring) {
      window.removeEventListener('error', handleExtensionError, true);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection, true);
      setIsMonitoring(false);
      console.log('⏹️ 浏览器扩展监控已停止');
    }
  }, [isMonitoring, handleExtensionError, handleUnhandledRejection]);

  // 清除错误计数
  const clearErrors = useCallback(() => {
    setErrorCount(0);
    setLastError(null);
  }, []);

  // 生成兼容性报告
  const generateReport = useCallback(() => {
    const riskAnalysis = analyzeExtensionRisks(extensions);

    const report = {
      timestamp: new Date().toISOString(),
      browser,
      extensions,
      error_count: errorCount,
      last_error: lastError,
      risk_analysis: riskAnalysis,
      monitoring_status: isMonitoring ? 'active' : 'inactive'
    };

    return JSON.stringify(report, null, 2);
  }, [browser, extensions, errorCount, lastError, isMonitoring]);

  // 自动启动监控
  useEffect(() => {
    startMonitoring();
    return () => {
      stopMonitoring();
    };
  }, [startMonitoring, stopMonitoring]);

  // 计算高风险扩展
  const hasHighRiskExtensions = extensions.some(ext => ext.risk_level === 'high');

  return {
    browser,
    extensions,
    errorCount,
    hasHighRiskExtensions,
    lastError,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    clearErrors,
    generateReport
  };
}

/**
 * 轻量级错误检测Hook，仅用于关键页面
 */
export function useExtensionErrorDetection() {
  const [errorDetected, setErrorDetected] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      if (isExtensionRelatedError(event.message)) {
        setErrorDetected(true);
        setErrorMessage(event.message);

        // 3秒后自动清除状态
        setTimeout(() => {
          setErrorDetected(false);
          setErrorMessage('');
        }, 3000);

        event.preventDefault();
        return false;
      }
    };

    window.addEventListener('error', handleError, true);

    return () => {
      window.removeEventListener('error', handleError, true);
    };
  }, []);

  return {
    errorDetected,
    errorMessage,
    clearError: () => {
      setErrorDetected(false);
      setErrorMessage('');
    }
  };
}