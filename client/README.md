# 🚀 Wxauto Smart Service 客户端

基于分离架构的现代化客户端解决方案：Web前端 + 本地代理

## 🏗️ **架构设计**

### **分离架构优势**
- **Web前端**: 跨平台配置管理、实时监控、统计分析
- **本地代理**: Windows原生微信自动化、高性能消息处理
- **技术栈**: 各取所长，发挥最佳性能

### **技术栈**
- **Web前端**: React + TypeScript + Ant Design
- **本地代理**: Python + wxauto + FastAPI
- **通信**: HTTP/WebSocket + RESTful API

## 📁 **项目结构**

```
client/
├── local_agent.py          # 本地微信代理
├── start_client.py         # 一键启动脚本
├── README.md              # 说明文档
└── config/                # 配置文件
    └── agent_config.json   # 代理配置
```

## 🚀 **快速开始**

### **1. 一键启动**
```bash
# 启动所有服务
python3 start_client.py
```

### **2. 分步启动**

#### **启动后端API**
```bash
cd backend/api
python3 client_management.py
```

#### **启动本地代理**
```bash
cd client
python3 local_agent.py
```

#### **启动Web前端**
```bash
cd frontend
npm install
npm run dev
```

## 🌐 **访问地址**

- **Web前端**: http://localhost:3000
- **本地代理API**: http://localhost:8001
- **后端管理API**: http://localhost:8002

## ⚙️ **配置管理**

### **Web前端配置**
通过Web界面进行配置：
- 微信群聊白名单
- AI模型配置
- 自动回复设置
- 高级选项

### **本地代理配置**
配置文件位置：`~/.wxauto-smart-service/agent_config.json`

```json
{
  "server_url": "http://localhost:8000",
  "api_key": "",
  "whitelist_groups": ["客服群", "技术支持群"],
  "enable_humanize": true,
  "auto_reply": true,
  "ai_model": "qwen",
  "ai_api_key": "",
  "heartbeat_interval": 30,
  "log_level": "INFO"
}
```

## 📊 **功能特性**

### **Web前端功能**
- ✅ **配置管理**: 可视化配置界面
- ✅ **实时监控**: 服务状态、消息流、连接状态
- ✅ **统计分析**: 消息统计、性能分析、群聊排行
- ✅ **日志查看**: 系统日志、错误追踪
- ✅ **远程控制**: 启动/停止代理服务

### **本地代理功能**
- ✅ **微信自动化**: 基于wxauto的消息监听和发送
- ✅ **智能回复**: AI驱动的自动回复
- ✅ **本地缓存**: 离线消息存储
- ✅ **心跳监控**: 与服务器保持连接
- ✅ **错误恢复**: 自动重连和错误处理

## 🔧 **API接口**

### **本地代理API** (端口8001)
- `GET /api/status` - 获取代理状态
- `GET /api/messages/recent` - 获取最近消息
- `GET /api/logs` - 获取日志
- `POST /api/config` - 更新配置
- `POST /api/start` - 启动代理
- `POST /api/stop` - 停止代理

### **后端管理API** (端口8002)
- `GET /api/config` - 获取配置
- `POST /api/config` - 更新配置
- `GET /api/status` - 获取状态
- `POST /api/agent/heartbeat` - 接收心跳
- `GET /api/messages/recent` - 获取消息
- `GET /api/logs` - 获取日志
- `GET /api/statistics` - 获取统计

## 🛠️ **开发指南**

### **添加新功能**

#### **Web前端**
1. 在 `frontend/src/pages/ClientManagement.tsx` 中添加新组件
2. 更新API调用逻辑
3. 添加相应的UI组件

#### **本地代理**
1. 在 `local_agent.py` 中添加新功能
2. 更新API接口
3. 添加配置选项

### **调试模式**
```bash
# 启动调试模式
python3 local_agent.py --log-level DEBUG
```

## 📋 **使用说明**

### **首次使用**
1. 运行 `python3 start_client.py`
2. 访问 http://localhost:3000
3. 配置微信群聊白名单
4. 设置AI模型和API密钥
5. 启动代理服务

### **日常使用**
1. 启动客户端：`python3 start_client.py`
2. 通过Web界面监控和管理
3. 查看实时消息和统计
4. 根据需要调整配置

## 🔍 **故障排除**

### **常见问题**

#### **前端无法访问**
- 检查Node.js是否安装
- 确认端口3000未被占用
- 运行 `npm install` 安装依赖

#### **代理无法启动**
- 检查Python环境
- 确认wxauto库已安装
- 检查微信是否已登录

#### **API连接失败**
- 检查端口8001/8002是否被占用
- 确认防火墙设置
- 查看错误日志

### **日志查看**
```bash
# 查看代理日志
tail -f wxauto_agent.log

# 查看API日志
tail -f client_api.log
```

## 🎯 **最佳实践**

### **性能优化**
- 合理设置心跳间隔
- 控制消息队列大小
- 定期清理日志文件

### **安全建议**
- 使用HTTPS连接
- 设置API密钥认证
- 定期更新依赖

### **维护建议**
- 定期备份配置
- 监控系统资源使用
- 及时处理错误日志

## 📞 **技术支持**

- **文档**: 查看项目文档
- **问题**: 提交GitHub Issue
- **讨论**: 参与社区讨论

---

**🎉 享受现代化的微信客服自动化体验！**