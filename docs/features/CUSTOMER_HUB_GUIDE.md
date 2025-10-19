# 客户中台使用指南

## 📖 概述

客户中台 (Customer Hub) 是一个基于"**最后说话方 + SLA**"状态机的智能客户分级系统。它通过**白/灰/黑名单**置信打分、**未知池日清**和**三大触发场景**（售前/售后/客户开发），实现：

- ✅ 未编码会话不遗漏
- ✅ 已读未回不失控  
- ✅ LLM 在正确节点介入
- ✅ 隐私底线保护（默认只索引白/灰名单）

---

## 🏗️ 架构设计

### 核心概念

1. **Party (对话方)**
   - `me`: 我方（客服/销售）
   - `them`: 客户

2. **ThreadStatus (会话状态)**
   - `UNSEEN`: 未处理
   - `NEED_REPLY`: 需回复（客户最后发言）
   - `WAITING_THEM`: 等待对方（我方最后发言）
   - `OVERDUE`: 逾期未回复
   - `RESOLVED`: 已解决
   - `SNOOZED`: 已推迟

3. **Bucket (名单分类)**
   - `WHITE`: 白名单（已建档客户，K编码）
   - `GRAY`: 灰名单（潜在客户，未建档，进入未知池）
   - `BLACK`: 黑名单（个人会话，不入库）

4. **SLA 时间点**
   - `sla_at`: 客户最后发言后的回复截止时间（默认30分钟）
   - `follow_up_at`: 我方最后发言后的回弹时间（默认48小时）
   - `snooze_at`: 手动推迟的唤醒时间

---

## 🚀 快速开始

### 1. 数据库初始化

```bash
# 运行升级脚本
sqlite3 data/data.db < sql/upgrade_customer_hub.sql
```

或在 Python 中：

```python
from customer_hub.repository import CustomerHubRepository

repo = CustomerHubRepository()
# 会自动连接到 data/data.db

# 执行升级脚本（首次使用）
import sqlite3
conn = repo.connect()
with open('sql/upgrade_customer_hub.sql', 'r', encoding='utf-8') as f:
    conn.executescript(f.read())
```

### 2. 运行测试

```bash
python test_customer_hub.py
```

预期输出：
```
✅ 所有测试通过!
🎉 客户中台系统验收通过!
```

### 3. 启动 Web 界面

将客户中台 API 注册到现有 Flask 应用：

```python
# 在 web_frontend.py 或 main.py 中
from customer_hub_api import register_customer_hub_api

app = Flask(__name__)
register_customer_hub_api(app)  # 注册客户中台 API

# 添加路由
@app.route('/customer-hub.html')
def customer_hub_page():
    return render_template('customer_hub.html')
```

访问: `http://localhost:5000/customer-hub.html`

---

## 📡 API 接口

### 基础路径
`/api/hub/*`

### 1. 消息处理

**POST** `/api/hub/messages/process`

处理入站消息，自动打分、更新状态、判断触发类型。

**Request Body:**
```json
{
  "wx_id": "wx_u_001",
  "text": "320kW充电桩报价多少？",
  "file_types": ["pdf"],
  "last_speaker": "them",
  "timestamp": "2025-10-18T09:10:00Z",
  "kb_matched": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "消息处理完成",
  "data": {
    "contact_id": "uuid...",
    "thread_id": "uuid...",
    "signal_id": "uuid...",
    "bucket": "GRAY",
    "total_score": 78,
    "status": "NEED_REPLY",
    "trigger_type": "售前"
  }
}
```

---

### 2. 未知池

**GET** `/api/hub/unknown-pool?limit=100`

获取灰名单且未处理的会话（需要建档的潜在客户）。

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "thread_id": "...",
      "contact_id": "...",
      "wx_id": "wx_u_001",
      "remark": "张先生",
      "last_speaker": "them",
      "last_msg_at": "2025-10-18T09:10:00",
      "status": "NEED_REPLY",
      "topic": "询问充电桩报价",
      "total_score": 78,
      "keyword_hits": {"报价": 1, "价格": 1},
      "file_types": ["pdf"]
    }
  ]
}
```

---

### 3. 今日待办

**GET** `/api/hub/today-todo?limit=100`

获取所有需要处理的会话（白名单 + 灰名单）。

---

### 4. 建档升级

**POST** `/api/hub/contacts/promote`

将灰名单联系人升级为正式客户（生成 K 编码，升白）。

**Request Body:**
```json
{
  "contact_id": "uuid...",
  "customer_name": "张三",
  "region": "渝A",
  "level": "VIP",
  "owner": "销售A"
}
```

**Response:**
```json
{
  "success": true,
  "message": "建档成功",
  "data": {
    "contact_id": "...",
    "k_code": "K3208-渝A-张三-VIP-微信",
    "type": "customer",
    "confidence": 100
  }
}
```

---

### 5. 状态操作

#### 推迟处理 (Snooze)

**POST** `/api/hub/threads/{thread_id}/snooze`

```json
{
  "snooze_minutes": 60
}
```

#### 标记为等待对方

**POST** `/api/hub/threads/{thread_id}/waiting`

```json
{
  "follow_up_hours": 48
}
```

#### 标记为已解决

**POST** `/api/hub/threads/{thread_id}/resolve`

---

### 6. 触发场景

**POST** `/api/hub/threads/{thread_id}/trigger`

调用 LLM 生成结构化表单和回复草稿。

**Request Body:**
```json
{
  "text": "你好，发下320kW双枪报价和交期，含税，发票要专票。",
  "trigger_type": "售前"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "output_id": "...",
    "trigger_type": "售前",
    "form": {
      "功率_kW": 320,
      "枪型": "双枪",
      "发票要求": "专票"
    },
    "reply_draft": "感谢您的咨询！根据您提供的信息...",
    "labels": ["售前"]
  }
}
```

---

### 7. 定时任务

**POST** `/api/hub/cron/recalc`

重新计算所有线程的状态（建议每小时执行一次）。

---

## 🎨 前端界面

访问 `/customer-hub.html` 可查看：

### 布局

- **左侧**: 📥 未知池（灰名单）
  - 不既读预览
  - 三键操作：建档 / 忽略 / 拉黑

- **中间**: 📊 四象限看板
  - 计数器：未处理 | 需回复 | 等待对方 | 逾期 | 已解决
  - 会话卡片列表

- **右侧**: ⚡ 工作台
  - LLM 摘要与一键复制话术
  - 表单（售前询价/售后工单/开发记录）
  - SLA 操作（推迟/等待对方/关闭）

---

## 🧪 测试用例

### 样例事件

来自需求文档的四个测试用例：

1. **t001**: 售前询价（320kW双枪报价） → GRAY，触发售前
2. **t002**: 售后工单（报警码E103） → GRAY，触发售后
3. **t003**: 客户开发（代理政策） → GRAY，触发客户开发
4. **t004**: 个人会话（晚上撸串） → BLACK，不触发

### 运行验收测试

```bash
python test_customer_hub.py
```

检查项：
- [x] t001 命中"售前"
- [x] t002 命中"售后"
- [x] t003 命中"客户开发"
- [x] t004 进入黑名单，不触发
- [x] 状态机正确计算 NEED_REPLY / WAITING_THEM / OVERDUE
- [x] 打分引擎正确判定白/灰/黑

---

## ⚙️ 配置

### SLA 配置

在代码中调整：

```python
from customer_hub.state_machine import SLAConfig, StateMachine

sla_config = SLAConfig(
    unseen_minutes=0,       # 未处理进入 NEED_REPLY 的阈值
    need_reply_minutes=30,  # 客户最后发言后需回复 SLA（分钟）
    follow_up_hours=48      # 我方最后发言后回弹窗口（小时）
)

state_machine = StateMachine(sla_config)
```

### 打分规则

在 `customer_hub/types.py` 中调整 `ScoringRules`:

```python
@dataclass
class ScoringRules:
    # 关键词分组
    keywords: Dict[str, List[str]] = field(default_factory=lambda: {
        "pre": ["报价", "价格", "参数", "型号", "交期", ...],
        "post": ["故障", "报错", "报警码", "返修", ...],
        "bizdev": ["代理", "渠道", "合作", "资质", ...]
    })
    
    # 阈值
    white_promotion_threshold: int = 80  # 升白阈值
    gray_lower: int = 60                  # 灰名单下限
    
    # 黑名单关键词
    blacklist_keywords: List[str] = field(default_factory=lambda: [
        "吃饭", "撸串", "喝酒", "打球", "游戏", "电影"
    ])
```

---

## 🔌 集成到现有系统

### 1. 在 `main.py` 中注册 API

```python
from flask import Flask, render_template
from customer_hub_api import register_customer_hub_api

app = Flask(__name__)

# 注册客户中台 API
register_customer_hub_api(app)

# 添加前端页面路由
@app.route('/customer-hub.html')
def customer_hub_page():
    return render_template('customer_hub.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### 2. 在消息处理流程中调用

```python
from customer_hub.service import CustomerHubService
from customer_hub.types import InboundMessage, Party

hub_service = CustomerHubService()

# 在接收到微信消息时
def on_wechat_message(wx_id, text, file_types, last_speaker):
    message = InboundMessage(
        wx_id=wx_id,
        thread_id="",  # 可选
        text=text,
        file_types=file_types,
        timestamp=datetime.now(),
        last_speaker=Party(last_speaker)
    )
    
    # 处理消息
    result = hub_service.process_inbound_message(
        message, 
        kb_matched=False  # 如果有知识库检索，设为 True
    )
    
    # 根据结果决定是否自动回复
    if result['bucket'] in ['WHITE', 'GRAY']:
        if result['trigger_type']:
            # 可以异步触发 LLM 生成回复
            pass
```

### 3. 配置定时任务

使用 `cron` 或 `APScheduler`:

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def recalc_all_threads():
    """每小时重算所有线程状态"""
    hub_service.recalc_all_threads()
    print("线程状态已重算")

# 每小时执行一次
scheduler.add_job(recalc_all_threads, 'interval', hours=1)
scheduler.start()
```

---

## 📊 每日指标

系统自动记录每日指标（`daily_metrics` 表）：

- `unknown_pool_count`: 未知池数量
- `promoted_count`: 建档数量
- `clear_rate`: 清零率
- `avg_response_time_min`: 平均响应时间（分钟）
- `overdue_count`: 逾期数量

### 目标 KPI

- **未知池清零率**: ≥ 95%（每日 20:00）
- **平均响应时间**: ≤ 30 分钟（白名单客户）
- **逾期率**: ≤ 5%

---

## 🔐 隐私与合规

### 只存派生指标模式

默认不长期存储对话全文，仅保存：
- `last_speaker`: 最后说话方
- `last_msg_at`: 最后消息时间
- `keyword_hits`: 关键词命中次数（JSON）
- `file_types`: 文件类型列表（JSON）
- `topic`: LLM 生成的摘要（≤200字）

### 本地向量库模式

如需检索，使用本地嵌入与向量库（如 Chroma），不上传外网。

### 黑名单保护

`bucket=BLACK` 的联系人：
- 不进入任何触发或统计
- 不长期存储
- 仅用于去重与屏蔽

---

## 🐛 故障排查

### 1. 数据库表不存在

```bash
sqlite3 data/data.db < sql/upgrade_customer_hub.sql
```

### 2. 未知池为空但有灰名单会话

检查会话状态：
```sql
SELECT status, COUNT(*) FROM threads WHERE bucket='GRAY' GROUP BY status;
```

未知池只显示 `UNSEEN`、`NEED_REPLY`、`OVERDUE` 状态。

### 3. 状态未自动更新

手动触发重算：
```bash
curl -X POST http://localhost:5000/api/hub/cron/recalc
```

或设置定时任务（见上文）。

---

## 📚 扩展阅读

- [架构设计文档](./CUSTOMER_HUB_ARCHITECTURE.md)
- [API 完整文档](./CUSTOMER_HUB_API.md)
- [前端组件说明](./CUSTOMER_HUB_FRONTEND.md)

---

## 🎯 下一步

1. ✅ 运行测试验证系统可用
2. ✅ 集成到现有微信消息处理流程
3. ✅ 配置 LLM 客户端（如 OpenAI、DeepSeek）
4. ✅ 启动 Web 界面，体验未知池日清
5. ✅ 设置定时任务，自动重算状态
6. ✅ 收集真实数据，调优打分规则

---

**版本**: v1.0.0  
**更新时间**: 2025-10-18  
**作者**: Customer Hub Team

