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

## 🔧 开发环境

### 后端环境
- Python 3.8+
- FastAPI
- Supabase
- Pinecone

### 前端环境
- Node.js 16+
- React 18
- TypeScript
- Vite
- Ant Design

### 客户端环境
- Python 3.8+
- wxauto
- Windows系统

## 📚 文档

- `📋项目使用指南.md` - 完整使用指南
- `🔄前后端分离开发指南.md` - 分离开发指南
- `📁项目结构说明.md` - 项目结构说明
- `backend/README.md` - 后端项目说明
- `frontend/README.md` - 前端项目说明
- `client/README.md` - 客户端说明

## 🐳 部署

### 开发环境
```bash
# 后端
cd backend && python3 main.py

# 前端
cd frontend && npm run dev

# 客户端
cd client && python3 cloud_client.py
```

### 生产环境
```bash
cd docker
./deploy.sh
```

## 🧪 测试

### 后端测试
```bash
cd backend
python3 -m pytest tests/
```

### 前端测试
```bash
cd frontend
npm run test
```

### 集成测试
```bash
python3 scripts/testing/test_system_suite.py
```
