#!/bin/bash
# 启动服务器脚本

echo "=========================================="
echo "  微信客服中台 - 服务器启动脚本"
echo "=========================================="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    exit 1
fi

# 检查依赖
echo "[1/3] 检查依赖..."
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements_server.txt

# 创建日志目录
echo "[2/3] 创建日志目录..."
mkdir -p logs

# 启动服务器
echo "[3/3] 启动服务器..."
echo ""
echo "=========================================="
echo "  服务器运行中"
echo "  地址: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo "  按 Ctrl+C 停止"
echo "=========================================="
echo ""

cd server && python main_server.py

