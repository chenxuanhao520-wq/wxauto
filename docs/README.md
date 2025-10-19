# 📚 文档中心

**微信客服中台系统 v2.0 - C/S架构版本**

---

## 🎯 快速导航

### 🚀 新手入门

| 文档 | 说明 | 推荐度 |
|------|------|--------|
| [../START_HERE.md](../START_HERE.md) | 5分钟快速开始 | ⭐⭐⭐⭐⭐ |
| [📘C-S架构部署指南.md](../📘C-S架构部署指南.md) | 部署操作手册 | ⭐⭐⭐⭐⭐ |
| [guides/快速开始.md](guides/快速开始.md) | 详细入门教程 | ⭐⭐⭐⭐ |
| [guides/INSTALLATION.md](guides/INSTALLATION.md) | 安装指南 | ⭐⭐⭐⭐ |

### 🏗️ 架构设计

| 文档 | 说明 | 推荐度 |
|------|------|--------|
| [🏗️架构设计-C-S分离方案.md](../🏗️架构设计-C-S分离方案.md) | 完整架构设计文档 | ⭐⭐⭐⭐⭐ |
| [../PROJECT_STRUCTURE_V2.md](../PROJECT_STRUCTURE_V2.md) | 项目结构说明 | ⭐⭐⭐⭐ |
| [🎉C-S架构重构完成报告.md](../🎉C-S架构重构完成报告.md) | 重构报告 | ⭐⭐⭐ |

---

## 📖 文档分类

### 1. 使用指南 (guides/)

**系统安装和基础使用**

- [快速开始.md](guides/快速开始.md) - 新手教程
- [INSTALLATION.md](guides/INSTALLATION.md) - 详细安装步骤
- [本地运行指南.md](guides/本地运行指南.md) - 本地开发指南
- [WINDOWS_DEPLOYMENT.md](guides/WINDOWS_DEPLOYMENT.md) - Windows部署
- [LLM_PROVIDERS.md](guides/LLM_PROVIDERS.md) - AI模型配置
- [MULTIMODAL_SUPPORT.md](guides/MULTIMODAL_SUPPORT.md) - 语音图片支持
- [ADAPTIVE_LEARNING_GUIDE.md](guides/ADAPTIVE_LEARNING_GUIDE.md) - 自适应学习
- [UPGRADE_GUIDE.md](guides/UPGRADE_GUIDE.md) - 升级指南

### 2. 功能文档 (features/)

**核心功能详解**

- [智能对话上下文管理方案.md](features/智能对话上下文管理方案.md) - Token优化 ⭐
- [会话超时管理方案对比.md](features/会话超时管理方案对比.md) - 会话管理 ⭐
- [智能对话闭环学习系统-增强方案.md](features/智能对话闭环学习系统-增强方案.md) - 自动学习 ⭐
- [KNOWLEDGE_BASE_SOLUTION.md](features/KNOWLEDGE_BASE_SOLUTION.md) - 知识库方案
- [CONVERSATION_TRACKING.md](features/CONVERSATION_TRACKING.md) - 对话追踪
- [ADAPTIVE_LEARNING.md](features/ADAPTIVE_LEARNING.md) - 自适应学习
- [CUSTOMER_HUB_GUIDE.md](features/CUSTOMER_HUB_GUIDE.md) - 客户中台

### 3. 集成文档 (integrations/)

**外部系统集成**

- [ERP同步系统README.md](integrations/ERP同步系统README.md) - ERP集成总览 ⭐
- [ERP_API文档清单.md](integrations/ERP_API文档清单.md) - API清单
- [表格同步使用说明.md](integrations/表格同步使用说明.md) - 飞书/钉钉集成
- [表格配置指南.md](integrations/表格配置指南.md) - 多维表格配置
- [MULTITABLE_INTEGRATION.md](integrations/MULTITABLE_INTEGRATION.md) - 多维表格详解
- [MIGRATION_TO_WEWORK.md](integrations/MIGRATION_TO_WEWORK.md) - 企业微信迁移

### 4. ERP API文档 (erp_api/)

**智邦国际ERP API完整文档**

- [智邦ERP_API完整索引.md](erp_api/智邦ERP_API完整索引.md) - API总索引 ⭐
- [智邦ERP_API完整分析报告.md](erp_api/智邦ERP_API完整分析报告.md) - 分析报告
- [微信中台ERP对接指南.md](erp_api/微信中台ERP对接指南.md) - 对接指南 ⭐
- [API快速参考表.md](erp_api/API快速参考表.md) - 快速参考
- [ERP同步安装使用指南.md](erp_api/ERP同步安装使用指南.md) - 安装配置
- [ERP智能自动同步方案.md](erp_api/ERP智能自动同步方案.md) - 同步方案
- [ERP数据质量控制方案.md](erp_api/ERP数据质量控制方案.md) - 质量控制
- [api_by_category/](erp_api/api_by_category/) - 分类API文档（41个）

---

## 🆕 v2.0 新增文档

### C/S架构相关

| 文档 | 说明 |
|------|------|
| [🏗️架构设计-C-S分离方案.md](../🏗️架构设计-C-S分离方案.md) | 完整架构设计（917行） |
| [📘C-S架构部署指南.md](../📘C-S架构部署指南.md) | 部署操作指南（280行） |
| [🎉C-S架构重构完成报告.md](../🎉C-S架构重构完成报告.md) | 重构完成报告 |

### 客户端文档

- `client/config/client_config.yaml` - 客户端配置说明
- `requirements_client.txt` - 客户端依赖清单

### 服务器文档

- `server/main_server.py` - FastAPI应用（含注释）
- `requirements_server.txt` - 服务器依赖清单
- `docker-compose.yml` - Docker部署配置

---

## 📊 文档地图

```
docs/
├── README.md                       # 本文档 ⭐
│
├── guides/                         # 使用指南（8个）
│   ├── 快速开始.md                 # 新手教程
│   ├── INSTALLATION.md             # 安装指南
│   ├── LLM_PROVIDERS.md            # AI配置
│   └── ...
│
├── features/                       # 功能文档（7个）
│   ├── 智能对话上下文管理方案.md   # 上下文优化
│   ├── 会话超时管理方案对比.md     # 会话管理
│   └── ...
│
├── integrations/                   # 集成文档（6个）
│   ├── ERP同步系统README.md        # ERP集成
│   ├── 表格同步使用说明.md         # 多维表格
│   └── ...
│
└── erp_api/                        # ERP API（49个）
    ├── 智邦ERP_API完整索引.md      # API索引
    └── api_by_category/            # 分类文档
```

---

## 🎓 学习路径

### 路径1: 快速上手（1小时）

```
1. START_HERE.md (10分钟)
   ↓
2. 📘C-S架构部署指南.md (20分钟)
   ↓
3. 启动服务器 + 客户端 (20分钟)
   ↓
4. 测试消息处理 (10分钟)
```

### 路径2: 深入理解（1天）

```
1. 🏗️架构设计-C-S分离方案.md (1小时)
   ↓
2. PROJECT_STRUCTURE_V2.md (30分钟)
   ↓
3. features/ 功能文档 (2小时)
   ↓
4. 阅读核心代码 (4小时)
```

### 路径3: 生产部署（3天）

```
Day 1: 环境搭建
  • Docker部署
  • PostgreSQL配置
  • Redis配置

Day 2: 功能配置
  • AI模型配置
  • 知识库上传
  • ERP对接

Day 3: 测试上线
  • 压力测试
  • 监控配置
  • 正式上线
```

---

## 🔧 开发文档

### API参考

- **服务器API**: http://localhost:8000/docs (Swagger UI)
- **客户端API**: 见 `client/api/server_client.py` 注释

### 代码示例

```python
# 客户端示例
from client.api.server_client import ServerClient

client = ServerClient(
    base_url="http://localhost:8000",
    agent_id="agent_001",
    api_key="your-key"
)

# 上报消息
result = await client.report_message(message)

# 发送心跳
await client.send_heartbeat(status)
```

```python
# 服务器示例
from server.services.message_service import MessageService

service = MessageService()

# 处理消息
result = await service.process_message(agent_id, message)
# 自动完成: 去重→识别→检索→AI生成→保存
```

---

## 📝 技术文档

### 架构文档

- [🏗️架构设计-C-S分离方案.md](../🏗️架构设计-C-S分离方案.md)
  - 架构总览
  - 通信协议
  - 数据流设计
  - 安全设计
  - 部署架构
  - 性能优化

### 数据库文档

- `sql/init.sql` - 数据库初始化脚本
- `sql/upgrade_*.sql` - 升级脚本
- `scripts/check_db.py` - 数据库检查工具

### 测试文档

- `tests/` - 52个测试用例
- `🧪测试报告.md` - 测试结果报告

---

## 🔍 故障排查

### 问题分类

| 问题类型 | 查看文档 |
|---------|---------|
| 安装失败 | guides/INSTALLATION.md |
| 连接失败 | 📘C-S架构部署指南.md |
| AI不工作 | guides/LLM_PROVIDERS.md |
| 知识库问题 | features/KNOWLEDGE_BASE_SOLUTION.md |
| ERP同步问题 | integrations/ERP同步系统README.md |

### 日志位置

- 客户端日志: `logs/client.log`
- 服务器日志: `logs/server.log`
- 应用日志: `logs/app.log`

---

## 📊 文档统计

- **总文档数**: 71个
- **核心文档**: 15个
- **API文档**: 49个
- **代码注释覆盖率**: ~90%

---

## 🆕 版本更新

### v2.0.0 (2025-01-19)

- ✅ C/S架构重构
- ✅ 轻量级客户端
- ✅ FastAPI服务器
- ✅ Docker部署支持
- ✅ 完整文档更新

### v1.x

- 单体架构版本（已归档）

---

## 📮 文档反馈

如果文档有不清楚的地方，欢迎：

1. 提交Issue
2. 提交PR改进文档
3. 联系开发团队

---

**文档最后更新**: 2025-01-19  
**文档版本**: v2.0  
**架构版本**: Client-Server
