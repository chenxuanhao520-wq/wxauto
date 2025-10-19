#!/bin/bash
# ==================== 生产环境启动脚本 ====================

echo "════════════════════════════════════════════════════════════════"
echo "🚀 微信客服中台 - 生产环境启动"
echo "════════════════════════════════════════════════════════════════"

# ✅ 检查必需的环境变量
check_env_var() {
    if [ -z "${!1}" ]; then
        echo "❌ 错误: 环境变量 $1 未设置"
        echo "   请设置: export $1=your-value"
        exit 1
    fi
}

echo "[1/5] 检查环境变量..."
check_env_var "QWEN_API_KEY"
check_env_var "GLM_API_KEY"
check_env_var "JWT_SECRET_KEY"
check_env_var "VALID_AGENT_CREDENTIALS"
echo "✅ 环境变量检查通过"

# ✅ 检查必需的目录
echo "[2/5] 检查目录结构..."
mkdir -p logs data client_cache
echo "✅ 目录结构就绪"

# ✅ 初始化数据库
echo "[3/5] 初始化数据库..."
if [ ! -f "data/data.db" ]; then
    python3 -c "
from modules.storage.db import Database
db = Database('data/data.db')
db.init_database('sql/init.sql')
print('✅ 数据库初始化完成')
"
else
    echo "✅ 数据库已存在"
fi

# ✅ 运行测试
echo "[4/5] 运行快速测试..."
python3 -c "
import os
import asyncio
from modules.ai_gateway.gateway import AIGateway

async def quick_test():
    gateway = AIGateway(
        primary_provider='qwen',
        primary_model='qwen-turbo',
        fallback_provider='glm',
        fallback_model='glm-4-flash',
        enable_smart_routing=True
    )
    
    response = await gateway.generate(
        user_message='你好，测试一下',
        max_tokens=50
    )
    
    if response.content:
        print(f'✅ AI Gateway 测试通过: {response.provider}/{response.model}')
        return True
    else:
        print(f'❌ AI Gateway 测试失败: {response.error}')
        return False

if not asyncio.run(quick_test()):
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 测试失败，请检查配置"
    exit 1
fi

# ✅ 选择启动模式
echo "[5/5] 选择启动模式..."
echo ""
echo "请选择："
echo "  1) 仅启动服务器"
echo "  2) 仅启动客户端"
echo "  3) 同时启动服务器和客户端"
echo "  4) 后台启动（使用 systemd/supervisor）"
echo ""
read -p "请输入选项 (1-4): " choice

case $choice in
  1)
    echo ""
    echo "🖥️  启动服务器 (生产模式)..."
    python3 server/main_server.py
    ;;
  2)
    echo ""
    echo "💻 启动客户端..."
    python3 client/main_client.py
    ;;
  3)
    echo ""
    echo "🚀 同时启动服务器和客户端..."
    
    # 启动服务器（后台）
    python3 server/main_server.py > logs/server.log 2>&1 &
    SERVER_PID=$!
    echo "✅ 服务器已启动 (PID: $SERVER_PID)"
    
    # 等待服务器就绪
    sleep 3
    
    # 检查服务器健康
    if curl -s http://localhost:8000/api/v1/health > /dev/null; then
        echo "✅ 服务器健康检查通过"
    else
        echo "❌ 服务器启动失败"
        kill $SERVER_PID
        exit 1
    fi
    
    # 启动客户端
    echo "启动客户端..."
    python3 client/main_client.py
    
    # 客户端退出后，停止服务器
    kill $SERVER_PID
    echo "✅ 服务器已停止"
    ;;
  4)
    echo ""
    echo "📝 后台启动说明："
    echo ""
    echo "使用 systemd (推荐):"
    echo "  sudo cp deploy/wxauto-server.service /etc/systemd/system/"
    echo "  sudo systemctl enable wxauto-server"
    echo "  sudo systemctl start wxauto-server"
    echo ""
    echo "使用 supervisor:"
    echo "  sudo cp deploy/supervisor.conf /etc/supervisor/conf.d/wxauto.conf"
    echo "  sudo supervisorctl reread"
    echo "  sudo supervisorctl update"
    echo ""
    echo "使用 nohup (简单方式):"
    echo "  nohup python3 server/main_server.py > logs/server.log 2>&1 &"
    echo "  nohup python3 client/main_client.py > logs/client.log 2>&1 &"
    ;;
  *)
    echo "❌ 无效选项"
    exit 1
    ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ 启动完成"
echo "════════════════════════════════════════════════════════════════"

