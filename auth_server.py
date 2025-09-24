#!/usr/bin/env python3
"""
认证服务器测试文件
专门用于JWT令牌验证和用户管理
"""

import http.server
import socketserver
import json
import uuid
import urllib.parse
import os
import sys
import hashlib
import hmac
import base64
from datetime import datetime, timedelta

# 密钥用于JWT签名（实际应用中应该使用环境变量）
JWT_SECRET = "saas_control_deck_secret_key_2024"

# 测试用户数据库
USER_DATABASE = {
    "test@saascontrol.dev": {
        "id": 1,
        "email": "test@saascontrol.dev",
        "password_hash": "hashed_TestPass123",  # 实际应用中应该是真正的哈希
        "full_name": "测试 用户",
        "first_name": "测试",
        "last_name": "用户",
        "is_active": True,
        "email_verified": True,
        "created_at": "2024-01-01T00:00:00Z",
        "last_login": None,
        "role": "user",
        "avatar_url": None
    },
    "admin@saascontrol.dev": {
        "id": 2,
        "email": "admin@saascontrol.dev",
        "password_hash": "hashed_AdminPass123",
        "full_name": "管理员 用户",
        "first_name": "管理员",
        "last_name": "用户",
        "is_active": True,
        "email_verified": True,
        "created_at": "2024-01-01T00:00:00Z",
        "last_login": None,
        "role": "admin",
        "avatar_url": None
    }
}

# 存储活跃的会话
active_sessions = {}
blacklisted_tokens = set()

class AuthServerHandler(http.server.BaseHTTPRequestHandler):

    def _set_cors_headers(self):
        """设置CORS头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Allow-Credentials', 'true')

    def _send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self._set_cors_headers()
        self.end_headers()

        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))

        # 记录日志
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        print(f'{timestamp} "{self.command} {self.path} HTTP/1.1" {status_code} -')
        sys.stdout.flush()

    def _send_error_response(self, message, status_code=400, error_code=None):
        """发送错误响应"""
        error_data = {
            "error": message,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        }
        if error_code:
            error_data["error_code"] = error_code

        self._send_json_response(error_data, status_code)

    def _generate_token(self, user_data):
        """生成JWT令牌（简化版本）"""
        payload = {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "role": user_data["role"],
            "issued_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }

        # 简化的令牌生成（实际应用中应该使用真正的JWT）
        token_id = uuid.uuid4().hex
        token = f"jwt_{token_id}"

        return token, payload

    def _verify_token(self, token):
        """验证令牌"""
        if token in blacklisted_tokens:
            return None

        session = active_sessions.get(token)
        if not session:
            return None

        # 检查过期
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.now() > expires_at:
            del active_sessions[token]
            return None

        return session

    def _hash_password(self, password):
        """哈希密码（简化版本）"""
        return f"hashed_{password}"

    def _verify_password(self, password, password_hash):
        """验证密码"""
        return self._hash_password(password) == password_hash

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
        elif path == '/auth/register':
            self._handle_register()
        elif path == '/auth/refresh':
            self._handle_refresh_token()
        elif path == '/auth/logout':
            self._handle_logout()
        elif path == '/auth/reset-password':
            self._handle_reset_password()
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
            self._handle_get_current_user()
        elif path == '/auth/verify':
            self._handle_verify_token()
        elif path == '/auth/sessions':
            self._handle_get_sessions()
        else:
            self._send_error_response("接口不存在", 404)

    def do_DELETE(self):
        """处理DELETE请求"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        print(f"🗑️ DELETE {path}")
        sys.stdout.flush()

        if path.startswith('/auth/sessions/'):
            self._handle_delete_session()
        else:
            self._send_error_response("接口不存在", 404)

    def _handle_health(self):
        """健康检查"""
        health_data = {
            "status": "healthy",
            "service": "auth-server",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "active_sessions": len(active_sessions),
            "blacklisted_tokens": len(blacklisted_tokens),
            "registered_users": len(USER_DATABASE)
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

            email = data.get('email', '').strip().lower()
            password = data.get('password', '').strip()
            remember_me = data.get('remember_me', False)

            print(f"📧 登录尝试: {email}")
            print(f"🔒 记住登录: {remember_me}")
            sys.stdout.flush()

            # 验证输入
            if not email or not password:
                self._send_error_response("邮箱和密码不能为空", 400, "MISSING_CREDENTIALS")
                return

            # 查找用户
            user = USER_DATABASE.get(email)
            if not user:
                print(f"❌ 用户不存在: {email}")
                sys.stdout.flush()
                self._send_error_response("邮箱或密码错误", 401, "INVALID_CREDENTIALS")
                return

            # 验证密码
            if not self._verify_password(password, user["password_hash"]):
                print(f"❌ 密码错误: {email}")
                sys.stdout.flush()
                self._send_error_response("邮箱或密码错误", 401, "INVALID_CREDENTIALS")
                return

            # 检查用户状态
            if not user["is_active"]:
                print(f"❌ 用户已被禁用: {email}")
                sys.stdout.flush()
                self._send_error_response("账户已被禁用", 403, "ACCOUNT_DISABLED")
                return

            # 生成令牌
            access_token, token_payload = self._generate_token(user)
            refresh_token = f"refresh_{uuid.uuid4().hex}"

            # 设置过期时间
            expires_hours = 24 * 7 if remember_me else 24  # 记住登录则7天，否则1天
            expires_at = datetime.now() + timedelta(hours=expires_hours)

            # 存储会话
            session_data = {
                **token_payload,
                "expires_at": expires_at.isoformat(),
                "refresh_token": refresh_token,
                "user_agent": self.headers.get('User-Agent', ''),
                "ip_address": self.client_address[0],
                "login_time": datetime.now().isoformat(),
                "remember_me": remember_me
            }

            active_sessions[access_token] = session_data

            # 更新用户最后登录时间
            USER_DATABASE[email]["last_login"] = datetime.now().isoformat()

            # 准备响应数据
            user_info = {k: v for k, v in user.items() if k != 'password_hash'}

            response_data = {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": int(expires_hours * 3600),
                "user": user_info
            }

            print(f"✅ 登录成功: {email}")
            sys.stdout.flush()
            self._send_json_response(response_data)

        except json.JSONDecodeError:
            self._send_error_response("请求数据格式错误", 400, "INVALID_JSON")
        except Exception as e:
            print(f"❌ 登录处理错误: {e}")
            sys.stdout.flush()
            self._send_error_response("服务器内部错误", 500, "INTERNAL_ERROR")

    def _handle_register(self):
        """处理注册请求"""
        print(f"📝 收到注册请求")
        sys.stdout.flush()

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            email = data.get('email', '').strip().lower()
            password = data.get('password', '').strip()
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()

            print(f"📧 注册尝试: {email}")
            sys.stdout.flush()

            # 验证输入
            if not email or not password or not first_name or not last_name:
                self._send_error_response("所有字段都必须填写", 400, "MISSING_FIELDS")
                return

            # 检查邮箱是否已存在
            if email in USER_DATABASE:
                print(f"❌ 邮箱已存在: {email}")
                sys.stdout.flush()
                self._send_error_response("邮箱已被注册", 409, "EMAIL_EXISTS")
                return

            # 创建新用户
            new_user_id = max([user["id"] for user in USER_DATABASE.values()]) + 1
            new_user = {
                "id": new_user_id,
                "email": email,
                "password_hash": self._hash_password(password),
                "full_name": f"{first_name} {last_name}",
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
                "email_verified": False,  # 实际应用中需要邮箱验证
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "role": "user",
                "avatar_url": None
            }

            # 添加到数据库
            USER_DATABASE[email] = new_user

            # 返回用户信息（不包括密码哈希）
            user_info = {k: v for k, v in new_user.items() if k != 'password_hash'}

            response_data = {
                "message": "注册成功",
                "user": user_info
            }

            print(f"✅ 注册成功: {email}")
            sys.stdout.flush()
            self._send_json_response(response_data, 201)

        except json.JSONDecodeError:
            self._send_error_response("请求数据格式错误", 400, "INVALID_JSON")
        except Exception as e:
            print(f"❌ 注册处理错误: {e}")
            sys.stdout.flush()
            self._send_error_response("注册失败", 500, "INTERNAL_ERROR")

    def _handle_refresh_token(self):
        """处理令牌刷新"""
        print(f"🔄 收到令牌刷新请求")
        sys.stdout.flush()

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            refresh_token = data.get('refresh_token', '').strip()

            if not refresh_token:
                self._send_error_response("缺少刷新令牌", 400, "MISSING_REFRESH_TOKEN")
                return

            # 查找对应的会话
            session = None
            access_token = None
            for token, sess in active_sessions.items():
                if sess.get("refresh_token") == refresh_token:
                    session = sess
                    access_token = token
                    break

            if not session:
                self._send_error_response("无效的刷新令牌", 401, "INVALID_REFRESH_TOKEN")
                return

            # 查找用户
            user = None
            for u in USER_DATABASE.values():
                if u["id"] == session["user_id"]:
                    user = u
                    break

            if not user:
                self._send_error_response("用户不存在", 404, "USER_NOT_FOUND")
                return

            # 生成新令牌
            new_access_token, token_payload = self._generate_token(user)
            new_refresh_token = f"refresh_{uuid.uuid4().hex}"

            # 更新会话
            expires_hours = 24 * 7 if session.get("remember_me") else 24
            expires_at = datetime.now() + timedelta(hours=expires_hours)

            session_data = {
                **token_payload,
                "expires_at": expires_at.isoformat(),
                "refresh_token": new_refresh_token,
                "user_agent": session.get("user_agent", ""),
                "ip_address": session.get("ip_address", ""),
                "login_time": session.get("login_time", ""),
                "remember_me": session.get("remember_me", False)
            }

            # 删除旧会话，添加新会话
            if access_token:
                del active_sessions[access_token]
                blacklisted_tokens.add(access_token)

            active_sessions[new_access_token] = session_data

            # 准备响应
            user_info = {k: v for k, v in user.items() if k != 'password_hash'}

            response_data = {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer",
                "expires_in": int(expires_hours * 3600),
                "user": user_info
            }

            print(f"✅ 令牌刷新成功: {user['email']}")
            sys.stdout.flush()
            self._send_json_response(response_data)

        except Exception as e:
            print(f"❌ 令牌刷新错误: {e}")
            sys.stdout.flush()
            self._send_error_response("令牌刷新失败", 500, "INTERNAL_ERROR")

    def _handle_logout(self):
        """处理登出请求"""
        print(f"👋 收到登出请求")
        sys.stdout.flush()

        auth_header = self.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

            # 移除会话并加入黑名单
            if token in active_sessions:
                del active_sessions[token]
                blacklisted_tokens.add(token)
                print(f"✅ 登出成功")
            else:
                print(f"⚠️ 令牌不存在或已失效")

        else:
            print(f"⚠️ 无令牌登出")

        sys.stdout.flush()

        response_data = {"message": "登出成功"}
        self._send_json_response(response_data)

    def _handle_get_current_user(self):
        """获取当前用户信息"""
        print(f"👤 收到获取用户信息请求")
        sys.stdout.flush()

        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            self._send_error_response("未授权", 401, "MISSING_TOKEN")
            return

        token = auth_header.split(' ')[1]
        session = self._verify_token(token)

        if not session:
            self._send_error_response("令牌无效或已过期", 401, "INVALID_TOKEN")
            return

        # 查找用户
        user = None
        for u in USER_DATABASE.values():
            if u["id"] == session["user_id"]:
                user = u
                break

        if not user:
            self._send_error_response("用户不存在", 404, "USER_NOT_FOUND")
            return

        user_info = {k: v for k, v in user.items() if k != 'password_hash'}
        self._send_json_response(user_info)

    def _handle_verify_token(self):
        """验证令牌"""
        print(f"🔍 收到令牌验证请求")
        sys.stdout.flush()

        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            self._send_error_response("未授权", 401, "MISSING_TOKEN")
            return

        token = auth_header.split(' ')[1]
        session = self._verify_token(token)

        if not session:
            self._send_error_response("令牌无效或已过期", 401, "INVALID_TOKEN")
            return

        response_data = {
            "valid": True,
            "user_id": session["user_id"],
            "email": session["email"],
            "role": session["role"],
            "expires_at": session["expires_at"]
        }

        self._send_json_response(response_data)

    def _handle_get_sessions(self):
        """获取用户会话列表"""
        print(f"📋 收到获取会话列表请求")
        sys.stdout.flush()

        auth_header = self.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            self._send_error_response("未授权", 401)
            return

        token = auth_header.split(' ')[1]
        session = self._verify_token(token)

        if not session:
            self._send_error_response("令牌无效", 401)
            return

        # 查找该用户的所有会话
        user_sessions = []
        for sess_token, sess_data in active_sessions.items():
            if sess_data["user_id"] == session["user_id"]:
                session_info = {
                    "token_id": sess_token[:16] + "...",  # 只显示部分令牌
                    "login_time": sess_data.get("login_time"),
                    "expires_at": sess_data.get("expires_at"),
                    "ip_address": sess_data.get("ip_address"),
                    "user_agent": sess_data.get("user_agent", "")[:50] + "...",
                    "is_current": sess_token == token
                }
                user_sessions.append(session_info)

        response_data = {
            "sessions": user_sessions,
            "total": len(user_sessions)
        }

        self._send_json_response(response_data)

def run_auth_server():
    """启动认证服务器"""
    port = 8003

    print(f"🔐 认证服务器启动于端口 {port}")
    print(f"📍 服务地址: http://localhost:{port}")
    print(f"🔍 健康检查: http://localhost:{port}/health")
    print(f"👤 测试账号: test@saascontrol.dev / TestPass123")
    print(f"👤 管理员账号: admin@saascontrol.dev / AdminPass123")
    print("=" * 60)
    print("🔧 可用接口:")
    print("  POST /auth/login - 用户登录")
    print("  POST /auth/register - 用户注册")
    print("  POST /auth/refresh - 刷新令牌")
    print("  POST /auth/logout - 用户登出")
    print("  GET /auth/me - 获取当前用户")
    print("  GET /auth/verify - 验证令牌")
    print("  GET /auth/sessions - 获取用户会话")
    print("=" * 60)
    print("按 Ctrl+C 停止服务器")
    sys.stdout.flush()

    try:
        with socketserver.TCPServer(("", port), AuthServerHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 认证服务器已停止")
        sys.stdout.flush()
    except Exception as e:
        print(f"❌ 服务器错误: {e}")
        sys.stdout.flush()

if __name__ == "__main__":
    run_auth_server()