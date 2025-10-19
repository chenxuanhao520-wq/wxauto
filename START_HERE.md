# 🚀 快速开始 - 从这里开始

**微信客服中台系统 v2.0 - C/S架构版**

---

## 🎯 5分钟快速上手

### 第一步: 了解架构

本系统采用**轻客户端-重服务器**架构：

```
Windows客户端              云服务器
(只做UI自动化)          (处理所有业务)
    ~50MB         ←→        可扩展
```

### 第二步: 选择部署方式

#### 方式A: 本地测试（推荐新手）

```bash
# 1. 启动服务器
./start_server.sh        # Mac/Linux
start_server.bat         # Windows

# 2. 启动客户端
./start_client.sh        # Mac/Linux  
start_client.bat         # Windows
```

#### 方式B: Docker部署（推荐生产）

```bash
# 一键启动服务器
docker-compose up -d

# 客户端仍在Windows运行
python client/main_client.py
```

---

## 📋 详细步骤

### 一、环境准备

#### 服务器端

```bash
# 1. Python 3.9+
python3 --version

# 2. 安装依赖
pip install -r requirements_server.txt

# 主要依赖:
# - fastapi      # Web框架
# - uvicorn      # ASGI服务器
# - pyjwt        # JWT认证
# - sqlalchemy   # ORM
```

#### 客户端

```bash
# 1. Python 3.9+
python3 --version

# 2. 安装依赖
pip install -r requirements_client.txt

# 主要依赖:
# - httpx        # HTTP客户端
# - cryptography # 加密
# - pyyaml       # 配置
# - psutil       # 系统监控
```

---

### 二、配置系统

#### 1. 配置服务器

创建 `.env` 文件（或使用环境变量）：

```bash
# 数据库
DATABASE_URL=postgresql://user:password@localhost:5432/wxauto

# 缓存
REDIS_URL=redis://localhost:6379/0

# 安全
SECRET_KEY=your-secret-key-change-me

# AI配置（可选）
OPENAI_API_KEY=sk-your-key
DEEPSEEK_API_KEY=sk-your-key
```

#### 2. 配置客户端

编辑 `client/config/client_config.yaml`:

```yaml
server:
  url: "http://localhost:8000"    # 服务器地址

client:
  agent_id: "agent_001"            # 客户端唯一ID
  api_key: "your-api-key-here"     # API密钥（服务器端配置）
  name: "客服001号"

wechat:
  auto_start: true
  check_interval: 1                # 每1秒检查新消息

cache:
  enabled: true                    # 启用本地缓存
  encryption: true                 # 启用加密
  cleanup_days: 7                  # 保留7天

heartbeat:
  enabled: true
  interval: 30                     # 每30秒发送心跳
```

---

### 三、启动系统

#### 服务器端

```bash
# 方式1: 直接运行
cd server
python main_server.py

# 方式2: 使用uvicorn（开发模式）
uvicorn server.main_server:app --reload

# 方式3: Docker
docker-compose up -d
```

服务器启动后：
- 服务地址: http://localhost:8000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/v1/health

#### 客户端

```bash
# 启动客户端
python client/main_client.py

# 客户端会:
# 1. 连接服务器
# 2. 认证登录
# 3. 启动心跳
# 4. 开始监听微信消息
```

---

## 🔍 验证运行

### 1. 检查服务器

```bash
# 访问健康检查接口
curl http://localhost:8000/api/v1/health

# 返回:
{
  "status": "healthy",
  "service": "wx-customer-service",
  "version": "2.0.0"
}
```

### 2. 检查客户端日志

```bash
# 查看客户端日志
tail -f logs/client.log

# 应该看到:
# ✅ 微信自动化初始化成功
# ✅ 认证成功
# ✅ 心跳监控已启动
# ✅ 客户端运行中...
```

### 3. 测试消息流程

1. 微信发送测试消息
2. 客户端抓取并上报服务器
3. 服务器AI生成回复
4. 客户端发送回复到微信

---

## 🎓 进阶配置

### 启用AI功能

在服务器配置AI API Key:

```bash
# OpenAI
export OPENAI_API_KEY=sk-your-key

# DeepSeek（推荐，性价比高）
export DEEPSEEK_API_KEY=sk-your-key

# 重启服务器生效
```

### 启用知识库

```bash
# 上传知识库文档
python scripts/upload_documents.py --dir /path/to/docs

# 测试知识库
python scripts/kb_manager.py test "你们的产品有哪些？"
```

### 启用ERP同步

```bash
# 配置ERP
# 编辑 config.yaml 中的 erp_sync 部分

# 启动同步服务
python scripts/start_erp_sync.py
```

---

## 📚 下一步

### 新手

1. ✅ 完成快速开始
2. 📖 阅读 [📘C-S架构部署指南.md](📘C-S架构部署指南.md)
3. 🎮 查看 [docs/guides/快速开始.md](docs/guides/快速开始.md)

### 开发者

1. 📖 阅读 [🏗️架构设计-C-S分离方案.md](🏗️架构设计-C-S分离方案.md)
2. 🔍 查看API文档: http://localhost:8000/docs
3. 💻 参考代码示例: `server/services/` 和 `client/agent/`

### 运维

1. 📊 查看监控: http://localhost:8000/api/v1/stats
2. 🐳 Docker部署: `docker-compose.yml`
3. 📈 性能优化: [docs/features/](docs/features/)

---

## ❓ 常见问题

### Q: 客户端无法连接服务器？

A: 检查：
1. 服务器是否启动: `curl http://localhost:8000/api/v1/health`
2. 配置文件中的服务器地址是否正确
3. 防火墙是否放行8000端口

### Q: AI回复都是错误？

A: 检查：
1. 服务器是否配置了AI API Key
2. 查看服务器日志: `logs/server.log`
3. 测试AI网关: `python -m modules.ai_gateway.gateway`

### Q: 如何添加新客户端？

A: 非常简单：
1. 复制 `client/config/client_config.yaml`
2. 修改 `agent_id` 为新ID（如agent_002）
3. 在新的Windows机器运行 `python client/main_client.py`

### Q: 数据存在哪里？

A:
- 客户端: 本地加密缓存 (`client_cache/`)
- 服务器: PostgreSQL数据库（集中存储）

---

## 🆘 获取帮助

1. 查看完整文档: [docs/README.md](docs/README.md)
2. 查看日志文件: `logs/client.log` 和 `logs/server.log`
3. 提交Issue: GitHub Issues

---

## 🎉 开始使用

```bash
# 启动服务器
./start_server.sh

# 启动客户端
./start_client.sh
```

**就这么简单！祝使用愉快！** 🚀
