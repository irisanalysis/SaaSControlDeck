#!/usr/bin/env python3
"""
SaaS Control Deck - 统一后端服务
临时简化版本，整合所有功能到单一文件
支持认证、文件上传、数据管理功能
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
import cgi
import io
import tempfile
import mimetypes

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

# 存储上传的文件信息
uploaded_files = {}

# 存储数据源信息
data_sources = {}

class UnifiedBackendHandler(http.server.BaseHTTPRequestHandler):

    def _set_cors_headers(self):
        """设置CORS头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def _send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self._set_cors_headers()
        self.end_headers()

        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))

        # 记录响应日志
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
        return active_tokens.get(token)

    def _log_request(self):
        """记录请求日志"""
        print(f"📤 {self.command} {self.path}")
        sys.stdout.flush()

    def do_OPTIONS(self):
        """处理预检请求"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        """处理GET请求"""
        self._log_request()

        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/health':
            self._handle_health()
        elif path == '/auth/me':
            self._handle_get_current_user()
        elif path.startswith('/data/sources'):
            self._handle_get_data_sources()
        elif path.startswith('/data/'):
            self._handle_get_data()
        else:
            self._send_error_response("接口不存在", 404)

    def do_POST(self):
        """处理POST请求"""
        self._log_request()

        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/auth/login':
            self._handle_login()
        elif path == '/auth/register':
            self._handle_register()
        elif path == '/auth/refresh':
            self._handle_refresh_token()
        elif path == '/auth/logout':
            self._handle_logout()
        elif path.startswith('/upload'):
            self._handle_file_upload()
        elif path.startswith('/data/sources'):
            self._handle_create_data_source()
        else:
            self._send_error_response("接口不存在", 404)

    def do_DELETE(self):
        """处理DELETE请求"""
        self._log_request()

        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path.startswith('/data/sources/'):
            self._handle_delete_data_source()
        else:
            self._send_error_response("接口不存在", 404)

    def _handle_health(self):
        """健康检查"""
        health_data = {
            "status": "healthy",
            "service": "unified-backend-service",
            "port": 8000,
            "features": ["authentication", "file-upload", "data-management"]
        }
        self._send_json_response(health_data)

    def _handle_login(self):
        """处理登录请求 - 简化版本"""
        print(f"🔐 收到登录请求")
        sys.stdout.flush()

        # 简化错误处理
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                print("❌ 无请求体")
                sys.stdout.flush()
                self._send_error_response("缺少请求数据", 400)
                return

            post_data = self.rfile.read(content_length)
            raw_data = post_data.decode('utf-8')
            print(f"📄 请求数据长度: {len(raw_data)}")
            sys.stdout.flush()

            # 解析JSON数据
            data = json.loads(raw_data)
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

        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {e}")
            sys.stdout.flush()
            self._send_error_response("请求数据格式错误", 400)
        except Exception as e:
            print(f"❌ 登录处理错误: {e}")
            print(f"错误详情: {traceback.format_exc()}")
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

            # 简单验证
            email = data.get('email', '').strip()
            if not email:
                self._send_error_response("邮箱不能为空", 400)
                return

            # 模拟注册成功
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
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # 生成新令牌
            new_token = f"token_{uuid.uuid4().hex[:16]}"
            new_refresh_token = f"refresh_{uuid.uuid4().hex[:16]}"

            # 存储新令牌
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

    def _handle_logout(self):
        """处理登出请求"""
        print(f"👋 收到登出请求")
        sys.stdout.flush()

        # 清除令牌（简化处理）
        auth_data = self._authenticate_request()
        if auth_data:
            # 在实际应用中，这里会清除对应的令牌
            pass

        response_data = {"message": "登出成功"}
        print(f"✅ 登出成功")
        sys.stdout.flush()
        self._send_json_response(response_data)

    def _handle_get_current_user(self):
        """获取当前用户信息"""
        print(f"👤 收到获取用户信息请求")
        sys.stdout.flush()

        auth_data = self._authenticate_request()
        if not auth_data:
            self._send_error_response("未授权", 401)
            return

        self._send_json_response(auth_data["user"])

    def _handle_file_upload(self):
        """处理文件上传"""
        print(f"📁 收到文件上传请求")
        sys.stdout.flush()

        # 验证认证
        auth_data = self._authenticate_request()
        if not auth_data:
            self._send_error_response("未授权", 401)
            return

        try:
            # 获取content-type
            content_type = self.headers.get('content-type')
            if not content_type or not content_type.startswith('multipart/form-data'):
                self._send_error_response("必须使用multipart/form-data上传", 400)
                return

            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            # 解析multipart数据
            boundary = content_type.split('boundary=')[1].encode()
            parts = post_data.split(b'--' + boundary)

            uploaded_file_info = None

            for part in parts[1:-1]:  # 跳过开始和结束部分
                if b'Content-Disposition' not in part:
                    continue

                # 分离头部和内容
                header_end = part.find(b'\r\n\r\n')
                if header_end == -1:
                    continue

                headers = part[:header_end].decode('utf-8')
                content = part[header_end + 4:]

                # 去除末尾的\r\n
                if content.endswith(b'\r\n'):
                    content = content[:-2]

                # 解析文件信息
                if 'filename=' in headers:
                    filename_start = headers.find('filename="') + 10
                    filename_end = headers.find('"', filename_start)
                    filename = headers[filename_start:filename_end]

                    if filename:
                        # 生成文件ID
                        file_id = f"file_{uuid.uuid4().hex[:16]}"

                        # 存储文件信息（实际应用中会保存到磁盘）
                        uploaded_files[file_id] = {
                            "id": file_id,
                            "filename": filename,
                            "size": len(content),
                            "content_type": self._guess_content_type(filename),
                            "uploaded_at": datetime.now().isoformat(),
                            "uploaded_by": auth_data["user"]["email"]
                        }

                        uploaded_file_info = uploaded_files[file_id]
                        break

            if uploaded_file_info:
                response_data = {
                    "success": True,
                    "message": "文件上传成功",
                    "file": uploaded_file_info
                }
                print(f"✅ 文件上传成功: {uploaded_file_info['filename']}")
                sys.stdout.flush()
                self._send_json_response(response_data)
            else:
                self._send_error_response("未找到有效文件", 400)

        except Exception as e:
            print(f"❌ 文件上传错误: {e}")
            print(f"错误详情: {traceback.format_exc()}")
            sys.stdout.flush()
            self._send_error_response("文件上传失败", 500)

    def _guess_content_type(self, filename):
        """猜测文件MIME类型"""
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def _handle_create_data_source(self):
        """创建数据源"""
        print(f"📊 收到创建数据源请求")
        sys.stdout.flush()

        # 验证认证
        auth_data = self._authenticate_request()
        if not auth_data:
            self._send_error_response("未授权", 401)
            return

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # 生成数据源ID
            source_id = f"ds_{uuid.uuid4().hex[:16]}"

            # 创建数据源
            data_source = {
                "id": source_id,
                "name": data.get("name", "未命名数据源"),
                "description": data.get("description", ""),
                "type": data.get("type", "file"),
                "file_id": data.get("file_id"),
                "created_at": datetime.now().isoformat(),
                "created_by": auth_data["user"]["email"],
                "status": "active",
                "row_count": 0,
                "column_count": 0
            }

            # 如果关联了文件，添加文件信息
            if data_source["file_id"] and data_source["file_id"] in uploaded_files:
                file_info = uploaded_files[data_source["file_id"]]
                data_source["file_info"] = file_info
                # 模拟解析文件内容
                data_source["row_count"] = 100  # 模拟数据
                data_source["column_count"] = 5

            # 存储数据源
            data_sources[source_id] = data_source

            print(f"✅ 数据源创建成功: {data_source['name']}")
            sys.stdout.flush()
            self._send_json_response(data_source, 201)

        except Exception as e:
            print(f"❌ 创建数据源错误: {e}")
            sys.stdout.flush()
            self._send_error_response("创建数据源失败", 500)

    def _handle_get_data_sources(self):
        """获取数据源列表"""
        print(f"📋 收到获取数据源列表请求")
        sys.stdout.flush()

        # 验证认证
        auth_data = self._authenticate_request()
        if not auth_data:
            self._send_error_response("未授权", 401)
            return

        # 返回当前用户的数据源
        user_sources = [
            source for source in data_sources.values()
            if source["created_by"] == auth_data["user"]["email"]
        ]

        response_data = {
            "data_sources": user_sources,
            "total": len(user_sources)
        }

        print(f"✅ 返回 {len(user_sources)} 个数据源")
        sys.stdout.flush()
        self._send_json_response(response_data)

    def _handle_delete_data_source(self):
        """删除数据源"""
        print(f"🗑️ 收到删除数据源请求")
        sys.stdout.flush()

        # 验证认证
        auth_data = self._authenticate_request()
        if not auth_data:
            self._send_error_response("未授权", 401)
            return

        # 从路径中提取数据源ID
        path_parts = self.path.strip('/').split('/')
        if len(path_parts) < 3:
            self._send_error_response("无效的数据源ID", 400)
            return

        source_id = path_parts[2]

        if source_id not in data_sources:
            self._send_error_response("数据源不存在", 404)
            return

        # 检查权限
        source = data_sources[source_id]
        if source["created_by"] != auth_data["user"]["email"]:
            self._send_error_response("无权限删除此数据源", 403)
            return

        # 删除数据源
        del data_sources[source_id]

        response_data = {"message": "数据源删除成功"}
        print(f"✅ 数据源删除成功: {source_id}")
        sys.stdout.flush()
        self._send_json_response(response_data)

    def _handle_get_data(self):
        """处理其他数据相关请求"""
        print(f"📈 收到数据请求")
        sys.stdout.flush()

        # 验证认证
        auth_data = self._authenticate_request()
        if not auth_data:
            self._send_error_response("未授权", 401)
            return

        # 返回模拟数据
        response_data = {
            "message": "数据接口正常",
            "data": []
        }

        self._send_json_response(response_data)

def run_unified_server():
    """启动统一后端服务器"""
    port = 8000

    print("🚀 SaaS Control Deck 统一后端服务启动于端口", port)
    print("📍 服务地址: http://localhost:8000")
    print("🔍 健康检查: http://localhost:8000/health")
    print("🔐 认证端点: http://localhost:8000/auth/*")
    print("📁 文件上传: http://localhost:8000/upload/*")
    print("📊 数据管理: http://localhost:8000/data/*")
    print("👤 测试账号: test@saascontrol.dev / TestPass123")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    sys.stdout.flush()

    try:
        with socketserver.TCPServer(("", port), UnifiedBackendHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        sys.stdout.flush()
    except Exception as e:
        print(f"❌ 服务器错误: {e}")
        sys.stdout.flush()

if __name__ == "__main__":
    run_unified_server()