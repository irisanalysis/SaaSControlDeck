/**
 * /frontend/src/app/extension-compatibility/page.tsx
 * 浏览器扩展兼容性检测和故障排除页面，帮助用户诊断和解决扩展冲突问题
 * 提供详细的扩展分析、风险评估和解决建议
 * RELEVANT FILES: /frontend/src/hooks/use-extension-compatibility.tsx, /frontend/src/lib/utils/extension-detector.ts
 */

"use client";

import React, { useState } from 'react';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  Info,
  Download,
  RefreshCw,
  Chrome,
  Globe
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useExtensionCompatibility } from '@/hooks/use-extension-compatibility';

function ExtensionCompatibilityPage() {
  const {
    browser,
    extensions,
    errorCount,
    hasHighRiskExtensions,
    lastError,
    isMonitoring,
    clearErrors,
    generateReport
  } = useExtensionCompatibility();

  const [reportDownloaded, setReportDownloaded] = useState(false);

  const getBrowserIcon = (browserName: string) => {
    switch (browserName.toLowerCase()) {
      case 'chrome': return <Chrome className="w-5 h-5" />;
      case 'firefox': return <Globe className="w-5 h-5 text-orange-500" />;
      case 'safari': return <Globe className="w-5 h-5 text-blue-500" />;
      case 'edge': return <Globe className="w-5 h-5 text-blue-600" />;
      default: return <Globe className="w-5 h-5" />;
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const downloadReport = () => {
    const report = generateReport();
    const blob = new Blob([report], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `saas-control-deck-extension-report-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setReportDownloaded(true);
    setTimeout(() => setReportDownloaded(false), 3000);
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">浏览器扩展兼容性</h1>
          <p className="text-muted-foreground">
            检测和解决浏览器扩展可能产生的冲突问题
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={clearErrors} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            清除错误
          </Button>
          <Button
            onClick={downloadReport}
            variant="outline"
            size="sm"
            className={reportDownloaded ? 'bg-green-50 text-green-700' : ''}
          >
            <Download className="w-4 h-4 mr-2" />
            {reportDownloaded ? '已下载' : '下载报告'}
          </Button>
        </div>
      </div>

      {/* 状态概览 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              {getBrowserIcon(browser.name)}
              <div>
                <div className="text-2xl font-bold">{browser.name}</div>
                <p className="text-xs text-muted-foreground">版本 {browser.version}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-blue-600" />
              <div>
                <div className="text-2xl font-bold">{extensions.length}</div>
                <p className="text-xs text-muted-foreground">检测到的扩展</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              {hasHighRiskExtensions ? (
                <AlertTriangle className="w-5 h-5 text-red-600" />
              ) : (
                <CheckCircle className="w-5 h-5 text-green-600" />
              )}
              <div>
                <div className="text-2xl font-bold">
                  {hasHighRiskExtensions ? '中等' : '良好'}
                </div>
                <p className="text-xs text-muted-foreground">兼容性状态</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2">
              <Info className="w-5 h-5 text-gray-600" />
              <div>
                <div className="text-2xl font-bold">{errorCount}</div>
                <p className="text-xs text-muted-foreground">扩展错误计数</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 错误警告 */}
      {errorCount > 0 && (
        <Alert className="border-yellow-200 bg-yellow-50">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>检测到扩展错误</AlertTitle>
          <AlertDescription>
            共检测到 {errorCount} 个与浏览器扩展相关的错误。这些错误已被自动隔离，不会影响应用功能。
            {lastError && (
              <div className="mt-2 text-sm font-mono bg-yellow-100 p-2 rounded">
                最新错误: {lastError.slice(0, 100)}...
              </div>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* 详细信息 */}
      <Tabs defaultValue="extensions" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="extensions">扩展详情</TabsTrigger>
          <TabsTrigger value="recommendations">解决建议</TabsTrigger>
          <TabsTrigger value="troubleshooting">故障排除</TabsTrigger>
        </TabsList>

        <TabsContent value="extensions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>检测到的浏览器扩展</CardTitle>
            </CardHeader>
            <CardContent>
              {extensions.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  未检测到已知的浏览器扩展
                </div>
              ) : (
                <div className="space-y-4">
                  {extensions.map((ext, index) => (
                    <div key={index} className={`border rounded-lg p-4 ${getRiskColor(ext.risk_level)}`}>
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold">{ext.name}</h3>
                        <Badge variant={ext.risk_level === 'high' ? 'destructive' :
                                      ext.risk_level === 'medium' ? 'secondary' : 'default'}>
                          {ext.risk_level === 'high' ? '高风险' :
                           ext.risk_level === 'medium' ? '中等风险' : '低风险'}
                        </Badge>
                      </div>
                      <p className="text-sm mb-3">{ext.description}</p>

                      {ext.potential_issues.length > 0 && (
                        <div className="mb-3">
                          <h4 className="font-medium text-sm mb-1">潜在问题:</h4>
                          <ul className="text-xs list-disc list-inside space-y-1">
                            {ext.potential_issues.map((issue, i) => (
                              <li key={i}>{issue}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {ext.recommendations.length > 0 && (
                        <div>
                          <h4 className="font-medium text-sm mb-1">建议:</h4>
                          <ul className="text-xs list-disc list-inside space-y-1">
                            {ext.recommendations.map((rec, i) => (
                              <li key={i}>{rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>通用解决建议</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold mb-2 flex items-center">
                    <CheckCircle className="w-4 h-4 mr-2 text-green-600" />
                    立即可行的解决方案
                  </h3>
                  <ul className="text-sm space-y-2 text-muted-foreground">
                    <li>• 在隐身模式下使用应用（自动禁用大部分扩展）</li>
                    <li>• 将应用域名添加到扩展白名单</li>
                    <li>• 暂时禁用非必要的浏览器扩展</li>
                    <li>• 刷新页面以清除临时错误</li>
                  </ul>
                </div>

                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold mb-2 flex items-center">
                    <Shield className="w-4 h-4 mr-2 text-blue-600" />
                    长期最佳实践
                  </h3>
                  <ul className="text-sm space-y-2 text-muted-foreground">
                    <li>• 定期审查已安装的浏览器扩展</li>
                    <li>• 保持浏览器和扩展更新到最新版本</li>
                    <li>• 使用可信来源的扩展</li>
                    <li>• 为重要应用创建专用的浏览器配置文件</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="troubleshooting" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>故障排除步骤</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold mb-3">步骤 1: 快速诊断</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Button variant="outline" className="justify-start">
                      <RefreshCw className="w-4 h-4 mr-2" />
                      硬刷新页面 (Ctrl+F5)
                    </Button>
                    <Button variant="outline" className="justify-start">
                      <Globe className="w-4 h-4 mr-2" />
                      检查网络连接
                    </Button>
                    <Button variant="outline" className="justify-start">
                      <Shield className="w-4 h-4 mr-2" />
                      尝试隐身模式
                    </Button>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-3">步骤 2: 扩展管理</h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium mb-2">Chrome 用户:</h4>
                    <ol className="text-sm space-y-1 list-decimal list-inside text-muted-foreground">
                      <li>打开 chrome://extensions/</li>
                      <li>暂时禁用所有扩展</li>
                      <li>测试应用功能是否正常</li>
                      <li>逐个启用扩展以找出冲突源</li>
                    </ol>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-3">步骤 3: 高级诊断</h3>
                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertTitle>开发者工具诊断</AlertTitle>
                    <AlertDescription className="mt-2">
                      <ol className="list-decimal list-inside space-y-1 text-sm">
                        <li>按 F12 打开开发者工具</li>
                        <li>切换到 Console 标签</li>
                        <li>查找以 &quot;content_script&quot; 开头的错误信息</li>
                        <li>记录错误信息并联系技术支持</li>
                      </ol>
                    </AlertDescription>
                  </Alert>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 监控状态 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isMonitoring ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
              <span className="text-sm">
                扩展错误监控: {isMonitoring ? '运行中' : '已停止'}
              </span>
            </div>
            <div className="text-xs text-muted-foreground">
              SaaS Control Deck 自动保护您的应用体验
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default ExtensionCompatibilityPage;