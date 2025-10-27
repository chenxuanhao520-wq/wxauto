#!/bin/bash

# 前后端分离部署脚本

set -e

echo "🚀 开始部署微信客服中台..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

# 检查环境变量文件
if [ ! -f "docker/.env" ]; then
    echo "⚠️ 环境变量文件不存在，从模板创建..."
    cp docker/env.example docker/.env
    echo "📝 请编辑 docker/.env 文件，填入真实的配置值"
    echo "然后重新运行此脚本"
    exit 1
fi

# 构建和启动服务
echo "🔨 构建Docker镜像..."
docker-compose -f docker/docker-compose.yml build

echo "🚀 启动服务..."
docker-compose -f docker/docker-compose.yml up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
docker-compose -f docker/docker-compose.yml ps

# 健康检查
echo "🏥 执行健康检查..."
if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "✅ 后端服务健康"
else
    echo "❌ 后端服务不健康"
fi

if curl -f http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ 前端服务健康"
else
    echo "❌ 前端服务不健康"
fi

echo ""
echo "🎉 部署完成！"
echo "📱 前端地址: http://localhost:3000"
echo "🔧 后端API: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo ""
echo "📋 管理命令:"
echo "  查看日志: docker-compose -f docker/docker-compose.yml logs -f"
echo "  停止服务: docker-compose -f docker/docker-compose.yml down"
echo "  重启服务: docker-compose -f docker/docker-compose.yml restart"
