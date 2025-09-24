#!/usr/bin/env python3
"""
简单认证服务器
用于测试JWT令牌生成和验证
"""

import http.server
import socketserver
import json
import uuid
from datetime import datetime, timedelta
import urllib.parse
import sys

# 测试用户
TEST_USERS = {
    "test@saascontrol.dev": {
        "id": 1,
        "email": "test@saascontrol.dev",
        "password": "TestPass123",
        "full_name": "测试 用户",
        "first_name": "测试",
        "last_name": "用户",
        "is_active": True,
        "email_verified": True,
        "created_at": "2024-01-01T00:00:00Z"
    }
}

# 活跃令牌存储
active_tokens = {}

class SimpleAuthHandler(http.server.BaseHTTPRequestHandler):

    def _set_cors_headers(self):
        """设置CORS头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def _send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self._set_cors_headers()
        self.end_headers()

        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))

    def _send_error_response(self, message, status_code=400):
        """发送错误响应"""
        error_data = {"error": message}
        self._send_json_response(error_data, status_code)

    def do_OPTIONS(self):
        """处理预检请求"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_POST(self):
        """处理POST请求"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        print(f"🔐 POST {path}")
        sys.stdout.flush()

        if path == '/auth/login':
            self._handle_login()
        elif path == '/auth/refresh':
            self._handle_refresh()
        else:
            self._send_error_response("接口不存在", 404)

    def do_GET(self):
        """处理GET请求"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        print(f"📤 GET {path}")
        sys.stdout.flush()

        if path == '/health':
            self._handle_health()
        elif path == '/auth/me':
            self._handle_get_user()
        else:
            self._send_error_response("接口不存在", 404)

    def _handle_health(self):
        """健康检查"""
        health_data = {
            "status": "healthy",
            "service": "simple-auth-server",
            "timestamp": datetime.now().isoformat()
        }
        self._send_json_response(health_data)

    def _handle_login(self):
        """处理登录"""
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            email = data.get('email', '').strip()
            password = data.get('password', '').strip()

            print(f"📧 登录尝试: {email}")
            sys.stdout.flush()

            # 验证用户
            if email in TEST_USERS:
                user = TEST_USERS[email]
                if user['password'] == password:
                    # 生成令牌
                    access_token = f"token_{uuid.uuid4().hex[:16]}"
                    refresh_token = f"refresh_{uuid.uuid4().hex[:16]}"

                    # 存储令牌
                    active_tokens[access_token] = {
                        "user": user,
                        "expires": datetime.now() + timedelta(hours=1)
                    }

                    response_data = {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "token_type": "bearer",
                        "expires_in": 3600,
                        "user": {k: v for k, v in user.items() if k != 'password'}
                    }

                    print(f"✅ 登录成功: {email}")
                    sys.stdout.flush()
                    self._send_json_response(response_data)
                    return

            print(f"❌ 登录失败: {email}")
            sys.stdout.flush()
            self._send_error_response("邮箱或密码错误", 401)

        except Exception as e:
            print(f"❌ 登录错误: {e}")
            sys.stdout.flush()
            self._send_error_response("登录处理失败", 500)

    def _handle_refresh(self):
        """处理令牌刷新"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # 生成新令牌（简化处理）
            new_access_token = f"token_{uuid.uuid4().hex[:16]}"
            new_refresh_token = f"refresh_{uuid.uuid4().hex[:16]}"

            # 使用默认用户
            default_user = TEST_USERS["test@saascontrol.dev"]
            active_tokens[new_access_token] = {
                "user": default_user,
                "expires": datetime.now() + timedelta(hours=1)
            }

            response_data = {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {k: v for k, v in default_user.items() if k != 'password'}
            }

            print(f"🔄 令牌刷新成功")
            sys.stdout.flush()
            self._send_json_response(response_data)

        except Exception as e:
            print(f"❌ 刷新错误: {e}")
            sys.stdout.flush()
            self._send_error_response("令牌刷新失败", 500)

    def _handle_get_user(self):
        """获取当前用户信息"""
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            self._send_error_response("未授权", 401)
            return

        token = auth_header.split(' ')[1]
        token_data = active_tokens.get(token)

        if not token_data:
            self._send_error_response("令牌无效", 401)
            return

        # 检查过期
        if datetime.now() > token_data['expires']:
            del active_tokens[token]
            self._send_error_response("令牌已过期", 401)
            return

        user = token_data['user']
        user_data = {k: v for k, v in user.items() if k != 'password'}

        print(f"👤 获取用户信息: {user['email']}")
        sys.stdout.flush()
        self._send_json_response(user_data)

def run_auth_server():
    """启动认证服务器"""
    port = 8001

    print(f"🔐 简单认证服务器启动于端口 {port}")
    print(f"📍 服务地址: http://localhost:{port}")
    print(f"🔍 健康检查: http://localhost:{port}/health")
    print(f"👤 测试账号: test@saascontrol.dev / TestPass123")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)
    sys.stdout.flush()

    try:
        with socketserver.TCPServer(("", port), SimpleAuthHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 认证服务器已停止")
        sys.stdout.flush()
    except Exception as e:
        print(f"❌ 服务器错误: {e}")
        sys.stdout.flush()

if __name__ == "__main__":
    run_auth_server()