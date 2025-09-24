#!/usr/bin/env python3
"""
SaaS Control Deck - 统一后端测试服务
整合所有API功能的测试版本
"""

import http.server
import socketserver
import json
import uuid
import urllib.parse
import os
import sys
import traceback
from datetime import datetime, timedelta

# 测试用户数据
TEST_USER = {
    "id": 1,
    "email": "test@saascontrol.dev",
    "password": "TestPass123",
    "full_name": "测试 用户",
    "first_name": "测试",
    "last_name": "用户",
    "is_active": True,
    "email_verified": True,
    "created_at": "2024-01-01T00:00:00Z",
    "avatar_url": None
}

# 存储活跃令牌
active_tokens = {}

# 存储数据
mock_data = {
    "projects": [],
    "data_sources": [],
    "uploads": []
}

class UnifiedHandler(http.server.BaseHTTPRequestHandler):

    def _set_cors_headers(self):
        """设置CORS头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def _send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self._set_cors_headers()
        self.end_headers()

        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))

        # 记录日志
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        print(f'{timestamp} "{self.command} {self.path} HTTP/1.1" {status_code} -')
        sys.stdout.flush()

    def _send_error_response(self, message, status_code=400):
        """发送错误响应"""
        error_data = {"error": message, "status_code": status_code}
        self._send_json_response(error_data, status_code)

    def _authenticate_request(self):
        """验证请求认证"""
        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        token_data = active_tokens.get(token)

        if not token_data:
            return None

        # 检查过期
        if datetime.now() > token_data['expires']:
            del active_tokens[token]
            return None

        return token_data

    def do_OPTIONS(self):
        """处理预检请求"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        """处理GET请求"""
        print(f"📤 GET {self.path}")
        sys.stdout.flush()

        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/health':
            self._handle_health()
        elif path == '/auth/me':
            self._handle_get_current_user()
        elif path.startswith('/api/data'):
            self._handle_get_data()
        elif path.startswith('/data'):
            self._handle_get_data()
        else:
            self._send_error_response("接口不存在", 404)

    def do_POST(self):
        """处理POST请求"""
        print(f"📤 POST {self.path}")
        sys.stdout.flush()

        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/auth/login':
            self._handle_login()
        elif path == '/auth/register':
            self._handle_register()
        elif path == '/auth/refresh':
            self._handle_refresh_token()
        elif path.startswith('/upload'):
            self._handle_upload()
        elif path.startswith('/api/data'):
            self._handle_create_data()
        elif path.startswith('/data'):
            self._handle_create_data()
        else:
            self._send_error_response("接口不存在", 404)

    def _handle_health(self):
        """健康检查"""
        health_data = {
            "status": "healthy",
            "service": "unified-backend",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "features": ["auth", "upload", "data-management"]
        }
        self._send_json_response(health_data)

    def _handle_login(self):
        """处理登录请求"""
        print(f"🔐 收到登录请求")
        sys.stdout.flush()

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            email = data.get('email', '').strip()
            password = data.get('password', '').strip()

            print(f"📧 邮箱: {email}")
            print(f"🔑 密码长度: {len(password)}")
            sys.stdout.flush()

            # 验证凭据
            if email == TEST_USER["email"] and password == TEST_USER["password"]:
                # 生成令牌
                token = f"token_{uuid.uuid4().hex[:16]}"
                refresh_token = f"refresh_{uuid.uuid4().hex[:16]}"

                # 存储令牌
                active_tokens[token] = {
                    "user": TEST_USER.copy(),
                    "expires": datetime.now() + timedelta(minutes=30)
                }

                response_data = {
                    "access_token": token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": 1800,
                    "user": TEST_USER.copy()
                }

                print(f"✅ 登录成功: {email}")
                sys.stdout.flush()
                self._send_json_response(response_data)
            else:
                print(f"❌ 登录失败: 凭据错误")
                sys.stdout.flush()
                self._send_error_response("邮箱或密码错误", 401)

        except Exception as e:
            print(f"❌ 登录处理错误: {e}")
            sys.stdout.flush()
            self._send_error_response("服务器内部错误", 500)

    def _handle_register(self):
        """处理注册请求"""
        print(f"📝 收到注册请求")
        sys.stdout.flush()

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            email = data.get('email', '').strip()
            if not email:
                self._send_error_response("邮箱不能为空", 400)
                return

            response_data = {
                "message": "注册成功",
                "user": {
                    "id": 2,
                    "email": email,
                    "full_name": f"{data.get('first_name', '')} {data.get('last_name', '')}",
                    "is_active": True
                }
            }

            print(f"✅ 注册成功: {email}")
            sys.stdout.flush()
            self._send_json_response(response_data, 201)

        except Exception as e:
            print(f"❌ 注册处理错误: {e}")
            sys.stdout.flush()
            self._send_error_response("注册失败", 500)

    def _handle_refresh_token(self):
        """处理令牌刷新"""
        print(f"🔄 收到令牌刷新请求")
        sys.stdout.flush()

        try:
            new_token = f"token_{uuid.uuid4().hex[:16]}"
            new_refresh_token = f"refresh_{uuid.uuid4().hex[:16]}"

            active_tokens[new_token] = {
                "user": TEST_USER.copy(),
                "expires": datetime.now() + timedelta(minutes=30)
            }

            response_data = {
                "access_token": new_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": 1800,
                "user": TEST_USER.copy()
            }

            print(f"✅ 令牌刷新成功")
            sys.stdout.flush()
            self._send_json_response(response_data)

        except Exception as e:
            print(f"❌ 令牌刷新错误: {e}")
            sys.stdout.flush()
            self._send_error_response("令牌刷新失败", 500)

    def _handle_get_current_user(self):
        """获取当前用户信息"""
        print(f"👤 收到获取用户信息请求")
        sys.stdout.flush()

        auth_data = self._authenticate_request()
        if not auth_data:
            self._send_error_response("未授权", 401)
            return

        self._send_json_response(auth_data["user"])

    def _handle_upload(self):
        """处理文件上传"""
        print(f"📁 收到文件上传请求")
        sys.stdout.flush()

        auth_data = self._authenticate_request()
        if not auth_data:
            self._send_error_response("未授权", 401)
            return

        try:
            # 模拟成功上传
            upload_id = f"upload_{uuid.uuid4().hex[:16]}"
            upload_data = {
                "id": upload_id,
                "filename": "test_data.csv",
                "size": 1024,
                "uploaded_at": datetime.now().isoformat(),
                "status": "completed"
            }

            mock_data["uploads"].append(upload_data)

            response_data = {
                "success": True,
                "message": "文件上传成功",
                "upload": upload_data
            }

            print(f"✅ 文件上传成功")
            sys.stdout.flush()
            self._send_json_response(response_data)

        except Exception as e:
            print(f"❌ 文件上传错误: {e}")
            sys.stdout.flush()
            self._send_error_response("文件上传失败", 500)

    def _handle_create_data(self):
        """创建数据"""
        print(f"📊 收到创建数据请求")
        sys.stdout.flush()

        auth_data = self._authenticate_request()
        if not auth_data:
            self._send_error_response("未授权", 401)
            return

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            data_id = f"data_{uuid.uuid4().hex[:16]}"
            new_data = {
                "id": data_id,
                "name": data.get("name", "新数据"),
                "type": data.get("type", "dataset"),
                "created_at": datetime.now().isoformat(),
                "created_by": auth_data["user"]["email"]
            }

            mock_data["data_sources"].append(new_data)

            print(f"✅ 数据创建成功: {new_data['name']}")
            sys.stdout.flush()
            self._send_json_response(new_data, 201)

        except Exception as e:
            print(f"❌ 数据创建错误: {e}")
            sys.stdout.flush()
            self._send_error_response("数据创建失败", 500)

    def _handle_get_data(self):
        """获取数据"""
        print(f"📋 收到获取数据请求")
        sys.stdout.flush()

        auth_data = self._authenticate_request()
        if not auth_data:
            self._send_error_response("未授权", 401)
            return

        response_data = {
            "data_sources": mock_data["data_sources"],
            "total": len(mock_data["data_sources"])
        }

        print(f"✅ 返回 {len(mock_data['data_sources'])} 条数据")
        sys.stdout.flush()
        self._send_json_response(response_data)

def run_unified_backend():
    """启动统一后端服务器"""
    port = 8002

    print(f"🚀 统一后端测试服务启动于端口 {port}")
    print(f"📍 服务地址: http://localhost:{port}")
    print(f"🔍 健康检查: http://localhost:{port}/health")
    print(f"👤 测试账号: test@saascontrol.dev / TestPass123")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    sys.stdout.flush()

    try:
        with socketserver.TCPServer(("", port), UnifiedHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        sys.stdout.flush()
    except Exception as e:
        print(f"❌ 服务器错误: {e}")
        sys.stdout.flush()

if __name__ == "__main__":
    run_unified_backend()