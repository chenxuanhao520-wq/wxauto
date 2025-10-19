#!/bin/bash
# ==================== 快速启动脚本 ====================

echo "════════════════════════════════════════════════════════════════"
echo "🚀 微信客服中台 - 快速启动"
echo "════════════════════════════════════════════════════════════════"

# 设置环境变量
export QWEN_API_KEY=sk-1d7d593d85b1469683eb8e7988a0f646
export GLM_API_KEY=2853e43adea74724865746c7ddfcd7ad.qp589y9s3P2KRlI4
export JWT_SECRET_KEY=dev-secret-key-change-in-production-min-32-chars
export VALID_AGENT_CREDENTIALS=agent_001:test-api-key-001

echo "✅ 环境变量已设置"
echo ""

# 选择启动模式
echo "请选择启动模式:"
echo "  1) 运行测试"
echo "  2) 启动服务器"
echo "  3) 启动客户端"
echo "  4) 同时启动服务器和客户端"
echo ""
read -p "请输入选项 (1-4): " choice

case $choice in
  1)
    echo ""
    echo "🧪 运行测试..."
    python3 test_all_fixes.py
    ;;
  2)
    echo ""
    echo "🖥️  启动服务器..."
    python3 server/main_server.py
    ;;
  3)
    echo ""
    echo "💻 启动客户端..."
    python3 client/main_client.py
    ;;
  4)
    echo ""
    echo "🚀 同时启动服务器和客户端..."
    
    # 启动服务器（后台）
    echo "启动服务器..."
    python3 server/main_server.py > logs/server.log 2>&1 &
    SERVER_PID=$!
    echo "✅ 服务器已启动 (PID: $SERVER_PID)"
    
    # 等待服务器启动
    sleep 3
    
    # 启动客户端
    echo "启动客户端..."
    python3 client/main_client.py
    
    # 客户端退出后，停止服务器
    echo ""
    echo "停止服务器..."
    kill $SERVER_PID
    ;;
  *)
    echo "❌ 无效选项"
    exit 1
    ;;
esac

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "完成！"
echo "════════════════════════════════════════════════════════════════"

