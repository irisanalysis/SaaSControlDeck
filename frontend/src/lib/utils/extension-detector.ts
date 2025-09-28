/**
 * /frontend/src/lib/utils/extension-detector.ts
 * 浏览器扩展检测和兼容性工具，分析常见扩展冲突并提供解决建议
 * 帮助识别可能影响SaaS Control Deck的扩展，提供用户指导
 * RELEVANT FILES: /frontend/src/components/guards/browser-extension-guard.tsx, /frontend/src/hooks/use-extension-compatibility.tsx
 */

export interface ExtensionInfo {
  name: string;
  detected: boolean;
  risk_level: 'low' | 'medium' | 'high';
  description: string;
  potential_issues: string[];
  recommendations: string[];
}

export interface BrowserInfo {
  name: string;
  version: string;
  vendor: string;
  is_extension_capable: boolean;
}

/**
 * 检测常见的浏览器扩展特征
 */
export function detectBrowserExtensions(): ExtensionInfo[] {
  const extensions: ExtensionInfo[] = [];

  // 检测AdBlock类扩展
  if (typeof window !== 'undefined') {
    // AdBlock Plus / uBlock Origin
    const hasAdBlocker = !!(
      // @ts-ignore
      window.adblockplusChrome ||
      // @ts-ignore
      window.ublock ||
      document.querySelector('div[id*="adblock"]') ||
      document.querySelector('script[src*="adblock"]')
    );

    if (hasAdBlocker) {
      extensions.push({
        name: 'AdBlock/uBlock',
        detected: true,
        risk_level: 'low',
        description: '广告拦截扩展',
        potential_issues: ['可能拦截某些API请求', '可能影响页面加载性能'],
        recommendations: [
          '将 localhost 和应用域名添加到白名单',
          '检查是否拦截了API请求'
        ]
      });
    }

    // 检测开发者工具扩展
    const hasDevTools = !!(
      // @ts-ignore
      window.devtools ||
      // @ts-ignore
      window.__REACT_DEVTOOLS_GLOBAL_HOOK__ ||
      // @ts-ignore
      window.__VUE_DEVTOOLS_GLOBAL_HOOK__
    );

    if (hasDevTools) {
      extensions.push({
        name: 'Developer Tools Extension',
        detected: true,
        risk_level: 'low',
        description: '开发者工具扩展 (React/Vue DevTools等)',
        potential_issues: ['可能在控制台产生调试信息'],
        recommendations: [
          '这些扩展通常对应用无害',
          '可以忽略相关的控制台消息'
        ]
      });
    }

    // 检测语法检查扩展 (Grammarly等)
    const hasGrammarChecker = !!(
      document.querySelector('div[data-grammarly-part]') ||
      document.querySelector('grammarly-extension') ||
      // @ts-ignore
      window.grammarly
    );

    if (hasGrammarChecker) {
      extensions.push({
        name: 'Grammar Checker',
        detected: true,
        risk_level: 'medium',
        description: '语法检查扩展 (如Grammarly)',
        potential_issues: [
          '可能修改表单输入',
          '可能注入DOM元素',
          '可能产生网络请求冲突'
        ],
        recommendations: [
          '在敏感页面暂时禁用',
          '确保表单验证正常工作'
        ]
      });
    }

    // 检测密码管理器
    const hasPasswordManager = !!(
      document.querySelector('input[data-1password]') ||
      document.querySelector('input[data-lastpass]') ||
      document.querySelector('div[data-dashlane]') ||
      // @ts-ignore
      window._1PasswordExtension ||
      // @ts-ignore
      window.LP_
    );

    if (hasPasswordManager) {
      extensions.push({
        name: 'Password Manager',
        detected: true,
        risk_level: 'low',
        description: '密码管理器扩展',
        potential_issues: ['可能修改登录表单', '可能注入填充脚本'],
        recommendations: [
          '确保登录功能正常',
          '检查自动填充是否正确'
        ]
      });
    }

    // 检测翻译扩展
    const hasTranslator = !!(
      document.querySelector('div[id*="translate"]') ||
      document.querySelector('div[class*="translate"]') ||
      // @ts-ignore
      window.google && window.google.translate
    );

    if (hasTranslator) {
      extensions.push({
        name: 'Translation Extension',
        detected: true,
        risk_level: 'medium',
        description: '翻译扩展',
        potential_issues: [
          '可能修改页面文本',
          '可能影响布局和样式',
          '可能产生网络请求'
        ],
        recommendations: [
          '如果界面显示异常，尝试禁用翻译',
          '确保数据显示正确'
        ]
      });
    }

    // 检测VPN/代理扩展
    const hasVPN = !!(
      // @ts-ignore
      window.webRTCDetector ||
      document.querySelector('div[id*="vpn"]') ||
      document.querySelector('div[id*="proxy"]')
    );

    if (hasVPN) {
      extensions.push({
        name: 'VPN/Proxy Extension',
        detected: true,
        risk_level: 'high',
        description: 'VPN或代理扩展',
        potential_issues: [
          '可能影响API请求',
          '可能导致网络超时',
          '可能影响地理位置检测'
        ],
        recommendations: [
          '如果遇到连接问题，尝试关闭VPN',
          '确保后端API可以正常访问'
        ]
      });
    }
  }

  return extensions;
}

/**
 * 获取浏览器信息
 */
export function getBrowserInfo(): BrowserInfo {
  if (typeof window === 'undefined') {
    return {
      name: 'Unknown',
      version: 'Unknown',
      vendor: 'Unknown',
      is_extension_capable: false
    };
  }

  const userAgent = navigator.userAgent;
  const vendor = navigator.vendor || '';

  let browserName = 'Unknown';
  let browserVersion = 'Unknown';

  // Chrome
  if (userAgent.includes('Chrome') && vendor.includes('Google')) {
    browserName = 'Chrome';
    const match = userAgent.match(/Chrome\/(\d+)/);
    browserVersion = match ? match[1] : 'Unknown';
  }
  // Firefox
  else if (userAgent.includes('Firefox')) {
    browserName = 'Firefox';
    const match = userAgent.match(/Firefox\/(\d+)/);
    browserVersion = match ? match[1] : 'Unknown';
  }
  // Safari
  else if (userAgent.includes('Safari') && vendor.includes('Apple')) {
    browserName = 'Safari';
    const match = userAgent.match(/Version\/(\d+)/);
    browserVersion = match ? match[1] : 'Unknown';
  }
  // Edge
  else if (userAgent.includes('Edg')) {
    browserName = 'Edge';
    const match = userAgent.match(/Edg\/(\d+)/);
    browserVersion = match ? match[1] : 'Unknown';
  }

  return {
    name: browserName,
    version: browserVersion,
    vendor: vendor,
    is_extension_capable: ['Chrome', 'Firefox', 'Safari', 'Edge'].includes(browserName)
  };
}

/**
 * 分析扩展兼容性风险
 */
export function analyzeExtensionRisks(extensions: ExtensionInfo[]): {
  total_extensions: number;
  risk_summary: Record<string, number>;
  high_risk_extensions: ExtensionInfo[];
  recommendations: string[];
} {
  const riskCounts = extensions.reduce((acc, ext) => {
    acc[ext.risk_level] = (acc[ext.risk_level] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const highRiskExtensions = extensions.filter(ext => ext.risk_level === 'high');

  const generalRecommendations = [
    '如果遇到意外错误，尝试在隐身模式下使用应用',
    '定期检查浏览器扩展，禁用不必要的扩展',
    '重要操作时可以暂时禁用所有扩展',
    '保持浏览器和扩展更新到最新版本'
  ];

  return {
    total_extensions: extensions.length,
    risk_summary: riskCounts,
    high_risk_extensions: highRiskExtensions,
    recommendations: generalRecommendations
  };
}

/**
 * 生成扩展兼容性报告
 */
export function generateCompatibilityReport(): {
  browser: BrowserInfo;
  extensions: ExtensionInfo[];
  risk_analysis: ReturnType<typeof analyzeExtensionRisks>;
  generated_at: string;
} {
  const browser = getBrowserInfo();
  const extensions = detectBrowserExtensions();
  const riskAnalysis = analyzeExtensionRisks(extensions);

  return {
    browser,
    extensions,
    risk_analysis: riskAnalysis,
    generated_at: new Date().toISOString()
  };
}

/**
 * 检查是否可能是扩展相关的错误
 */
export function isExtensionRelatedError(error: Error | string): boolean {
  const message = typeof error === 'string' ? error : error.message;
  const stack = typeof error === 'object' && error.stack ? error.stack : '';

  const extensionIndicators = [
    'content_script',
    'chrome-extension',
    'moz-extension',
    'safari-extension',
    'extension://',
    'Failed to fetch',
    'NetworkError',
    'Load failed'
  ];

  return extensionIndicators.some(indicator =>
    message.includes(indicator) || stack.includes(indicator)
  );
}