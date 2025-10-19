# 📦 安装指南

**微信客服中台 v2.0 - C/S架构版本**

---

## 🎯 架构说明

v2.0采用C/S分离架构，需要分别安装：

1. **服务器端** - 云服务器（处理所有业务逻辑）
2. **客户端** - Windows机器（只做UI自动化）

---

## 🖥️ 服务器端安装

### 环境要求

- **操作系统**: Linux (推荐Ubuntu 20.04+) / Mac / Windows Server
- **Python**: 3.9+
- **内存**: 4GB+ (8GB推荐)
- **存储**: 20GB+

### 方式A: Docker安装（推荐）

```bash
# 1. 安装Docker和Docker Compose
curl -fsSL https://get.docker.com | sh
sudo apt-get install docker-compose

# 2. 克隆项目
git clone https://github.com/chenxuanhao520-wq/wxauto.git
cd wxauto

# 3. 一键启动
docker-compose up -d

# 4. 查看状态
docker-compose ps
docker-compose logs -f server
```

服务将在以下端口启动：
- FastAPI: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### 方式B: 手动安装

```bash
# 1. 安装Python 3.9+
sudo apt-get update
sudo apt-get install python3.9 python3.9-venv python3-pip

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. 安装服务器依赖
pip install -r requirements_server.txt

# 4. 安装PostgreSQL（可选，也可用SQLite）
sudo apt-get install postgresql postgresql-contrib

# 5. 安装Redis（可选）
sudo apt-get install redis-server

# 6. 配置数据库
# 创建数据库
sudo -u postgres createdb wxauto

# 配置连接（.env文件）
echo "DATABASE_URL=postgresql://user:password@localhost:5432/wxauto" > .env
echo "REDIS_URL=redis://localhost:6379/0" >> .env

# 7. 启动服务器
python server/main_server.py

# 或使用uvicorn
uvicorn server.main_server:app --host 0.0.0.0 --port 8000
```

### 配置AI模型（必需）

```bash
# 设置环境变量
export DEEPSEEK_API_KEY=sk-your-deepseek-key
export OPENAI_API_KEY=sk-your-openai-key  # 可选

# 或在.env文件中
echo "DEEPSEEK_API_KEY=sk-your-key" >> .env
```

### 验证安装

```bash
# 1. 健康检查
curl http://localhost:8000/api/v1/health

# 应返回
{
  "status": "healthy",
  "service": "wx-customer-service",
  "version": "2.0.0"
}

# 2. 查看API文档
# 浏览器访问: http://localhost:8000/docs
```

---

## 💻 客户端安装

### 环境要求

- **操作系统**: Windows 10/11
- **Python**: 3.9+
- **微信**: PC版最新版（保持登录状态）
- **内存**: 2GB+ (实际占用~50MB)

### 安装步骤

```bash
# 1. 克隆项目（如果还没有）
git clone https://github.com/chenxuanhao520-wq/wxauto.git
cd wxauto

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 3. 安装客户端依赖
pip install -r requirements_client.txt

# 4. 配置客户端
# 编辑 client/config/client_config.yaml
notepad client\config\client_config.yaml

# 必须配置:
# - server.url: 服务器地址
# - client.agent_id: 客户端ID
# - client.api_key: API密钥

# 5. 启动客户端
python client\main_client.py

# 或使用启动脚本
start_client.bat
```

### 配置说明

编辑 `client/config/client_config.yaml`:

```yaml
server:
  url: "http://your-server-ip:8000"  # 改为实际服务器地址

client:
  agent_id: "agent_001"               # 唯一ID
  api_key: "your-api-key-here"        # 与服务器端配置一致
  name: "客服001号"

wechat:
  check_interval: 1                   # 消息检查间隔

cache:
  enabled: true
  encryption: true

heartbeat:
  enabled: true
  interval: 30
```

---

## 🔐 安全配置

### 1. JWT密钥配置

在服务器端配置JWT密钥（生产环境必须修改！）：

```python
# server/api/auth.py
SECRET_KEY = "your-very-secret-key-change-in-production"
```

或通过环境变量：

```bash
export JWT_SECRET_KEY=your-very-secret-key
```

### 2. 客户端API Key管理

在服务器端配置允许的客户端：

```python
# server/api/auth.py
valid_agents = {
    "agent_001": "api-key-001",
    "agent_002": "api-key-002"
}
```

生产环境应从数据库或配置文件读取！

### 3. HTTPS配置

生产环境建议使用HTTPS：

```bash
# 使用Nginx反向代理
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
    }
}
```

---

## 🧪 安装验证

### 服务器端验证

```bash
# 1. API健康检查
curl http://localhost:8000/api/v1/health

# 2. 测试认证
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"agent_001","api_key":"your-api-key"}'

# 3. 查看统计
curl http://localhost:8000/api/v1/stats
```

### 客户端验证

启动客户端后，检查日志：

```
✅ 服务器健康
✅ 认证成功
✅ 心跳监控已启动
✅ 微信在线
✅ 客户端运行中...
```

---

## 🛠️ 故障排查

### 服务器问题

#### 1. 端口被占用

```bash
# 查找占用8000端口的进程
lsof -i :8000
# 或
netstat -ano | findstr :8000

# 杀死进程或更换端口
```

#### 2. 数据库连接失败

```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 检查连接
psql -h localhost -U user -d wxauto

# 查看日志
tail -f /var/log/postgresql/postgresql-*.log
```

#### 3. Redis连接失败

```bash
# 检查Redis状态
redis-cli ping
# 应返回: PONG

# 启动Redis
sudo systemctl start redis
```

### 客户端问题

#### 1. 无法连接服务器

```bash
# 测试网络连通性
ping your-server-ip
telnet your-server-ip 8000

# 检查防火墙
# Windows: 控制面板 → 防火墙 → 高级设置
# Linux: sudo ufw status
```

#### 2. 认证失败

- 检查 `client_config.yaml` 中的 `api_key` 是否正确
- 检查服务器端 `auth.py` 中是否配置了该客户端
- 查看服务器日志确认错误原因

#### 3. 微信不响应

- 确认PC微信已登录且在前台
- 检查wxauto是否正确安装
- 查看客户端日志错误信息

---

## 📊 性能优化建议

### 服务器端

```bash
# 1. 启用数据库连接池
# 在SQLAlchemy配置中:
pool_size=20
max_overflow=40

# 2. 启用Redis缓存
REDIS_URL=redis://localhost:6379/0

# 3. 启用Nginx缓存
# nginx.conf中添加缓存配置

# 4. 使用SSD存储
# 数据库和Redis数据放在SSD上
```

### 客户端

```bash
# 1. 调整消息检查间隔
# client_config.yaml:
wechat:
  check_interval: 2  # 从1秒改为2秒

# 2. 定期清理缓存
# 客户端会自动清理7天前的缓存

# 3. 关闭不必要的功能
cache:
  enabled: false  # 如果服务器稳定，可关闭本地缓存
```

---

## 🔄 升级指南

### 从v1.x升级到v2.0

v2.0是架构大升级，建议重新安装：

```bash
# 1. 备份数据
cp -r data/ data_backup/
cp config.yaml config.yaml.bak

# 2. 拉取最新代码
git pull origin main

# 3. 安装新依赖
pip install -r requirements_server.txt
pip install -r requirements_client.txt

# 4. 迁移数据（如需要）
# 运行迁移脚本
python scripts/migrate_to_v2.py

# 5. 启动新架构
# 服务器
python server/main_server.py

# 客户端
python client/main_client.py
```

---

## 📚 下一步

安装完成后，请阅读：

1. [快速开始.md](快速开始.md) - 详细使用教程
2. [LLM_PROVIDERS.md](LLM_PROVIDERS.md) - AI模型配置
3. [../features/](../features/) - 功能文档

---

## 🆘 获取帮助

- 📖 查看[常见问题](../../START_HERE.md#常见问题)
- 🐛 提交[GitHub Issue](https://github.com/chenxuanhao520-wq/wxauto/issues)
- 📧 联系技术支持

---

**安装文档版本**: v2.0  
**最后更新**: 2025-01-19
