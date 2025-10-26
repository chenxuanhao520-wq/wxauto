# 📁 项目结构说明 v2.0

**C/S分离架构版本**

---

## 🏗️ 总体架构

```
wxauto-1/
├── 📱 client/              # Windows轻客户端
├── 🖥️  server/              # 云服务器端
├── 📦 modules/             # 共享模块（服务器使用）
├── 🧠 core/                # 核心功能
├── 🌐 web/                 # Web管理界面
├── 📚 docs/                # 文档
├── 🧪 tests/               # 测试
└── 🛠️  scripts/             # 工具脚本
```

---

## 📱 客户端 (client/)

**职责**: Windows端UI自动化，资源占用~50MB

```
client/
├── agent/                          # 微信自动化
│   ├── __init__.py
│   └── wx_automation.py           # 微信UI操作封装
│       • get_new_messages()       # 抓取消息
│       • send_message()           # 发送消息
│       • get_screenshot()         # 截图（预留）
│       • get_status()             # 状态检查
│
├── api/                            # 服务器通信
│   └── server_client.py           # HTTP客户端
│       • authenticate()           # JWT认证
│       • report_message()         # 上报消息
│       • get_reply()              # 获取回复
│       • send_heartbeat()         # 发送心跳
│
├── cache/                          # 本地缓存
│   └── local_cache.py             # AES-256加密缓存
│       • save_message()           # 加密保存
│       • load_message()           # 解密读取
│       • offline_queue管理        # 离线队列
│
├── monitor/                        # 监控
│   └── heartbeat.py               # 心跳服务
│       • 30秒间隔心跳
│       • 状态自动上报
│
├── config/                         # 配置
│   └── client_config.yaml         # 客户端配置文件
│
├── __init__.py
└── main_client.py                 # 客户端主程序 ⭐
    • 296行
    • 完整的消息循环
    • 离线队列处理
    • 错误处理
```

---

## 🖥️ 服务器 (server/)

**职责**: 所有复杂业务逻辑，可弹性扩展

```
server/
├── api/                            # REST API层
│   ├── __init__.py
│   ├── auth.py                    # 认证API
│   │   • POST /auth/login        # 客户端登录
│   │   • POST /auth/refresh      # Token刷新
│   │
│   ├── messages.py                # 消息API
│   │   • POST /messages          # 接收消息
│   │   • GET  /messages/:id/reply # 获取回复
│   │   • POST /send              # 主动发送
│   │
│   ├── heartbeat.py               # 心跳API
│   │   • POST /heartbeat         # 接收心跳
│   │   • GET  /agents/status     # 客户端状态
│   │
│   └── stats.py                   # 统计API
│       • GET  /stats             # 系统统计
│       • GET  /stats/messages    # 消息统计
│
├── services/                       # 业务服务层
│   └── message_service.py         # 消息处理服务 ⭐
│       • process_message()        # 核心处理逻辑
│       • _is_duplicate()          # 去重
│       • _identify_customer()     # 客户识别
│       • _check_rules()           # 规则引擎
│       • _retrieve_knowledge()    # 知识库检索
│       • _generate_reply()        # AI生成
│
├── models/                         # 数据模型（预留）
├── utils/                          # 工具函数（预留）
├── __init__.py
└── main_server.py                 # FastAPI主程序 ⭐
    • 107行
    • 生命周期管理
    • 路由注册
    • CORS配置
```

---

## 📦 共享模块 (modules/)

**服务器端使用的业务模块**

```
modules/
├── ai_gateway/                     # AI网关
│   ├── gateway.py                 # 统一网关
│   └── providers/                 # 7个提供商
│       ├── openai_provider.py
│       ├── claude_provider.py
│       ├── deepseek_provider.py
│       ├── qwen_provider.py
│       ├── moonshot_provider.py
│       ├── gemini_provider.py
│       └── ernie_provider.py
│
├── rag/                            # 知识库检索
│   └── retriever.py               # 向量检索
│
├── storage/                        # 数据存储
│   └── db.py                      # 数据库操作
│
├── erp_sync/                       # ERP同步
│   ├── erp_client.py              # ERP客户端
│   ├── sync_service.py            # 同步服务
│   └── rule_engine.py             # 规则引擎
│
├── conversation_context/           # 对话上下文
│   ├── context_manager.py         # 上下文管理
│   └── session_lifecycle.py       # 会话生命周期
│
├── learning_loop/                  # 自动学习
│   └── knowledge_learner.py       # 知识学习
│
├── adapters/                       # 适配器（客户端用）
│   └── wxauto_adapter.py          # 微信适配器
│
└── integrations/                   # 外部集成
    ├── feishu_bitable.py          # 飞书多维表格
    └── dingtalk_bitable.py        # 钉钉多维表格
```

---

## 🧠 核心功能 (core/)

**服务器端核心业务**

```
core/
├── customer_manager.py             # 客户管理
│   • 客户分级（白/灰/黑名单）
│   • 状态机（新客→潜客→成交→复购）
│
├── conversation_tracker.py         # 对话追踪
│   • 完整对话串保存
│   • 质量评估
│   • 结果标记
│
├── system_monitor.py               # 系统监控 ⭐
│   • 系统资源监控
│   • 性能追踪
│   • 告警管理
│
├── error_handler.py                # 错误处理 ⭐
│   • 统一异常处理
│   • 重试机制
│   • 错误统计
│
├── performance_optimizer.py        # 性能优化 ⭐
│   • 缓存管理
│   • 数据库优化
│
├── config_loader.py                # 配置加载
└── system_integrator.py            # 系统集成
```

---

## 🌐 Web界面 (web/)

**Web管理后台**

```
web/
├── web_frontend.py                 # Flask应用
├── customer_hub_api.py             # 客户中台API
└── templates/                      # HTML模板
    ├── index.html                 # 首页
    ├── monitor.html               # 监控大盘
    ├── customers.html             # 客户管理
    └── logs.html                  # 日志查看
```

---

## 📚 文档 (docs/)

```
docs/
├── README.md                       # 文档索引 ⭐
│
├── guides/                         # 使用指南
│   ├── 快速开始.md
│   ├── INSTALLATION.md
│   ├── LLM_PROVIDERS.md
│   └── ...
│
├── features/                       # 功能文档
│   ├── 智能对话上下文管理方案.md
│   ├── 会话超时管理方案对比.md
│   ├── KNOWLEDGE_BASE_SOLUTION.md
│   └── ...
│
├── integrations/                   # 集成文档
│   ├── ERP同步系统README.md
│   ├── 表格同步使用说明.md
│   └── ...
│
└── erp_api/                        # ERP API文档
    ├── 智邦ERP_API完整索引.md
    └── api_by_category/           # 分类API文档
```

---

## 🧪 测试 (tests/)

```
tests/
├── test_system_enhancements.py     # 系统增强测试 ⭐
│   • 监控测试
│   • 缓存测试
│   • 错误处理测试
│
├── test_db.py                      # 数据库测试
├── test_rag_routing.py             # 知识库测试
├── test_customer_system.py         # 客户管理测试
└── ...

总计: 52个测试用例，96%通过率
```

---

## 🛠️ 脚本 (scripts/)

```
scripts/
├── check_db.py                     # 数据库检查
├── kb_manager.py                   # 知识库管理
├── upload_documents.py             # 文档上传
├── start_erp_sync.py               # ERP同步启动
└── ...
```

---

## 📄 配置文件

```
├── config.yaml                     # 主配置文件（服务器）
├── client/config/client_config.yaml # 客户端配置 ⭐
├── requirements.txt                # 原有依赖
├── requirements_client.txt         # 客户端依赖 ⭐
├── requirements_server.txt         # 服务器依赖 ⭐
├── docker-compose.yml              # Docker编排 ⭐
└── Dockerfile.server               # 服务器镜像 ⭐
```

---

## 🚀 启动脚本

```
├── start_server.sh/.bat            # 启动服务器 ⭐
├── start_client.sh/.bat            # 启动客户端 ⭐
├── start.bat                       # 旧版启动（兼容）
└── 启动Web界面.bat                  # Web界面启动
```

---

## 📊 代码统计

| 模块 | 文件数 | 代码行数 | 说明 |
|------|--------|---------|------|
| **client/** | 7个 | ~900行 | 轻量级客户端 ⭐ |
| **server/** | 7个 | ~650行 | FastAPI服务器 ⭐ |
| **modules/** | 60+个 | ~8000行 | 业务模块 |
| **core/** | 10个 | ~2500行 | 核心功能 |
| **web/** | 10个 | ~1000行 | Web界面 |
| **tests/** | 10个 | ~800行 | 测试用例 |
| **总计** | ~100个 | ~14,000行 | - |

---

## 🎯 架构特点

### 客户端（轻）

- ✅ 只做UI自动化
- ✅ 内存占用~50MB
- ✅ 启动速度快
- ✅ 支持低配PC

### 服务器（重）

- ✅ 所有复杂计算
- ✅ 集中数据管理
- ✅ 可水平扩展
- ✅ 微服务友好

### 通信

- ✅ REST API（同步）
- ✅ WebSocket（实时，可选）
- ✅ JWT认证
- ✅ AES-256加密

---

## 📖 相关文档

- [README.md](README.md) - 项目总览
- [START_HERE.md](START_HERE.md) - 快速开始
- [🏗️架构设计-C-S分离方案.md](🏗️架构设计-C-S分离方案.md) - 架构详解
- [📘C-S架构部署指南.md](📘C-S架构部署指南.md) - 部署手册
- [docs/README.md](docs/README.md) - 完整文档索引

---

**更新日期**: 2025-01-19  
**版本**: v2.0.0  
**架构**: Client-Server

