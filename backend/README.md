# 🚀 Wxauto 后端服务

基于FastAPI的云原生微信客服中台后端服务。

## ✨ 核心特性

- 🤖 **AI智能路由** - 多模型智能路由 (Qwen, GLM, OpenAI等)
- 🔍 **向量搜索** - Pinecone向量数据库 + RAG
- ☁️ **云原生架构** - Supabase + 实时同步
- ⚙️ **配置管理** - 动态配置 + 实时同步
- 🔐 **多租户支持** - 租户隔离 + 权限管理
- 📊 **API文档** - 自动生成的Swagger文档

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
# Supabase配置
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your_supabase_anon_key"
export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"

# Pinecone配置
export PINECONE_API_KEY="your_pinecone_api_key"
export PINECONE_ENVIRONMENT="us-west1-gcp-free"
export PINECONE_INDEX_NAME="wxauto-knowledge"

# AI服务配置
export QWEN_API_KEY="your_qwen_api_key"
export GLM_API_KEY="your_glm_api_key"
export OPENAI_API_KEY="your_openai_api_key"
```

### 3. 启动服务
```bash
# 开发模式
python3 main.py

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 4. 访问服务
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **配置管理**: http://localhost:8000/api/v1/config/

## 📁 项目结构

```
backend/
├── main.py                    # 主服务入口
├── modules/                   # 核心模块
│   ├── api/                   # API路由层
│   ├── storage/               # 数据存储层
│   ├── vector/                 # 向量搜索
│   ├── embeddings/             # 嵌入服务
│   ├── auth/                   # 认证授权
│   ├── config/                 # 配置管理
│   ├── realtime/               # 实时服务
│   ├── ai_gateway/             # AI网关
│   └── rag/                    # 检索增强生成
├── config/                     # 配置文件
├── sql/                        # 数据库脚本
├── tests/                      # 单元测试
└── requirements.txt            # 依赖列表
```

## 🔧 API接口

### 配置管理
- `GET /api/v1/config/categories` - 获取配置分类
- `GET /api/v1/config/status` - 获取服务状态
- `POST /api/v1/config/update` - 更新配置
- `POST /api/v1/config/test` - 测试连接
- `POST /api/v1/config/sync` - 同步配置

### 消息处理
- `POST /api/v1/messages/process` - 处理消息
- `GET /api/v1/messages/history` - 获取消息历史

### 租户管理
- `GET /api/v1/tenants` - 获取租户列表
- `POST /api/v1/tenants` - 创建租户
- `PUT /api/v1/tenants/{id}` - 更新租户
- `DELETE /api/v1/tenants/{id}` - 删除租户

### 健康检查
- `GET /api/v1/health` - 健康检查

## 🧪 测试

```bash
# 运行单元测试
python3 -m pytest tests/

# 运行特定测试
python3 -m pytest tests/test_api.py

# 运行测试并生成覆盖率报告
python3 -m pytest --cov=modules tests/
```

## 🐳 Docker部署

```bash
# 构建镜像
docker build -t wxauto-backend .

# 运行容器
docker run -p 8000:8000 wxauto-backend
```

## 📊 监控

- **日志**: 查看 `logs/server.log`
- **健康检查**: 访问 `/api/v1/health`
- **性能监控**: 内置性能指标

## 🔧 开发

### 添加新的API端点
1. 在 `modules/api/` 中创建新的路由文件
2. 在 `main.py` 中注册路由
3. 添加相应的测试用例

### 添加新的服务
1. 在 `modules/` 中创建新的服务模块
2. 实现相应的接口和逻辑
3. 添加单元测试

## 📄 许可证

MIT License
