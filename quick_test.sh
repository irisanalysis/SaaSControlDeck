#!/bin/bash
# 使脚本可执行
chmod +x "$0"

# SaaS Control Deck - 快速功能测试脚本
# 验证数据持久化和API端点是否正常工作

echo "🚀 SaaS Control Deck 快速功能测试"
echo "=================================="

# 配置
BASE_URL="http://localhost:8000"
TEST_EMAIL="test@saascontrol.dev"
TEST_PASSWORD="TestPass123"

# 检查后端服务是否运行
echo "1. 检查后端服务状态..."
if curl -f -s "${BASE_URL}/health" > /dev/null; then
    echo "✅ 后端服务正常运行"
    curl -s "${BASE_URL}/health" | python3 -m json.tool
else
    echo "❌ 后端服务无法访问，请先启动后端服务"
    echo "启动命令: cd backend/backend-pro1 && source .venv/bin/activate && uvicorn unified_backend_fastapi:app --reload --port 8000 --host 0.0.0.0"
    exit 1
fi

echo ""
echo "2. 测试用户认证..."

# 获取访问令牌
AUTH_RESPONSE=$(curl -s -X POST "${BASE_URL}/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"${TEST_EMAIL}\",\"password\":\"${TEST_PASSWORD}\"}")

if echo "$AUTH_RESPONSE" | grep -q "access_token"; then
    echo "✅ 用户认证成功"
    ACCESS_TOKEN=$(echo "$AUTH_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data['access_token'])
except:
    print('')
")
    if [ -z "$ACCESS_TOKEN" ]; then
        echo "❌ 无法提取访问令牌"
        exit 1
    fi
else
    echo "❌ 用户认证失败"
    echo "响应: $AUTH_RESPONSE"
    exit 1
fi

echo ""
echo "3. 测试数据源列表..."

# 获取数据源列表
SOURCES_RESPONSE=$(curl -s -X GET "${BASE_URL}/data/sources" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")

if echo "$SOURCES_RESPONSE" | grep -q "data_sources"; then
    echo "✅ 数据源列表获取成功"
    SOURCE_COUNT=$(echo "$SOURCES_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('total', 0))
except:
    print(0)
")
    echo "📊 当前数据源数量: $SOURCE_COUNT"
else
    echo "❌ 数据源列表获取失败"
    echo "响应: $SOURCES_RESPONSE"
fi

echo ""
echo "4. 测试文件上传..."

# 创建测试CSV文件
TEST_FILE="/tmp/test_data.csv"
cat > "$TEST_FILE" << EOF
id,name,age,city,score
1,Alice,25,New York,95.5
2,Bob,30,San Francisco,87.2
3,Charlie,28,Chicago,92.1
EOF

# 上传文件
UPLOAD_RESPONSE=$(curl -s -X POST "${BASE_URL}/upload/file" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -F "file=@${TEST_FILE}")

if echo "$UPLOAD_RESPONSE" | grep -q '"success":true'; then
    echo "✅ 文件上传成功"
    echo "响应: $UPLOAD_RESPONSE" | python3 -m json.tool
else
    echo "❌ 文件上传失败"
    echo "响应: $UPLOAD_RESPONSE"
fi

echo ""
echo "5. 再次检查数据源列表..."

# 再次获取数据源列表以验证上传
SOURCES_RESPONSE_2=$(curl -s -X GET "${BASE_URL}/data/sources" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")

if echo "$SOURCES_RESPONSE_2" | grep -q "data_sources"; then
    NEW_SOURCE_COUNT=$(echo "$SOURCES_RESPONSE_2" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('total', 0))
except:
    print(0)
")
    echo "✅ 更新后的数据源数量: $NEW_SOURCE_COUNT"

    if [ "$NEW_SOURCE_COUNT" -gt "$SOURCE_COUNT" ]; then
        echo "🎉 数据源成功增加，文件上传并保存到数据库"
    else
        echo "⚠️  数据源数量未增加，可能存在问题"
    fi
else
    echo "❌ 无法获取更新后的数据源列表"
fi

echo ""
echo "6. 测试数据统计..."

# 获取数据统计
STATS_RESPONSE=$(curl -s -X GET "${BASE_URL}/data/stats" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}")

if echo "$STATS_RESPONSE" | grep -q "total_datasets"; then
    echo "✅ 数据统计获取成功"
    echo "$STATS_RESPONSE" | python3 -m json.tool
else
    echo "❌ 数据统计获取失败"
    echo "响应: $STATS_RESPONSE"
fi

# 清理测试文件
rm -f "$TEST_FILE"

echo ""
echo "=================================="
echo "🏁 快速测试完成"
echo ""
echo "💡 数据持久化测试说明:"
echo "   1. 现在重启后端服务"
echo "   2. 重新运行此脚本"
echo "   3. 验证数据源是否仍然存在"
echo ""
echo "🔧 重启后端服务命令:"
echo "   cd /home/user/studio/backend/backend-pro1"
echo "   source .venv/bin/activate"
echo "   uvicorn unified_backend_fastapi:app --reload --port 8000 --host 0.0.0.0"