#!/bin/bash

# 前后端分离文件清理脚本

echo "🧹 开始清理和重新组织文件..."

# 1. 删除重复的config目录
if [ -d "config" ]; then
    echo "删除重复的config目录..."
    rm -rf config
fi

# 2. 删除client 2目录
if [ -d "client 2" ]; then
    echo "删除client 2目录..."
    rm -rf "client 2"
fi

# 3. 删除不需要的目录
echo "删除不需要的目录..."
rm -rf data
rm -rf logs

# 4. 重新组织scripts目录
echo "重新组织scripts目录..."
mkdir -p scripts/shared
mkdir -p scripts/backend
mkdir -p scripts/frontend
mkdir -p scripts/client

# 移动脚本到对应目录
if [ -d "scripts/erp_tools" ]; then
    mv scripts/erp_tools scripts/shared/
fi

if [ -d "scripts/utils" ]; then
    mv scripts/utils scripts/shared/
fi

# 5. 创建项目根目录的README
cat > PROJECT_STRUCTURE.md << 'EOF'
# 📁 项目结构说明

## 🏗️ 整体架构

```
wxauto-1/
├── 📁 backend/              # 后端项目
│   ├── main.py              # FastAPI服务入口
│   ├── modules/              # 核心业务模块
│   ├── config/               # 配置文件
│   ├── sql/                  # 数据库脚本
│   ├── tests/                # 单元测试
│   ├── requirements.txt     # Python依赖
│   └── README.md             # 后端说明
│
├── 📁 frontend/             # 前端项目
│   ├── src/                  # 源代码
│   ├── public/               # 静态资源
│   ├── package.json          # Node.js依赖
│   ├── vite.config.ts        # Vite配置
│   ├── tsconfig.json         # TypeScript配置
│   └── README.md             # 前端说明
│
├── 📁 client/               # 微信客户端
│   ├── cloud_client.py       # 云原生客户端
│   ├── agent/                # 自动化代理
│   ├── api/                  # 客户端API
│   ├── cache/                # 本地缓存
│   └── config/                # 客户端配置
│
├── 📁 docker/               # 容器化配置
│   ├── backend.Dockerfile    # 后端镜像
│   ├── frontend.Dockerfile   # 前端镜像
│   ├── docker-compose.yml    # 服务编排
│   ├── nginx.conf            # Nginx配置
│   └── deploy.sh             # 部署脚本
│
├── 📁 docs/                 # 共享文档
├── 📁 scripts/              # 共享脚本
│   ├── shared/              # 共享工具
│   ├── backend/             # 后端脚本
│   ├── frontend/            # 前端脚本
│   └── client/              # 客户端脚本
│
└── 📋 各种指南文档.md
```

## 🚀 快速开始

### 后端开发
```bash
cd backend
pip install -r requirements.txt
python3 main.py
```

### 前端开发
```bash
cd frontend
npm install
npm run dev
```

### 客户端开发
```bash
cd client
python3 cloud_client.py
```

### 一键部署
```bash
cd docker
./deploy.sh
```

## 📋 访问地址

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
EOF

echo "✅ 文件清理和重新组织完成！"
echo "📁 项目结构已优化"
echo "🚀 可以开始独立开发了"
