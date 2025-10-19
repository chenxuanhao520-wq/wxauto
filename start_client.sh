#!/bin/bash
# 启动客户端脚本

echo "=========================================="
echo "  微信客服中台 - 客户端启动脚本"
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
pip install -q -r requirements_client.txt

# 检查配置
echo "[2/3] 检查配置..."
if [ ! -f "client/config/client_config.yaml" ]; then
    echo "❌ 配置文件不存在: client/config/client_config.yaml"
    echo "请先配置客户端"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 启动客户端
echo "[3/3] 启动客户端..."
echo ""
echo "=========================================="
echo "  客户端运行中"
echo "  按 Ctrl+C 停止"
echo "=========================================="
echo ""

python client/main_client.py

