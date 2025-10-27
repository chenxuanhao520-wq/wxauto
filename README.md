# 🚀 Wxauto Smart Service 智能客服中台

基于云原生架构的智能微信客服系统，集成Supabase、pgvector和AI Gateway。

## ✨ 核心特性

- 🤖 **AI智能回复** - 多模型智能路由 (Qwen, GLM, OpenAI等)
- 🔍 **知识库检索** - Supabase pgvector向量搜索 + RAG
- ☁️ **云原生架构** - Supabase + 实时同步
- ⚙️ **配置管理** - 动态配置 + 实时同步
- 📱 **微信自动化** - Windows微信PC版自动化
- 🔐 **多租户支持** - 租户隔离 + 权限管理

## 🚀 快速开始

### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动服务
```bash
# 后端服务
cd backend
python3 main.py

# 前端界面
cd frontend
npm install
npm run dev

# 微信客户端
cd client
python3 cloud_client.py
```

### 3. 访问服务
- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 📁 项目结构

```
wxauto-smart-service/
├── backend/          # 后端项目 (FastAPI + Python)
├── frontend/         # 前端项目 (React + TypeScript)
├── client/           # 微信客户端 (Python)
├── docker/           # 容器化配置
├── docs/             # 文档
├── scripts/          # 脚本工具
└── README.md         # 项目说明
```

## 📚 文档

- [项目使用指南](docs/guides/📋项目使用指南.md)
- [前后端分离开发指南](docs/guides/🔄前后端分离开发指南.md)
- [项目结构说明](docs/guides/📁项目结构说明.md)
- [项目结构文档](docs/PROJECT_STRUCTURE.md)

## 🐳 部署

```bash
cd docker
./deploy.sh
```

## 💰 成本优势

| 服务 | 之前 | 现在 | 节省 |
|------|------|------|------|
| **数据库** | Supabase | Supabase | 0 |
| **向量搜索** | Pinecone $70/月 | Supabase 免费 | **$70/月** |
| **AI模型** | 多个API | 多个API | 0 |
| **总计** | ~$100/月 | ~$30/月 | **$70/月** |

## 🔧 配置说明

### 必需配置

```bash
# Supabase配置（数据库 + 向量数据库）
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# AI模型配置
QWEN_API_KEY=sk-your-qwen-api-key
GLM_API_KEY=your-glm-api-key
OPENAI_API_KEY=sk-your-openai-api-key
```

### 向量数据库配置

```bash
# 向量数据库配置（使用Supabase pgvector）
VECTOR_TABLE_NAME=knowledge_vectors
VECTOR_DIMENSION=1536
VECTOR_SIMILARITY_THRESHOLD=0.7
```

## 🎯 技术优势

- **成本更低** - 每月节省$70
- **集成更好** - 与数据库一体化
- **维护更简单** - 减少一个外部服务
- **性能足够** - pgvector性能完全够用
- **功能完整** - 支持所有向量搜索功能

## 📄 许可证

MIT License