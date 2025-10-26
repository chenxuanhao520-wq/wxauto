# 🎯 客户中台 (Customer Hub) - 完整实现

> 基于"最后说话方 + SLA"的智能客户分级系统  
> 未编码会话不遗漏 · 已读未回不失控 · LLM在正确节点介入

---

## ✨ 核心亮点

### 1️⃣ 状态机驱动的自动化管理
- **无需手动更新状态**：根据最后说话方和时间自动计算
- **SLA自动追踪**：客户发言30分钟内需回复，超时自动标记逾期
- **智能回弹**：我方发言48小时后自动回弹到待办

### 2️⃣ 白/灰/黑名单智能打分
- **综合评分**（0-100分）：关键词 + 文件类型 + 工作时间 + 知识库匹配
- **自动分级**：≥80分→白名单，≥60分→灰名单（未知池），<60分→黑名单
- **隐私保护**：黑名单不入库，灰名单未建档前只存派生指标

### 3️⃣ 三大触发场景
- **售前**：自动提取询价要素（功率/枪型/交期/发票），生成澄清问题和回复草稿
- **售后**：自动生成工单（报警码/故障现象/紧急程度），提供排查步骤和沟通话术
- **客户开发**：识别线索级别（A/B/C），生成商务脚本（首触达/次日跟进）

### 4️⃣ 未知池日清
- **不既读预览**：灰名单会话只显示摘要，不标记为已读
- **三键操作**：建档（升白）/ 忽略（推迟）/ 拉黑
- **清零率监控**：目标每日20:00清零率≥95%

---

## 🚀 5分钟快速启动

### 步骤1：初始化数据库
```bash
python test_customer_hub.py
```

### 步骤2：启动 Web 服务
```bash
python web_frontend.py
```

### 步骤3：访问界面
打开浏览器访问：
```
http://localhost:5000/customer-hub.html
```

---

## 📸 界面预览

### 三栏式布局

```
┌────────────────┬──────────────────────────┬────────────────┐
│  📥 未知池     │   📊 四象限看板          │  ⚡ 工作台     │
│  (灰名单)      │                          │                │
│                │  ┌─────────────────────┐ │  LLM摘要       │
│  不既读预览    │  │ 未处理 | 需回复 | ... │ │  一键复制      │
│                │  └─────────────────────┘ │                │
│  张先生        │                          │  表单信息      │
│  78分          │  会话卡片列表             │  - 功率: 320kW │
│  ┌──────────┐  │  ┌──────────────────┐   │  - 枪型: 双枪  │
│  │建档│忽略│  │  │ K3208-张三       │   │                │
│  └──────────┘  │  │ 逾期 | 售前      │   │  SLA操作       │
│                │  │ 10分钟前          │   │  [推迟][解决]  │
│                │  └──────────────────┘   │                │
└────────────────┴──────────────────────────┴────────────────┘
```

---

## 📡 API 快速参考

### 核心接口

| 接口 | 说明 | 示例 |
|------|------|------|
| `POST /api/hub/messages/process` | 处理入站消息 | 打分+状态更新+触发判断 |
| `GET /api/hub/unknown-pool` | 获取未知池 | 灰名单+未处理会话 |
| `POST /api/hub/contacts/promote` | 建档升级 | 生成K编码，升白名单 |
| `POST /api/hub/threads/{id}/snooze` | 推迟处理 | 延后1小时/24小时 |
| `POST /api/hub/threads/{id}/trigger` | 触发场景 | LLM生成表单+草稿 |

### 示例：处理微信消息

```bash
curl -X POST http://localhost:5000/api/hub/messages/process \
  -H "Content-Type: application/json" \
  -d '{
    "wx_id": "wx_customer_001",
    "text": "请问320kW充电桩价格多少？",
    "file_types": ["pdf"],
    "last_speaker": "them"
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "bucket": "GRAY",
    "total_score": 78,
    "status": "NEED_REPLY",
    "trigger_type": "售前"
  }
}
```

---

## 🧪 验收测试

运行测试套件验证系统：

```bash
python test_customer_hub.py
```

### 测试覆盖

✅ **状态机测试**（4个场景）
- 客户发言未超时 → NEED_REPLY
- 客户发言超时 → OVERDUE  
- 我方发言未超时 → WAITING_THEM
- 我方发言超时 → NEED_REPLY（回弹）

✅ **打分引擎测试**（4个场景）  
- 售前消息 → GRAY（78分）
- 售后消息 → GRAY（72分）
- 客户开发 → GRAY（68分）
- 个人会话 → BLACK（0分）

✅ **触发器测试**（3个场景）  
- 售前 → 询价要素表 + 澄清问题 + 回复草稿
- 售后 → 工单表 + 排查步骤 + 沟通话术
- 客户开发 → 线索表 + 商务脚本

✅ **集成测试**  
- 样例事件导入（4条）
- 验收标准检查（100%通过）

---

## 🎨 核心架构

```
┌─────────────────────────────────────────────────────────┐
│                  客户中台 Customer Hub                   │
└─────────────────────────────────────────────────────────┘
                            ▼
         ┌──────────────────┴───────────────────┐
         │                                       │
    入站消息                                 定时任务
  (InboundMessage)                          (Cron Job)
         │                                       │
         ▼                                       ▼
┌─────────────────┐                    ┌─────────────────┐
│  Service Layer  │◄───────────────────│  State Machine  │
│  消息处理/建档   │                    │  状态计算/SLA    │
└─────────────────┘                    └─────────────────┘
         │
         ├─────────┬──────────┬──────────┐
         ▼         ▼          ▼          ▼
   ┌─────────┬─────────┬─────────┬──────────┐
   │ Scoring │Triggers │Repository│ REST API │
   │ 打分引擎 │ 触发器  │ 数据访问 │ Flask API│
   └─────────┴─────────┴─────────┴──────────┘
                        │
                        ▼
              ┌──────────────────┐
              │  SQLite Database │
              │  contacts/threads│
              │  signals/outputs │
              └──────────────────┘
```

---

## 🔧 配置与调优

### SLA 配置

```python
# customer_hub/state_machine.py

SLAConfig(
    need_reply_minutes=30,   # 客户发言后回复时限
    follow_up_hours=48       # 我方发言后回弹时限
)
```

### 打分规则

```python
# customer_hub/types.py - ScoringRules

keywords = {
    "pre": ["报价", "价格", "参数", "交期", ...],
    "post": ["故障", "报错", "报警码", ...],
    "bizdev": ["代理", "渠道", "合作", ...]
}

white_promotion_threshold = 80  # 升白阈值
gray_lower = 60                  # 灰名单下限
```

### 黑名单关键词

```python
blacklist_keywords = [
    "吃饭", "撸串", "喝酒", "打球", "游戏", "电影"
]
```

---

## 📊 KPI 监控

系统自动记录以下指标（`daily_metrics` 表）：

| 指标 | 目标值 | 说明 |
|------|--------|------|
| **未知池清零率** | ≥ 95% | 每日20:00未知池清空比例 |
| **平均响应时间** | ≤ 30分钟 | 白名单客户平均等待时长 |
| **逾期率** | ≤ 5% | 超过SLA的会话比例 |
| **建档转化率** | - | 灰名单→白名单的转化率 |

---

## 🔌 集成示例

### 在现有系统中接入

```python
from customer_hub.service import CustomerHubService
from customer_hub.types import InboundMessage, Party

# 初始化服务
hub = CustomerHubService()

# 在微信消息回调中
def on_wechat_message(wx_id, text, file_types):
    # 构建消息对象
    msg = InboundMessage(
        wx_id=wx_id,
        text=text,
        file_types=file_types,
        timestamp=datetime.now(),
        last_speaker=Party.THEM
    )
    
    # 处理消息
    result = hub.process_inbound_message(msg, kb_matched=False)
    
    # 根据结果决定下一步
    if result['bucket'] == 'WHITE':
        # 白名单客户，优先处理
        pass
    elif result['bucket'] == 'GRAY':
        # 灰名单，进入未知池
        if result['trigger_type']:
            # 异步触发LLM
            asyncio.create_task(
                hub.trigger_scenario(
                    thread_id=result['thread_id'],
                    text=text,
                    trigger_type=result['trigger_type']
                )
            )
    # BLACK会话自动忽略
```

---

## 📚 文档导航

- 📖 [完整使用指南](docs/CUSTOMER_HUB_GUIDE.md) - 详细API文档、配置说明
- 📦 [交付文档](CUSTOMER_HUB_DELIVERY.md) - 功能清单、验收标准
- 🧪 [测试用例](test_customer_hub.py) - 单元测试、集成测试
- 🗄️ [数据库脚本](sql/upgrade_customer_hub.sql) - 表结构、视图、索引

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | Flask + Blueprint |
| **数据库** | SQLite (支持迁移到 PostgreSQL) |
| **数据访问** | Repository Pattern (原生SQL) |
| **前端** | HTML + CSS + JavaScript (原生，无依赖) |
| **状态机** | 自定义实现 (Python dataclass) |
| **打分引擎** | 基于规则的综合评分 |
| **触发器** | LLM提示词模板 (支持 OpenAI/DeepSeek) |
| **异步** | Python asyncio |

---

## 🔐 隐私与合规

✅ **只存派生指标**  
- 不长期存储对话全文
- 仅保存：最后说话方、时间戳、关键词计数、文件类型、LLM摘要（≤200字）

✅ **黑名单保护**  
- `bucket=BLACK` 的会话不入库
- 仅用于去重与屏蔽

✅ **本地向量库**  
- 如需检索，使用本地嵌入（如 BGE-M3）
- 不上传外网

✅ **默认只索引白/灰名单**  
- 个人会话自动黑名单，不参与统计

---

## 🐛 故障排查

### 未知池为空？

**问题**：明明有灰名单会话，但未知池显示为空  
**原因**：未知池只显示 `UNSEEN` / `NEED_REPLY` / `OVERDUE` 状态  
**解决**：检查会话状态，手动重算：

```bash
curl -X POST http://localhost:5000/api/hub/cron/recalc
```

### 状态未自动更新？

**问题**：客户发言超过30分钟，仍显示 `NEED_REPLY` 而非 `OVERDUE`  
**原因**：需要定时任务触发状态重算  
**解决**：配置定时任务（每小时或每30分钟）：

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.add_job(
    hub.recalc_all_threads, 
    'interval', 
    hours=1
)
scheduler.start()
```

### 数据库表不存在？

**问题**：启动报错 `no such table: threads`  
**解决**：运行升级脚本

```bash
sqlite3 data/data.db < sql/upgrade_customer_hub.sql
```

或运行测试（会自动初始化）：

```bash
python test_customer_hub.py
```

---

## 🔮 后续扩展

### 1. 启用真实 LLM

```python
from ai_gateway.gateway import AIGateway

# 使用现有的 AI Gateway
llm_client = AIGateway()

trigger_engine = TriggerEngine(llm_client=llm_client)
hub_service = CustomerHubService(trigger_engine=trigger_engine)
```

### 2. 配置定时任务

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# 每小时重算所有线程状态
scheduler.add_job(hub.recalc_all_threads, 'interval', hours=1)

# 每日20:00生成指标报告
scheduler.add_job(generate_daily_metrics, 'cron', hour=20)

scheduler.start()
```

### 3. 消息队列（高并发场景）

```python
from celery import Celery

celery_app = Celery('customer_hub', broker='redis://localhost:6379')

@celery_app.task
def process_message_async(wx_id, text, file_types):
    hub.process_inbound_message(...)
```

### 4. PostgreSQL 迁移（大规模）

```python
# 修改 repository.py
from sqlalchemy import create_engine

engine = create_engine('postgresql://user:pass@localhost/dbname')
```

---

## 📞 支持与反馈

如有问题，请参考：

1. 📖 [完整文档](docs/CUSTOMER_HUB_GUIDE.md)
2. 🧪 [测试用例](test_customer_hub.py)
3. 📦 [交付文档](CUSTOMER_HUB_DELIVERY.md)

---

## 📜 变更日志

### v1.0.0 (2025-10-18)

**新功能**
- ✅ 状态机：基于"最后说话方 + SLA"的自动状态管理
- ✅ 打分引擎：白/灰/黑名单智能分级（0-100分）
- ✅ 三大触发器：售前/售后/客户开发场景识别与LLM生成
- ✅ 未知池日清：不既读预览 + 三键操作（建档/忽略/拉黑）
- ✅ REST API：12个端点，完整的CRUD操作
- ✅ Web 界面：三栏式布局（未知池/看板/工作台）
- ✅ 测试套件：单元测试 + 集成测试 + API测试
- ✅ 文档：使用指南 + API文档 + 交付文档

**验收标准**
- ✅ 所有测试通过（100%）
- ✅ 样例事件正确识别（售前/售后/客户开发/黑名单）
- ✅ 状态机正确计算（NEED_REPLY/WAITING_THEM/OVERDUE）
- ✅ 未知池清零率监控就绪

---

**版本**: v1.0.0  
**交付时间**: 2025-10-18  
**状态**: ✅ 生产就绪  

---

## 🎉 开始使用

```bash
# 1. 运行测试
python test_customer_hub.py

# 2. 启动服务
python web_frontend.py

# 3. 访问界面
# http://localhost:5000/customer-hub.html
```

**祝使用愉快！** 🚀

