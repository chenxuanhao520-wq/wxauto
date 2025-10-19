# 对话效果追踪与完整对话保存指南

本文档介绍如何使用对话追踪功能，实现对话效果分析和完整对话保存。

---

## 🎯 功能概述

### 核心能力

1. **对话效果追踪**
   - ✅ 自动判断对话是否解决问题
   - ✅ 记录解决方式（AI/人工/自助）
   - ✅ 标记对话结果（已解决/未解决/转人工/放弃）
   - ✅ 可添加备注说明原因

2. **完整对话保存**
   - ✅ 保存完整对话串（包含所有轮次）
   - ✅ 支持上下文关联
   - ✅ 多轮对话统一管理
   - ✅ 便于后续分析和追溯

3. **数据可视化**
   - ✅ 在多维表格中展示对话级别数据
   - ✅ 支持按结果、标签、解决方式筛选
   - ✅ 自动生成对话摘要

---

## 📊 数据结构

### 对话级别字段（Sessions表）

| 字段名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| conversation_outcome | 文本 | 对话结果 | solved/unsolved/transferred/abandoned |
| outcome_reason | 文本 | 结果原因/备注 | AI直接解答 / 需要人工协助 |
| resolved_by | 文本 | 解决方式 | ai / human / self |
| satisfaction_score | 数字 | 满意度评分 | 1-5 |
| tags | 文本 | 对话标签 | 售后,安装问题 |
| total_messages | 数字 | 总消息数 | 8 |
| ai_messages | 数字 | AI回复数 | 4 |
| resolution_time_sec | 数字 | 解决用时（秒） | 180 |
| conversation_thread | JSON | 完整对话串 | {...} |
| first_response_time_ms | 数字 | 首次响应时间 | 2500 |

### 对话结果类型

- **solved**: 问题已解决
- **unsolved**: 问题未解决
- **transferred**: 转人工处理
- **abandoned**: 用户放弃

### 解决方式类型

- **ai**: AI自动解决
- **human**: 人工解决
- **self**: 用户自助解决

### 标签示例

- `售后` - 售后服务
- `技术支持` - 技术支持
- `安装问题` - 安装相关
- `故障排查` - 故障排查
- `价格咨询` - 价格相关
- `转人工` - 需转人工
- `待澄清` - 需要更多信息
- `AI解决` - AI成功解决

---

## 🚀 使用方法

### 1. 数据库升级

首先执行升级脚本：

```bash
# 备份数据库
cp data/data.db data/data.db.backup

# 执行升级
sqlite3 data/data.db < sql/upgrade_v3.1.sql

# 验证
sqlite3 data/data.db "PRAGMA table_info(sessions);"
```

### 2. 在代码中使用

#### 初始化追踪器

```python
from conversation_tracker import ConversationTracker, ConversationOutcome
from storage.db import Database

db = Database("data/data.db")
tracker = ConversationTracker(db)
```

#### 开始对话时设置标签

```python
# 开始对话，标记为"售后"
tracker.start_conversation(
    session_key="group_id:user_id",
    tags=["售后", "安装问题"]
)
```

#### 记录对话消息

```python
# 记录用户消息
tracker.add_message_to_thread(
    session_key="group_id:user_id",
    message_id="req_123",
    role="user",
    content="如何安装设备？",
    metadata={'timestamp': datetime.now().isoformat()}
)

# 记录AI回复
tracker.add_message_to_thread(
    session_key="group_id:user_id",
    message_id="req_123",
    role="assistant",
    content="请参考安装手册第3章...",
    metadata={
        'confidence': 0.85,
        'model': 'gpt-4o-mini',
        'tokens': 150
    }
)
```

#### 标记对话结果

**方式1：手动标记**

```python
# 问题已解决（AI解决）
outcome = ConversationOutcome(
    outcome='solved',
    reason='AI成功解答安装问题',
    resolved_by='ai',
    satisfaction_score=5,
    tags=['售后', 'AI解决']
)
tracker.mark_outcome("group_id:user_id", outcome)

# 转人工
outcome = ConversationOutcome(
    outcome='transferred',
    reason='涉及价格问题，需要销售介入',
    resolved_by='human',
    tags=['价格咨询', '转人工']
)
tracker.mark_outcome("group_id:user_id", outcome)

# 失败
outcome = ConversationOutcome(
    outcome='unsolved',
    reason='系统异常，无法处理',
    resolved_by='unknown',
    tags=['失败', '系统异常']
)
tracker.mark_outcome("group_id:user_id", outcome)
```

**方式2：自动评估**

```python
# 根据最后的分支和状态自动评估
outcome = tracker.auto_evaluate_outcome(
    session_key="group_id:user_id",
    last_branch='direct_answer',  # direct_answer/clarification/handoff
    last_status='answered',        # answered/failed
    avg_confidence=0.85
)
tracker.mark_outcome("group_id:user_id", outcome)
```

#### 获取对话摘要

```python
# 获取完整对话摘要
summary = tracker.get_conversation_summary("group_id:user_id")

print(f"对话结果: {summary['outcome']}")
print(f"解决方式: {summary['resolved_by']}")
print(f"对话轮数: {summary['turn_count']}")
print(f"完整对话串:")
for msg in summary['conversation_thread']:
    print(f"  {msg['role']}: {msg['content']}")
```

#### 获取上下文用于AI

```python
# 获取最近5轮对话历史
context = tracker.get_conversation_thread_for_context(
    session_key="group_id:user_id",
    max_turns=5
)

# 传递给AI网关
response = ai_gateway.generate(
    user_message="新问题",
    session_history=context  # 包含上下文
)
```

---

## 📈 多维表格集成

### 两种视图

#### 1. 对话级别视图（推荐）

**表格字段**：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 会话ID | 文本 | 唯一标识 |
| 群名称 | 文本 | 群聊名称 |
| 用户 | 文本 | 用户昵称 |
| 客户名称 | 文本 | 绑定的客户 |
| **对话结果** | 单选 | solved/unsolved/transferred/abandoned |
| **结果说明** | 文本 | 备注原因 |
| **解决方式** | 单选 | ai/human/self |
| **满意度** | 数字 | 1-5分 |
| **标签** | 多选 | 售后、技术支持等 |
| 对话轮数 | 数字 | 交互轮次 |
| 总消息数 | 数字 | 消息总数 |
| AI消息数 | 数字 | AI回复数 |
| 解决用时(秒) | 数字 | 解决时长 |
| **完整对话** | 多行文本 | 对话内容 |
| 平均置信度 | 数字 | AI置信度 |
| 总Token数 | 数字 | Token消耗 |
| 开始时间 | 日期 | 对话开始 |
| 结束时间 | 日期 | 对话结束 |

**同步方法**：

```bash
# 需要在飞书创建"对话表"（不同于"消息表"）
python sync_to_bitable.py sync-conversations --platform feishu --days 7
```

#### 2. 消息级别视图（原有）

保持现有的消息级别同步。

**两种视图的关系**：
- 对话表：一个对话一条记录（适合分析效果）
- 消息表：一条消息一条记录（适合查看细节）
- 通过会话ID关联

### 在飞书中创建分析视图

#### 视图1：按结果统计

```
分组：对话结果
聚合：
  - 计数：会话ID
  - 平均：满意度
  - 平均：解决用时(秒)
筛选：
  - 开始时间 >= 最近7天
```

#### 视图2：按标签分析

```
分组：标签
聚合：
  - 计数：会话ID
  - 平均：对话轮数
  - 求和：总Token数
```

#### 视图3：售后问题追踪

```
筛选：
  - 标签包含"售后"
  - 对话结果 = "unsolved" 或 "transferred"
排序：
  - 开始时间降序
```

---

## 💡 实际案例

### 案例1：售后问题成功解决

```python
# 1. 开始对话
tracker.start_conversation(
    session_key="support_group:user_001",
    tags=["售后", "安装问题"]
)

# 2. 用户提问
tracker.add_message_to_thread(
    session_key="support_group:user_001",
    message_id="req_001",
    role="user",
    content="设备安装后无法启动"
)

# 3. AI回答
tracker.add_message_to_thread(
    session_key="support_group:user_001",
    message_id="req_001",
    role="assistant",
    content="请检查：① 电源连接是否正常 ② 保险丝是否熔断...",
    metadata={'confidence': 0.88, 'model': 'gpt-4o-mini'}
)

# 4. 用户继续
tracker.add_message_to_thread(
    session_key="support_group:user_001",
    message_id="req_002",
    role="user",
    content="检查后发现是保险丝问题，已解决，谢谢！"
)

# 5. 标记为已解决
outcome = ConversationOutcome(
    outcome='solved',
    reason='用户按照AI指引自行解决保险丝问题',
    resolved_by='ai',
    satisfaction_score=5,
    tags=['售后', '安装问题', 'AI解决', '自助解决']
)
tracker.mark_outcome("support_group:user_001", outcome)
```

**多维表格展示**：
```
会话ID: support_group:user_001
对话结果: ✅ solved
结果说明: 用户按照AI指引自行解决保险丝问题
解决方式: ai
满意度: ⭐⭐⭐⭐⭐ (5分)
标签: 售后, 安装问题, AI解决, 自助解决
对话轮数: 2
解决用时: 125秒
完整对话:
  用户: 设备安装后无法启动
  AI: 请检查：① 电源连接是否正常 ② 保险丝是否熔断...
  用户: 检查后发现是保险丝问题，已解决，谢谢！
```

### 案例2：复杂问题转人工

```python
# 1. 开始对话
tracker.start_conversation(
    session_key="vip_group:user_002",
    tags=["技术支持", "故障排查"]
)

# 2-4. 多轮对话（略）

# 5. 最终转人工
outcome = ConversationOutcome(
    outcome='transferred',
    reason='设备故障复杂，涉及硬件维修，需要工程师现场处理',
    resolved_by='human',
    satisfaction_score=4,
    tags=['技术支持', '硬件故障', '转人工', '需现场']
)
tracker.mark_outcome("vip_group:user_002", outcome)
```

**多维表格展示**：
```
会话ID: vip_group:user_002
对话结果: 🔄 transferred
结果说明: 设备故障复杂，涉及硬件维修，需要工程师现场处理
解决方式: human
满意度: ⭐⭐⭐⭐ (4分)
标签: 技术支持, 硬件故障, 转人工, 需现场
对话轮数: 5
解决用时: 380秒
```

### 案例3：系统失败

```python
outcome = ConversationOutcome(
    outcome='unsolved',
    reason='LLM调用超时，无法生成回复',
    resolved_by='unknown',
    tags=['失败', '系统异常', '超时']
)
tracker.mark_outcome("group_id:user_id", outcome)
```

---

## 📊 数据分析示例

### SQL 查询示例

#### 1. 按结果统计

```sql
SELECT 
    conversation_outcome,
    COUNT(*) as count,
    AVG(satisfaction_score) as avg_satisfaction,
    AVG(resolution_time_sec) as avg_time
FROM sessions
WHERE created_at >= datetime('now', '-7 days')
GROUP BY conversation_outcome;
```

#### 2. AI解决率

```sql
SELECT 
    DATE(created_at) as date,
    COUNT(CASE WHEN resolved_by = 'ai' THEN 1 END) * 100.0 / COUNT(*) as ai_resolution_rate
FROM sessions
WHERE created_at >= datetime('now', '-30 days')
GROUP BY DATE(created_at);
```

#### 3. 标签分析

```sql
SELECT 
    tags,
    COUNT(*) as count,
    AVG(turn_count) as avg_turns,
    SUM(CASE WHEN conversation_outcome = 'solved' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as solve_rate
FROM sessions
WHERE tags IS NOT NULL
GROUP BY tags
ORDER BY count DESC
LIMIT 10;
```

### 飞书多维表格分析

#### 仪表板建议

1. **总览看板**
   - 今日对话数
   - 解决率（solved / total）
   - AI解决率（resolved_by=ai / total）
   - 平均满意度

2. **效果分析**
   - 折线图：每日对话结果趋势
   - 饼图：解决方式分布（AI/人工/自助）
   - 柱状图：标签排名

3. **质量监控**
   - 低满意度对话列表（<3分）
   - 长时间未解决对话
   - 失败对话详情

---

## 🔧 最佳实践

### 1. 标签规范

建议使用统一的标签体系：

**一级分类**：
- `售后` - 售后服务
- `技术支持` - 技术问题
- `价格咨询` - 价格相关
- `产品咨询` - 产品信息

**二级分类**：
- `安装问题` - 安装相关
- `故障排查` - 故障问题
- `功能咨询` - 功能问题
- `维修保养` - 维修相关

**结果标签**：
- `AI解决` - AI成功解决
- `转人工` - 需人工介入
- `待澄清` - 需更多信息
- `失败` - 系统失败

### 2. 满意度评分标准

- **5分**：问题完美解决，用户非常满意
- **4分**：问题基本解决，用户满意
- **3分**：问题部分解决，用户接受
- **2分**：问题未解决，用户不满
- **1分**：体验很差，用户投诉

### 3. 自动评估规则

```python
def auto_evaluate(last_branch, last_status, avg_confidence):
    if last_branch == 'handoff':
        # 转人工 -> transferred
        return ConversationOutcome(
            outcome='transferred',
            resolved_by='human',
            satisfaction_score=3
        )
    
    elif last_status == 'failed':
        # 失败 -> unsolved
        return ConversationOutcome(
            outcome='unsolved',
            resolved_by='unknown',
            satisfaction_score=2
        )
    
    elif last_branch == 'direct_answer' and avg_confidence >= 0.75:
        # 高置信度直答 -> solved
        return ConversationOutcome(
            outcome='solved',
            resolved_by='ai',
            satisfaction_score=4
        )
    
    else:
        # 其他情况 -> unsolved
        return ConversationOutcome(
            outcome='unsolved',
            resolved_by='ai',
            satisfaction_score=3
        )
```

### 4. 定期分析

建议每周/每月分析：

1. **解决率趋势**：是否在提升
2. **AI解决率**：知识库是否需要补充
3. **高频标签**：哪类问题最多
4. **低满意度对话**：找出问题点
5. **长时间对话**：是否需要优化流程

---

## 🎯 总结

### 核心价值

1. **效果可量化**：明确知道每个对话是否解决问题
2. **完整可追溯**：保存完整对话串，方便复盘
3. **数据可分析**：多维表格支持灵活分析
4. **持续优化**：基于数据改进知识库和流程

### 快速开始

```bash
# 1. 升级数据库
sqlite3 data/data.db < sql/upgrade_v3.1.sql

# 2. 在代码中使用
from conversation_tracker import ConversationTracker
tracker = ConversationTracker(db)

# 3. 标记对话结果
outcome = tracker.auto_evaluate_outcome(...)
tracker.mark_outcome(session_key, outcome)

# 4. 同步到多维表格
python sync_to_bitable.py sync-conversations --platform feishu
```

---

**更新时间**：2025-10-16  
**版本**：v3.1

