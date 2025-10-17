# 多维表格集成指南

本文档介绍如何将客服系统的消息日志同步到飞书和钉钉多维表格，实现数据可视化和分析。

---

## 📊 功能概述

### 支持的平台

- ✅ **飞书多维表格（Bitable）**
- ✅ **钉钉多维表格（智能表格）**

### 主要功能

1. **自动同步**：将消息日志自动同步到多维表格
2. **批量写入**：支持批量操作，提升效率
3. **字段映射**：自动转换数据格式，适配表格结构
4. **定时同步**：可配置定时任务，定期同步数据

---

## 🚀 快速开始

### 1. 飞书多维表格配置

#### 步骤 1：创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 创建企业自建应用
3. 获取 **App ID** 和 **App Secret**
4. 开通权限：
   - `bitable:app` - 多维表格应用权限
   - `bitable:app:readonly` - 读取多维表格
   - 根据需要添加其他权限

#### 步骤 2：创建多维表格

1. 在飞书中创建多维表格
2. 创建数据表，包含以下字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 请求ID | 文本 | 唯一标识 |
| 会话ID | 数字 | 会话标识 |
| 群名称 | 文本 | 群聊名称 |
| 发送者 | 文本 | 用户昵称 |
| 用户消息 | 文本 | 用户问题 |
| AI回复 | 文本 | AI回答 |
| 置信度 | 数字 | 0-1 |
| 分支 | 文本 | 分流类型 |
| AI提供商 | 文本 | openai/deepseek等 |
| 模型 | 文本 | 模型名称 |
| Token总数 | 数字 | Token消耗 |
| 总时延(ms) | 数字 | 响应时延 |
| 状态 | 文本 | answered/failed等 |
| 接收时间 | 日期 | 接收时间戳 |
| 响应时间 | 日期 | 响应时间戳 |

3. 获取表格信息：
   - 打开表格，URL 格式：`https://xxx.feishu.cn/base/[bitable_token]?table=[table_id]`
   - 记录 `bitable_token` 和 `table_id`

#### 步骤 3：配置环境变量

```bash
# 飞书配置
export FEISHU_APP_ID=cli_xxxxxxxxxxxxx
export FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export FEISHU_BITABLE_TOKEN=bascnxxxxxxxxxxxxx
export FEISHU_TABLE_ID=tblxxxxxxxxxxxxx
```

#### 步骤 4：测试连接

```bash
# 测试飞书连接
python sync_to_bitable.py test --platform feishu
```

**预期输出**：
```
✅ Access Token 获取成功
✅ 测试记录写入成功
```

#### 步骤 5：同步数据

```bash
# 同步最近 7 天数据
python sync_to_bitable.py sync --platform feishu --days 7

# 或者
python sync_to_bitable.py sync --platform feishu --db data/data.db --days 30
```

---

### 2. 钉钉多维表格配置

#### 步骤 1：创建钉钉应用

1. 访问 [钉钉开放平台](https://open-dev.dingtalk.com/)
2. 创建企业内部应用
3. 获取 **App Key** 和 **App Secret**
4. 开通权限：
   - 智能表格权限
   - 根据需要添加其他权限

#### 步骤 2：创建智能表格

1. 在钉钉工作台创建智能表格（多维表格）
2. 创建数据表，字段结构同飞书
3. 获取表格信息：
   - Base ID：表格的唯一标识
   - Table ID：数据表的唯一标识

#### 步骤 3：配置环境变量

```bash
# 钉钉配置
export DINGTALK_APP_KEY=dingtalkxxxxxxxxxxxxx
export DINGTALK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export DINGTALK_BASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export DINGTALK_TABLE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### 步骤 4：测试连接

```bash
# 测试钉钉连接
python sync_to_bitable.py test --platform dingtalk
```

#### 步骤 5：同步数据

```bash
# 同步最近 7 天数据
python sync_to_bitable.py sync --platform dingtalk --days 7
```

---

## 🔧 使用方法

### 命令行工具

`sync_to_bitable.py` 是多维表格同步工具，支持以下操作：

#### 测试连接

```bash
# 测试飞书
python sync_to_bitable.py test --platform feishu

# 测试钉钉
python sync_to_bitable.py test --platform dingtalk

# 测试两个平台
python sync_to_bitable.py test --platform both
```

#### 同步数据

```bash
# 同步到飞书（最近 7 天）
python sync_to_bitable.py sync --platform feishu --days 7

# 同步到钉钉（最近 30 天）
python sync_to_bitable.py sync --platform dingtalk --days 30

# 同步到两个平台
python sync_to_bitable.py sync --platform both --days 7

# 指定数据库路径
python sync_to_bitable.py sync --db /path/to/data.db --days 7
```

### 编程方式

#### 飞书同步示例

```python
from integrations import FeishuBitable
from datetime import datetime, timedelta

# 初始化
feishu = FeishuBitable(
    app_id="cli_xxxxxxxxxxxxx",
    app_secret="xxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    bitable_token="bascnxxxxxxxxxxxxx",
    table_id="tblxxxxxxxxxxxxx"
)

# 添加单条记录
record = {
    'request_id': 'req_123',
    'group_name': '技术支持群',
    'sender_name': '张三',
    'user_message': '如何安装设备？',
    'bot_response': '请参考安装手册...',
    'status': 'answered',
    'received_at': datetime.now()
}

feishu.add_record(record)

# 批量添加
records = [record1, record2, record3]
feishu.add_records(records)

# 从数据库同步（最近 7 天）
since = datetime.now() - timedelta(days=7)
count = feishu.sync_from_database('data/data.db', since=since)
print(f"同步了 {count} 条记录")
```

#### 钉钉同步示例

```python
from integrations import DingtalkBitable

# 初始化
dingtalk = DingtalkBitable(
    app_key="dingtalkxxxxxxxxxxxxx",
    app_secret="xxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    base_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    table_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
)

# 使用方法同飞书
dingtalk.add_record(record)
dingtalk.add_records(records)
dingtalk.sync_from_database('data/data.db', since=since)
```

---

## ⚙️ 定时同步

### Linux/Mac 定时任务（Cron）

```bash
# 编辑 crontab
crontab -e

# 每天凌晨 2 点同步数据到飞书
0 2 * * * cd /path/to/project && python sync_to_bitable.py sync --platform feishu --days 1

# 每小时同步到钉钉
0 * * * * cd /path/to/project && python sync_to_bitable.py sync --platform dingtalk --days 1
```

### Windows 定时任务

使用 Windows 任务计划程序：

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器（如每天凌晨 2 点）
4. 操作：启动程序
   - 程序：`python`
   - 参数：`sync_to_bitable.py sync --platform both --days 1`
   - 起始于：项目目录

---

## 📊 数据分析示例

### 飞书多维表格分析

同步数据后，你可以在飞书中：

1. **创建视图**
   - 按日期分组统计
   - 按AI提供商分析成本
   - 按分支类型分析质量

2. **创建图表**
   - 每日消息量趋势
   - AI回答置信度分布
   - Token消耗统计
   - 响应时延分析

3. **创建仪表板**
   - 实时监控消息处理情况
   - AI性能指标
   - 成本分析

### 钉钉智能表格分析

1. **数据透视表**
   - 按群聊分组统计
   - 按用户分析活跃度
   - 按时间段分析高峰

2. **图表可视化**
   - 柱状图：每日消息量
   - 折线图：置信度趋势
   - 饼图：分支分布

---

## 🐛 常见问题

### Q1: Access Token 获取失败

**原因**：App ID 或 App Secret 错误

**解决**：
1. 检查环境变量是否正确设置
2. 确认应用权限已开通
3. 查看应用是否已启用

### Q2: 记录写入失败

**原因**：字段不匹配或权限不足

**解决**：
1. 确认表格字段名称与代码中的映射一致
2. 检查应用是否有表格写入权限
3. 查看表格是否设置了写入限制

### Q3: 同步速度慢

**原因**：批量写入数量过大

**解决**：
1. 调整同步天数，减少单次同步量
2. 分批同步，每次同步一部分数据
3. 使用定时任务，定期增量同步

### Q4: 时间显示异常

**原因**：时区问题

**解决**：
- 飞书和钉钉使用毫秒时间戳
- 代码已自动转换，如有问题请检查数据库时间格式

---

## 📚 API 参考

### FeishuBitable 类

```python
class FeishuBitable:
    def __init__(self, app_id, app_secret, bitable_token, table_id)
    def is_configured(self) -> bool
    def add_record(self, record: Dict) -> bool
    def add_records(self, records: List[Dict]) -> bool
    def sync_from_database(self, db_path: str, since: datetime) -> int
```

### DingtalkBitable 类

```python
class DingtalkBitable:
    def __init__(self, app_key, app_secret, base_id, table_id)
    def is_configured(self) -> bool
    def add_record(self, record: Dict) -> bool
    def add_records(self, records: List[Dict]) -> bool
    def sync_from_database(self, db_path: str, since: datetime) -> int
```

---

## 🔐 安全建议

1. **密钥管理**
   - 不要将密钥提交到代码仓库
   - 使用环境变量或密钥管理服务
   - 定期轮换密钥

2. **权限控制**
   - 仅授予必要的权限
   - 使用独立应用，避免权限过大
   - 定期审计权限使用

3. **数据安全**
   - 同步的数据包含用户信息，注意保护隐私
   - 设置表格访问权限
   - 考虑数据脱敏

---

## 📞 技术支持

如遇问题：

1. 查看日志文件 `logs/app.log`
2. 运行测试命令检查配置
3. 参考官方文档：
   - [飞书开放平台](https://open.feishu.cn/document)
   - [钉钉开放平台](https://open.dingtalk.com/document)

---

**最后更新**：2025-10-16

