#!/usr/bin/env python3
"""
临时API端点测试脚本 - 快速验证FastAPI服务状态
"""

import urllib.request
import json
import time

def test_endpoint(url):
    try:
        start_time = time.time()
        req = urllib.request.Request(url)

        with urllib.request.urlopen(req, timeout=5) as response:
            response_time = (time.time() - start_time) * 1000
            content = response.read().decode('utf-8')

            print(f"✅ {url}")
            print(f"   状态码: {response.status}")
            print(f"   响应时间: {response_time:.1f}ms")

            # 尝试解析JSON
            try:
                data = json.loads(content)
                if 'service' in data:
                    print(f"   服务: {data.get('service', 'unknown')}")
                if 'status' in data:
                    print(f"   状态: {data.get('status', 'unknown')}")
                if 'features' in data:
                    print(f"   功能: {', '.join(data.get('features', []))}")
            except:
                print(f"   内容长度: {len(content)} 字符")

            print()
            return True

    except urllib.error.HTTPError as e:
        print(f"❌ {url}")
        print(f"   HTTP错误: {e.code} - {e.reason}")
        print()
        return False

    except Exception as e:
        print(f"❌ {url}")
        print(f"   连接错误: {str(e)}")
        print()
        return False

# 测试关键端点
print("🚀 FastAPI服务端点快速测试")
print("=" * 50)

base_url = "http://localhost:8000"
endpoints = [
    f"{base_url}/health",
    f"{base_url}/",
    f"{base_url}/docs",
]

success_count = 0
for endpoint in endpoints:
    if test_endpoint(endpoint):
        success_count += 1

print(f"📊 测试结果: {success_count}/{len(endpoints)} 端点响应正常")

if success_count > 0:
    print("🎉 FastAPI服务基本可用！")
else:
    print("❌ FastAPI服务可能未启动，请检查服务状态")