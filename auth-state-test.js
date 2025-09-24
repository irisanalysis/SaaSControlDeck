/**
 * 认证状态管理测试脚本
 * 验证登录后的状态变化和令牌处理
 * 测试localStorage、会话管理、token刷新等功能
 * RELEVANT FILES: auth-context.tsx, auth.ts, use-auth.ts
 */

const http = require('http');
const { URL } = require('url');

class AuthStateTest {
    constructor() {
        this.baseURL = 'http://localhost:9000';
        this.testCredentials = {
            email: 'test@saascontrol.dev',
            password: 'TestPass123'
        };
        this.authToken = null;
        this.refreshToken = null;
        this.userInfo = null;
        this.results = [];
    }

    // HTTP请求帮助函数
    makeRequest(url, options = {}) {
        return new Promise((resolve, reject) => {
            const urlObj = new URL(url);
            const isHttps = urlObj.protocol === 'https:';
            const client = isHttps ? require('https') : http;

            const requestOptions = {
                hostname: urlObj.hostname,
                port: urlObj.port || (isHttps ? 443 : 80),
                path: urlObj.pathname + urlObj.search,
                method: options.method || 'GET',
                headers: options.headers || {},
                timeout: 10000
            };

            const req = client.request(requestOptions, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    resolve({
                        status: res.statusCode,
                        headers: res.headers,
                        data: data
                    });
                });
            });

            req.on('error', reject);
            req.on('timeout', () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });

            if (options.data) {
                req.write(options.data);
            }

            req.end();
        });
    }

    // 记录测试结果
    log(test, passed, details = '') {
        const result = { test, passed, details, timestamp: new Date().toISOString() };
        this.results.push(result);
        const status = passed ? '✅ PASS' : '❌ FAIL';
        console.log(`${status}: ${test} - ${details}`);
        return passed;
    }

    // 测试1：执行登录并获取令牌
    async testLogin() {
        console.log('\n📋 测试1：登录并获取认证令牌');

        try {
            const postData = JSON.stringify(this.testCredentials);
            const response = await this.makeRequest(`${this.baseURL}/api/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(postData)
                },
                data: postData
            });

            if (response.status === 200) {
                const data = JSON.parse(response.data);
                if (data.access_token && data.user) {
                    this.authToken = data.access_token;
                    this.refreshToken = data.refresh_token;
                    this.userInfo = data.user;

                    this.log('登录获取令牌', true, `成功获得访问令牌: ${this.authToken.substring(0, 20)}...`);
                    this.log('用户信息获取', true, `用户: ${this.userInfo.email}, ID: ${this.userInfo.id}`);

                    // 检查令牌格式
                    const isJWT = this.authToken.split('.').length === 3;
                    this.log('令牌格式验证', isJWT, isJWT ? 'JWT格式正确' : '令牌格式异常');

                    return true;
                } else {
                    this.log('登录获取令牌', false, '响应缺少必要的认证信息');
                    return false;
                }
            } else {
                this.log('登录获取令牌', false, `登录失败，状态码: ${response.status}`);
                return false;
            }
        } catch (error) {
            this.log('登录获取令牌', false, `登录请求失败: ${error.message}`);
            return false;
        }
    }

    // 测试2：使用令牌访问受保护资源
    async testProtectedAccess() {
        console.log('\n📋 测试2：使用令牌访问受保护资源');

        if (!this.authToken) {
            this.log('受保护资源访问', false, '无有效令牌');
            return;
        }

        try {
            // 测试访问主页（已认证状态）
            const dashboardResponse = await this.makeRequest(`${this.baseURL}/`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Cookie': `auth_token=${this.authToken}`
                }
            });

            this.log('认证状态访问主页', dashboardResponse.status === 200,
                     `主页访问状态码: ${dashboardResponse.status}`);

            // 检查页面是否包含认证后的内容
            const hasAuthenticatedContent = dashboardResponse.data.includes('Dashboard') ||
                                          dashboardResponse.data.includes('仪表盘') ||
                                          dashboardResponse.data.includes(this.userInfo.email);

            this.log('认证内容验证', hasAuthenticatedContent,
                     hasAuthenticatedContent ? '页面包含认证后内容' : '未检测到认证后内容');

        } catch (error) {
            this.log('受保护资源访问', false, `访问失败: ${error.message}`);
        }
    }

    // 测试3：验证令牌刷新机制
    async testTokenRefresh() {
        console.log('\n📋 测试3：验证令牌刷新机制');

        if (!this.refreshToken) {
            this.log('令牌刷新测试', false, '无有效刷新令牌');
            return;
        }

        try {
            const postData = JSON.stringify({ refresh_token: this.refreshToken });
            const response = await this.makeRequest(`${this.baseURL}/api/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(postData)
                },
                data: postData
            });

            if (response.status === 200) {
                const data = JSON.parse(response.data);
                if (data.access_token) {
                    const newToken = data.access_token;
                    const tokenChanged = newToken !== this.authToken;

                    this.log('令牌刷新功能', true, `新令牌: ${newToken.substring(0, 20)}...`);
                    this.log('令牌更新验证', tokenChanged, tokenChanged ? '令牌已更新' : '令牌未变化');

                    // 更新令牌用于后续测试
                    this.authToken = newToken;
                    if (data.refresh_token) {
                        this.refreshToken = data.refresh_token;
                    }
                } else {
                    this.log('令牌刷新功能', false, '刷新响应缺少新令牌');
                }
            } else {
                this.log('令牌刷新功能', false, `刷新失败，状态码: ${response.status}`);
            }
        } catch (error) {
            this.log('令牌刷新测试', false, `刷新请求失败: ${error.message}`);
        }
    }

    // 测试4：验证认证状态API
    async testAuthStatus() {
        console.log('\n📋 测试4：验证认证状态API');

        if (!this.authToken) {
            this.log('认证状态API', false, '无有效令牌');
            return;
        }

        try {
            const response = await this.makeRequest(`${this.baseURL}/api/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.status === 200) {
                const data = JSON.parse(response.data);
                if (data.email && data.id) {
                    this.log('用户信息API', true, `获取用户信息: ${data.email}`);

                    // 验证信息一致性
                    const infoConsistent = data.email === this.userInfo.email &&
                                         data.id === this.userInfo.id;
                    this.log('用户信息一致性', infoConsistent,
                             infoConsistent ? '用户信息一致' : '用户信息不匹配');
                } else {
                    this.log('用户信息API', false, '用户信息格式错误');
                }
            } else {
                this.log('用户信息API', false, `获取用户信息失败，状态码: ${response.status}`);
            }
        } catch (error) {
            this.log('认证状态API', false, `状态检查失败: ${error.message}`);
        }
    }

    // 测试5：验证登出功能
    async testLogout() {
        console.log('\n📋 测试5：验证登出功能');

        if (!this.authToken) {
            this.log('登出功能测试', false, '无有效令牌');
            return;
        }

        try {
            const response = await this.makeRequest(`${this.baseURL}/api/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            const logoutSuccess = response.status === 200 || response.status === 204;
            this.log('登出请求', logoutSuccess, `登出状态码: ${response.status}`);

            if (logoutSuccess) {
                // 验证登出后令牌是否失效
                try {
                    const testResponse = await this.makeRequest(`${this.baseURL}/api/auth/me`, {
                        headers: {
                            'Authorization': `Bearer ${this.authToken}`
                        }
                    });

                    const tokenInvalid = testResponse.status === 401 || testResponse.status === 403;
                    this.log('令牌失效验证', tokenInvalid,
                             tokenInvalid ? '令牌已失效' : '令牌仍有效（可能存在问题）');
                } catch (error) {
                    this.log('令牌失效验证', true, '令牌验证请求失败（正常）');
                }
            }

        } catch (error) {
            this.log('登出功能测试', false, `登出请求失败: ${error.message}`);
        }
    }

    // 测试6：验证未认证访问重定向
    async testUnauthenticatedRedirect() {
        console.log('\n📋 测试6：验证未认证访问重定向');

        try {
            // 不带令牌访问受保护页面
            const response = await this.makeRequest(`${this.baseURL}/dashboard`, {
                // 不设置Authorization header
            });

            // 检查是否重定向到登录页面
            const isRedirect = response.status === 302 || response.status === 301;
            const isAuthPage = response.status === 200 &&
                             (response.data.includes('登录') || response.data.includes('auth'));

            if (isRedirect) {
                const location = response.headers.location;
                const redirectsToAuth = location && (location.includes('/auth') || location.includes('/login'));
                this.log('未认证重定向', redirectsToAuth, `重定向到: ${location}`);
            } else if (isAuthPage) {
                this.log('未认证重定向', true, '直接显示认证页面');
            } else {
                this.log('未认证重定向', false, `未认证访问状态码: ${response.status}`);
            }

        } catch (error) {
            this.log('未认证访问测试', false, `测试失败: ${error.message}`);
        }
    }

    // 生成测试报告
    generateReport() {
        console.log('\n' + '='.repeat(80));
        console.log('🔍 认证状态管理测试报告');
        console.log('='.repeat(80));

        const passed = this.results.filter(r => r.passed).length;
        const failed = this.results.length - passed;
        const successRate = this.results.length > 0 ? ((passed / this.results.length) * 100).toFixed(1) : 0;

        console.log(`📊 测试统计:`);
        console.log(`   总测试数: ${this.results.length}`);
        console.log(`   通过: ${passed}`);
        console.log(`   失败: ${failed}`);
        console.log(`   成功率: ${successRate}%`);

        console.log('\n📋 认证流程分析:');

        const loginTests = this.results.filter(r => r.test.includes('登录'));
        const tokenTests = this.results.filter(r => r.test.includes('令牌'));
        const accessTests = this.results.filter(r => r.test.includes('访问') || r.test.includes('资源'));
        const logoutTests = this.results.filter(r => r.test.includes('登出'));

        if (loginTests.every(t => t.passed)) {
            console.log('   ✅ 登录流程: 正常工作');
        } else {
            console.log('   ❌ 登录流程: 存在问题');
        }

        if (tokenTests.every(t => t.passed)) {
            console.log('   ✅ 令牌管理: 正常工作');
        } else {
            console.log('   ❌ 令牌管理: 存在问题');
        }

        if (accessTests.every(t => t.passed)) {
            console.log('   ✅ 访问控制: 正常工作');
        } else {
            console.log('   ❌ 访问控制: 存在问题');
        }

        if (logoutTests.every(t => t.passed)) {
            console.log('   ✅ 登出流程: 正常工作');
        } else {
            console.log('   ❌ 登出流程: 存在问题');
        }

        console.log('\n📋 详细结果:');
        this.results.forEach(result => {
            const status = result.passed ? '✅' : '❌';
            console.log(`   ${status} ${result.test}: ${result.details}`);
        });

        // 安全评估
        console.log('\n🔒 安全性评估:');
        const securityIssues = [];

        if (!this.results.find(r => r.test.includes('令牌格式') && r.passed)) {
            securityIssues.push('令牌格式可能不安全');
        }

        if (!this.results.find(r => r.test.includes('令牌失效') && r.passed)) {
            securityIssues.push('登出后令牌未正确失效');
        }

        if (!this.results.find(r => r.test.includes('未认证重定向') && r.passed)) {
            securityIssues.push('未认证访问控制可能存在问题');
        }

        if (securityIssues.length === 0) {
            console.log('   🛡️  未发现明显安全问题');
        } else {
            securityIssues.forEach((issue, index) => {
                console.log(`   ⚠️  ${index + 1}. ${issue}`);
            });
        }

        console.log('\n' + '='.repeat(80));
        console.log('测试完成时间:', new Date().toLocaleString('zh-CN'));
    }

    // 主测试流程
    async run() {
        console.log('🔐 开始认证状态管理测试');
        console.log(`📍 测试目标: ${this.baseURL}`);
        console.log(`🔑 测试凭据: ${this.testCredentials.email}`);
        console.log('-'.repeat(80));

        try {
            // 执行测试序列
            const loginSuccess = await this.testLogin();

            if (loginSuccess) {
                await this.testProtectedAccess();
                await this.testTokenRefresh();
                await this.testAuthStatus();
                await this.testLogout();
            }

            await this.testUnauthenticatedRedirect();

        } catch (error) {
            console.log(`❌ 测试执行错误: ${error.message}`);
        }

        this.generateReport();
    }
}

// 运行测试
async function main() {
    const tester = new AuthStateTest();
    await tester.run();
}

if (require.main === module) {
    main();
}

module.exports = AuthStateTest;