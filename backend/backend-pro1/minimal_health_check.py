#!/usr/bin/env python3
"""
极简健康检查 - 仅使用标准库验证FastAPI服务
"""

import socket
import urllib.request
import json
from datetime import datetime

print("🚀 FastAPI服务极简健康检查")
print("=" * 50)

# 1. 检查端口8000是否开放
print("🔍 检查端口8000可达性...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex(('localhost', 8000))
    sock.close()

    if result == 0:
        print("✅ 端口8000已开放，服务可能在运行")
        port_accessible = True
    else:
        print("❌ 端口8000不可达，FastAPI服务可能未启动")
        port_accessible = False
except Exception as e:
    print(f"❌ 端口检查失败: {str(e)}")
    port_accessible = False

print()

if not port_accessible:
    print("💡 建议操作:")
    print("   1. 启动FastAPI服务: uv run uvicorn unified_backend_fastapi:app --reload --port 8000")
    print("   2. 检查服务是否正常启动")
    print("   3. 确认端口8000未被其他进程占用")
    exit(1)

# 2. 尝试访问健康检查端点
print("🔍 测试健康检查端点...")
try:
    url = "http://localhost:8000/health"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Health-Check-Agent/1.0')

    with urllib.request.urlopen(req, timeout=10) as response:
        content = response.read().decode('utf-8')

        print(f"✅ /health 端点响应正常")
        print(f"   状态码: {response.status}")
        print(f"   内容类型: {response.headers.get('content-type', 'unknown')}")

        # 尝试解析健康数据
        try:
            health_data = json.loads(content)
            print(f"   服务状态: {health_data.get('status', 'unknown')}")
            print(f"   服务名称: {health_data.get('service', 'unknown')}")
            print(f"   服务端口: {health_data.get('port', 'unknown')}")

            features = health_data.get('features', [])
            if features:
                print(f"   支持功能: {', '.join(features)}")

            uptime = health_data.get('uptime', 0)
            if uptime:
                print(f"   运行时间: {uptime:.1f}秒")

            print("\n🎉 FastAPI迁移健康检查通过！")
            print("✅ 主要验证项目:")
            print("  - 端口8000服务响应 ✓")
            print("  - 健康检查端点 ✓")
            print("  - JSON响应格式 ✓")
            print("  - 服务基础信息 ✓")

        except json.JSONDecodeError:
            print(f"⚠️  健康端点返回非JSON内容:")
            print(f"   内容预览: {content[:200]}...")

except urllib.error.HTTPError as e:
    print(f"❌ HTTP错误: {e.code} - {e.reason}")
    try:
        error_content = e.read().decode('utf-8')
        print(f"   错误详情: {error_content[:200]}...")
    except:
        pass
except Exception as e:
    print(f"❌ 连接失败: {str(e)}")

print("\n" + "=" * 50)
print(f"📅 检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("🔗 更多验证: 运行 comprehensive_api_validation.py 进行完整测试")