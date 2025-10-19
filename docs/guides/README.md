# 微信群聊客服中台

基于 **PC 微信 + wxauto** 的智能客服中台，实现群聊自动应答、RAG 知识检索、置信度分流与全链路可观测。

---

## 🏁 客户快速部署指南

1. **准备环境**  
   - Windows 10/11 专机，已登录最新 PC 微信并保持前台。  
   - 安装 Python 3.10+，确保 `python` / `pip` 命令可用。  
   - 建议使用管理员权限 PowerShell 或 CMD。

2. **解压代码包**  
   - 将交付目录放置到目标路径，例如 `C:\WeChatBot`。  
   - 进入目录：`cd C:\WeChatBot`。

3. **创建虚拟环境并安装依赖**  
   ```cmd
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
   > 若仅测试流程，可跳过 `wxauto`，真实部署必须安装。

4. **初始化数据库**  
   ```cmd
   mkdir data
   sqlite3 data\data.db < sql\init.sql
   ```
   > 无 sqlite3 命令时，可执行 `python -c "from storage.db import Database; Database('data/data.db').init_database()"`。

5. **配置运行参数**  
   - 编辑 `config.yaml`，在 `wechat.whitelisted_groups` 中填入目标群名。  
   - 如需调整 ACK、置信度阈值、速率限制，可在同一文件修改。  
   - 设置环境变量：  
     ```cmd
     set USE_FAKE_ADAPTER=false
     set OPENAI_API_KEY=sk-***  (Phase 3 开启后必填)
     ```

6. **功能连通性自检**  
   ```cmd
   # 运行单元测试（建议保留记录）
   python -m pytest -q

   # 首次运行使用假适配器验证主流程
   set USE_FAKE_ADAPTER=true
   python main.py
   ```
   - 在 Fake 模式下可调用 `FakeWxAdapter.inject_message` 进行演示。  
   - 确认 `data\data.db` 中 `messages` / `sessions` 表有新增记录。

7. **切换真实微信模式**  
   ```cmd
   set USE_FAKE_ADAPTER=false
   python main.py
   ```
   - 程序启动后保持窗口运行；若需后台运行，参考下文 NSSM 服务化。  
   - 建议管理员先在白名单群内测试 @ 触发、#status 等指令。

8. **故障排查与支持**  
   - 日志位于 `logs/app.log`（需确保 `logs/` 目录可写）。  
   - 若日志提示“wxauto 未安装”，请重新安装并确认以管理员启动。  
   - 常见问题与联系渠道见 README 后续章节。

完成以上步骤后即可正式对外提供群聊自动客服服务。生产部署前，请确认专机具备稳定网络、电源及桌面锁屏策略，避免微信离线。

---

## 📋 目录

- [功能特性](#功能特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [环境变量配置](#环境变量配置)
- [运行模式](#运行模式)
- [测试指南](#测试指南)
- [NSSM 服务化](#nssm-服务化)
- [常见问题](#常见问题)
- [开发路线图](#开发路线图)

---

## 🎯 功能特性

### 核心能力（已实现 - Phase 0-1）

- ✅ **@触发响应**：仅在群聊中被 @ 时响应
- ✅ **3秒 ACK**：被 @ 后 ≤3s 发出"收到，处理中……"
- ✅ **消息去重**：10秒窗口内相同消息自动去重
- ✅ **速率限制**：群级别 & 用户级别的频控保护
- ✅ **会话管理**：15分钟 TTL，自动滚动摘要（≤200字）
- ✅ **置信度分流**：
  - C ≥ 0.75 → 直答
  - 0.55 ≤ C < 0.75 → 澄清
  - C < 0.55 → 转人工
- ✅ **全量落库**：SQLite 存储，含 token、时延、证据ID
- ✅ **管理指令**：`#mute`、`#status`、`#debug on|off`
- ✅ **禁答域保护**：价格/交付/法务等自动转人工

### 新增功能（Phase 2-4 已完成）

- ✅ **RAG 检索**：BM25 关键词检索 + 向量检索（Chroma + BGE-M3）
- ✅ **多模型支持**：OpenAI, DeepSeek, Claude, 通义千问, 文心一言, Gemini, Moonshot
- ✅ **AI 网关**：主备自动降级，支持 7 个大模型提供商
- ✅ **多模态支持**：语音识别（FunASR）+ 图片识别（PaddleOCR + GPT-4V）
- ✅ **企业级知识库**：支持 PDF、DOC、图片等多格式文档
- ✅ **对话效果追踪**：记录是否解决、转人工原因、完整对话串
- ✅ **多维表格集成**：飞书/钉钉自动同步，对话级+消息级双视图
- ✅ **防封号机制**：拟人化行为 + 企业微信备用方案
- ✅ **自适应学习**：学习对话风格 + 用户画像 + 个性化回复 ⭐新
- ✅ **Windows一键部署**：8个批处理脚本，一键安装启动 ⭐新
- ✅ **运维工具**：健康检查、日志轮转、性能报告
- ✅ **CSV 导出**：日志导出与多维分析

---

## 🏗 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   主循环 (main.py)                   │
│  监听 → 降噪 → RAG → LLM → 发送 → 落库              │
└──────────┬──────────────────────────────────────────┘
           │
    ┌──────┴─────────┬──────────────┬──────────────┐
    │                │              │              │
┌───▼────┐   ┌──────▼──────┐  ┌───▼────┐   ┌─────▼──────┐
│ WxAuto │   │ RAG         │  │ AI     │   │ Database   │
│Adapter │   │ Retriever   │  │Gateway │   │ (SQLite)   │
└────────┘   └─────────────┘  └────────┘   └────────────┘
    │              │               │              │
    │              │               │              │
   PC微信      BM25+向量       OpenAI/       sessions/
  (仅此层)      重排           DeepSeek      messages
```

### 目录结构

```
project_root/
├── adapters/          # 微信适配层（仅此处与PC微信耦合）
│   └── wxauto_adapter.py
├── rag/               # RAG 检索器
│   └── retriever.py
├── storage/           # 数据持久化
│   └── db.py
├── ai_gateway/        # AI 网关（Phase 3）
├── sql/               # 数据库初始化脚本
│   └── init.sql
├── tests/             # 单元测试
│   ├── test_db.py
│   ├── test_triggering.py
│   └── test_rag_routing.py
├── main.py            # 主程序入口
├── config.yaml        # 配置文件
└── requirements.txt   # 依赖清单
```

---

## 🚀 快速开始

### 前置要求

- **操作系统**：Windows 10/11（PC 微信仅支持 Windows）
- **Python**：3.10+
- **PC 微信**：最新版本，已登录

### 1. 创建虚拟环境

```bash
# 克隆或下载代码到本地
cd "project_root"

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\activate  # Windows
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

**注意**：`wxauto` 在真实环境下安装，测试环境可跳过。

### 3. 初始化数据库

```bash
# 创建数据目录
mkdir data

# 执行初始化脚本
sqlite3 data/data.db < sql/init.sql
```

**或使用 Python 自动初始化**（推荐）：

```python
from storage.db import Database

db = Database("data/data.db")
db.init_database()
db.close()
```

### 4. 配置文件

编辑 `config.yaml`，设置白名单群聊：

```yaml
wechat:
  whitelisted_groups:
    - 技术支持群
    - VIP客户群
```

### 5. 运行（测试模式）

```bash
# 使用假适配器（无需真实微信）
python main.py
```

### 6. 运行（真实模式）

```bash
# 设置环境变量
set USE_FAKE_ADAPTER=false
set OPENAI_API_KEY=sk-your-key-here

# 确保 PC 微信已登录并打开
python main.py
```

### 7. 初始化知识库（推荐）

```bash
# 添加示例文档到知识库
python kb_manager.py --action add

# 查看知识库内容
python kb_manager.py --action list

# 测试检索
python kb_manager.py --action search --query "如何安装设备"
```

---

## 🔑 环境变量配置

### 大模型配置（选择一个或多个）

```bash
# OpenAI（推荐）
set OPENAI_API_KEY=sk-xxxxxxxxxxxxx
set OPENAI_MODEL=gpt-4o-mini

# DeepSeek（性价比高）
set DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx

# Claude（高质量）
set CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxx

# 通义千问（国内）
set QWEN_API_KEY=sk-xxxxxxxxxxxxx

# 文心一言（国内）
set ERNIE_API_KEY=client_id:client_secret

# Gemini（快速）
set GEMINI_API_KEY=xxxxxxxxxxxxx

# Moonshot/Kimi（长上下文）
set MOONSHOT_API_KEY=sk-xxxxxxxxxxxxx
```

详见 [大模型配置指南](docs/LLM_PROVIDERS.md)

### 可选配置

```bash
# 测试模式
set USE_FAKE_ADAPTER=true

# 飞书多维表格集成
set FEISHU_APP_ID=cli_xxxxxxxxxxxxx
set FEISHU_APP_SECRET=xxxxxxxxxxxxx
set FEISHU_BITABLE_TOKEN=bascnxxxxxxxxxxxxx
set FEISHU_TABLE_ID=tblxxxxxxxxxxxxx

# 钉钉多维表格集成
set DINGTALK_APP_KEY=dingtalkxxxxxxxxxxxxx
set DINGTALK_APP_SECRET=xxxxxxxxxxxxx
set DINGTALK_BASE_ID=xxxxxxxxxxxxx
set DINGTALK_TABLE_ID=xxxxxxxxxxxxx
```

详见文档：
- [多维表格集成指南](docs/MULTITABLE_INTEGRATION.md)
- [大模型配置指南](docs/LLM_PROVIDERS.md)

---

## 🎮 运行模式

### 测试模式（FakeWxAdapter）

适用于**开发调试**，无需真实微信环境：

```python
from adapters.wxauto_adapter import FakeWxAdapter

adapter = FakeWxAdapter(whitelisted_groups=["测试群"])

# 注入测试消息
adapter.inject_message(
    group_name="测试群",
    sender_name="张三",
    content="如何安装设备？",
    is_at_me=True
)

# 迭代消息
for msg in adapter.iter_new_messages():
    print(msg.content)
```

### 真实模式（WxAutoAdapter）

适用于**生产部署**，需 PC 微信运行：

```python
from adapters.wxauto_adapter import WxAutoAdapter

adapter = WxAutoAdapter(whitelisted_groups=["技术支持群"])

# 自动监听群聊消息
for msg in adapter.iter_new_messages():
    print(f"收到 @消息: {msg.content}")
```

---

## 🧪 测试指南

### 运行所有测试

```bash
pytest tests/ -v
```

### 运行特定测试文件

```bash
# 数据库测试
pytest tests/test_db.py -v

# 触发逻辑测试
pytest tests/test_triggering.py -v

# RAG 分流测试
pytest tests/test_rag_routing.py -v
```

### 测试覆盖率

```bash
pytest tests/ --cov=. --cov-report=html
```

### 测试注意事项

1. **数据库测试**使用临时文件，不影响生产数据
2. **适配器测试**使用 `FakeWxAdapter`，无需真实微信
3. **RAG 测试**使用桩实现，Phase 2 后替换为真实检索

---

## 🔧 NSSM 服务化

在 Windows 上使用 **NSSM** 将程序注册为系统服务：

### 1. 下载 NSSM

https://nssm.cc/download

### 2. 安装服务

```cmd
# 使用绝对路径
nssm install WeChatBot "C:\path\to\venv\Scripts\python.exe" "C:\path\to\main.py"

# 设置工作目录
nssm set WeChatBot AppDirectory "C:\path\to\project_root"

# 设置环境变量
nssm set WeChatBot AppEnvironmentExtra USE_FAKE_ADAPTER=false
nssm set WeChatBot AppEnvironmentExtra OPENAI_API_KEY=sk-xxxxx

# 设置日志
nssm set WeChatBot AppStdout "C:\path\to\logs\stdout.log"
nssm set WeChatBot AppStderr "C:\path\to\logs\stderr.log"
```

### 3. 启动服务

```cmd
nssm start WeChatBot
```

### 4. 管理服务

```cmd
# 查看状态
nssm status WeChatBot

# 停止服务
nssm stop WeChatBot

# 重启服务
nssm restart WeChatBot

# 卸载服务
nssm remove WeChatBot confirm
```

### 5. 服务配置建议

- **启动类型**：自动（延迟启动）
- **恢复策略**：失败后 1 分钟重启，最多重启 3 次
- **日志轮转**：定期归档 `stdout.log` 和 `stderr.log`

---

## ❓ 常见问题

### 1. wxauto 初始化失败

**症状**：`ImportError: cannot import name 'WeChat' from 'wxauto'`

**解决**：
- 确保在 **Windows** 系统上运行
- 确保 **PC 微信**已登录并保持前台
- 尝试重新安装：`pip install --upgrade wxauto`

### 2. 数据库锁定错误

**症状**：`sqlite3.OperationalError: database is locked`

**解决**：
- 确保只有一个进程访问数据库
- 检查是否有其他程序（如 SQLite 工具）打开了数据库
- 设置更长的超时：`conn.timeout = 10.0`

### 3. @识别失败

**症状**：被 @ 后没有响应

**原因**：
- 昵称获取失败（`get_my_name()` 返回错误）
- 正则表达式不匹配（特殊字符/表情）

**调试**：
```python
# 开启调试模式
logging.getLogger().setLevel(logging.DEBUG)

# 检查昵称
adapter = WxAutoAdapter(whitelisted_groups=["测试群"])
print(f"我的昵称: {adapter.get_my_name()}")
```

### 4. 速率限制误触发

**症状**：正常消息被提示"频率稍快"

**解决**：
- 调整 `config.yaml` 中的限制阈值
- 检查数据库中的 `rate_limits` 表，清理过期记录

### 5. CSV 导出乱码

**症状**：导出的 CSV 在 Excel 中显示乱码

**解决**：
- 使用 `encoding='utf-8-sig'` 写入（已实现）
- 或用 Excel 导入功能指定 UTF-8 编码

### 6. 日志文件过大

**解决**：
- 使用 `RotatingFileHandler` 限制大小
- 定期归档或清理旧日志

---

## 📊 管理指令

在白名单群聊中，**管理员**可以发送以下指令：

| 指令 | 功能 | 示例 |
|------|------|------|
| `#mute` | 开启全局静默 | @小助手 #mute |
| `#unmute` | 关闭全局静默 | @小助手 #unmute |
| `#status` | 查看系统状态 | @小助手 #status |
| `#debug on` | 开启调试模式 | @小助手 #debug on |
| `#debug off` | 关闭调试模式 | @小助手 #debug off |
| `#kb +文档` | 添加知识库文档（规划中） | @小助手 #kb +安装手册.pdf |
| `#bind 客户名` | 绑定客户名称（规划中） | @小助手 #bind 某某科技 |

**管理员配置**（`config.yaml`）：

```yaml
admin:
  names:
    - 管理员
    - 系统管理员
```

---

## 🛠 运维工具

### 知识库管理（kb_manager.py）

```bash
# 添加示例文档到知识库
python kb_manager.py --action add --db data/data.db

# 列出所有文档
python kb_manager.py --action list --db data/data.db

# 测试检索
python kb_manager.py --action search --query "设备过热怎么办" --db data/data.db

# 重建索引
python kb_manager.py --action rebuild --db data/data.db
```

### 系统运维（ops_tools.py）

```bash
# 健康检查
python ops_tools.py health --db data/data.db

# 性能报告（最近7天）
python ops_tools.py report --db data/data.db --days 7

# 日志轮转（超过50MB自动归档）
python ops_tools.py rotate --max-log-size 50

# 清理旧数据（90天前）
python ops_tools.py cleanup --db data/data.db --days 90
```

### 示例：定期运维任务

在 Windows 任务计划程序中设置：

```cmd
# 每天凌晨2点：健康检查
python ops_tools.py health

# 每天凌晨3点：同步到飞书多维表格
python sync_to_bitable.py sync --platform feishu --days 1

# 每天凌晨4点：同步到钉钉多维表格
python sync_to_bitable.py sync --platform dingtalk --days 1

# 每周日凌晨3点：日志轮转
python ops_tools.py rotate

# 每月1号凌晨4点：清理旧数据
python ops_tools.py cleanup --days 90

# 每周一早上9点：生成性能报告
python ops_tools.py report --days 7
```

### 多维表格同步

```bash
# 测试连接
python sync_to_bitable.py test --platform feishu
python sync_to_bitable.py test --platform dingtalk

# 同步数据
python sync_to_bitable.py sync --platform both --days 7
```

详见 [多维表格集成指南](docs/MULTITABLE_INTEGRATION.md)

---

## 🗺 开发路线图

### ✅ Phase 0：脚手架（已完成）
- [x] 项目结构与依赖
- [x] 配置文件与数据库初始化
- [x] 基础日志与存储模块
- [x] README 与测试框架

### ✅ Phase 1：监听与发送（已完成）
- [x] wxauto 适配器（真实 + 假适配器）
- [x] @识别与去重
- [x] 速率限制
- [x] ACK 确认
- [x] 主循环与分流

### ✅ Phase 2：RAG 检索（已完成）
- [x] BM25 关键词检索
- [x] 置信度计算
- [x] 证据引用格式化
- [x] 知识库加载接口
- [x] 知识库管理工具

### ✅ Phase 3：AI 网关（已完成）
- [x] OpenAI 调用（gpt-4o-mini）
- [x] DeepSeek 备用降级
- [x] 超时与重试逻辑
- [x] Token 计量
- [x] 系统指令组装

### ✅ Phase 4：运维工具（已完成）
- [x] 健康检查工具
- [x] 日志轮转
- [x] 性能报告
- [x] 数据清理
- [x] CSV 导出（Phase 1 已完成）

### 🔮 未来增强
- [ ] 向量嵌入与重排（提升检索精度）
- [ ] 会话历史管理（多轮对话）
- [ ] 图片/语音识别（OCR/ASR）
- [ ] Web 管理后台
- [ ] MCP (Model Context Protocol) 支持

---

## 📝 代码规范

- **类型标注**：所有函数必须有完整类型标注
- **函数长度**：<80 行
- **模块长度**：<400 行
- **命名**：
  - 变量/函数：`snake_case`
  - 类：`PascalCase`
  - 常量：`UPPER_SNAKE_CASE`
- **注释**：关键路径需注释"为何这样做"
- **日志前缀**：`req_id/session_id/group/sender/provider/conf/latency_ms/token_in/out/branch`

---

## 📄 许可证

MIT License

---

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 开启 Pull Request

**提交规范**：
- 每个 Phase 一个 PR
- 包含完整测试
- 更新 README 相关章节

---

## 📧 联系方式

- **项目负责人**：架构师团队
- **技术支持**：请提 Issue
- **商务合作**：请联系管理员

---

**最后更新**：2025-10-16  
**当前版本**：Phase 0-1（脚手架与监听功能已完成）
