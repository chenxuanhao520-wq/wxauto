# 🚀 ERP智能自动同步系统

**版本**: v1.0  
**发布日期**: 2025-10-18  
**核心功能**: 微信客服中台 ↔ 智邦国际ERP 双向自动同步

---

## ✨ 核心特性

### 🎯 完全自动化
- ✅ **无需人工审批** - 规则引擎自动判定
- ✅ **定时自动同步** - ERP每小时拉取，每30分钟推送
- ✅ **智能冲突处理** - 自动解决数据冲突

### 🔄 双向同步
- ✅ **ERP → 本地** - 每小时自动拉取客户数据
- ✅ **本地 → ERP** - 符合条件自动推送到ERP
- ✅ **增量同步** - 只同步变更数据，高效节能

### 🛡️ 数据质量保证
- ✅ **严格准入规则** - 低质量数据自动跳过
- ✅ **ERP为主** - 核心数据以ERP为准
- ✅ **本地融合** - 微信信息自动补充

### 📊 完整的可追溯性
- ✅ **同步日志** - 记录每次同步详情
- ✅ **变更历史** - 追踪字段变更记录
- ✅ **API调用日志** - 完整的API交互记录

---

## 📁 项目结构

```
wxauto-1/
├── erp_sync/                      # ERP同步核心模块
│   ├── __init__.py
│   ├── erp_client.py              # ERP API客户端
│   ├── rule_engine.py             # 同步规则引擎
│   ├── change_detector.py         # 变更检测器
│   ├── sync_service.py            # 同步服务（核心业务逻辑）
│   ├── scheduler.py               # 定时任务调度器
│   └── config_manager.py          # 配置管理器
│
├── sql/
│   └── upgrade_erp_integration.sql # 数据库升级脚本
│
├── docs/erp_api/
│   ├── 智邦国际ERP_客户管理API详细文档.md
│   ├── 客户来源字段说明.md
│   ├── 微信中台与ERP集成方案.md
│   ├── ERP数据质量控制方案.md
│   ├── ERP智能自动同步方案.md
│   └── ERP同步安装使用指南.md
│
├── start_erp_sync.py              # 启动脚本
├── test_erp_sync.py               # 测试脚本
└── config.yaml                    # 配置文件（已添加ERP配置）
```

---

## 🚀 快速开始

### 步骤1: 配置ERP凭证

编辑 `config.yaml`：

```yaml
erp_integration:
  enabled: true                      # 启用ERP集成
  auth:
    username: "your_erp_username"    # ⚠️ 填写ERP用户名
    password: "your_erp_password"    # ⚠️ 填写ERP密码
```

### 步骤2: 初始化数据库

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('storage/customer_manager.db')
with open('sql/upgrade_erp_integration.sql', 'r', encoding='utf-8') as f:
    conn.executescript(f.read())
conn.close()
print('✅ 数据库初始化完成')
"
```

### 步骤3: 测试连接

```bash
python3 test_erp_sync.py
```

### 步骤4: 启动服务

```bash
python3 start_erp_sync.py
```

或后台运行：

```bash
nohup python3 start_erp_sync.py > logs/erp_sync_output.log 2>&1 &
```

---

## 🎯 同步规则说明

### ⚡ 强制同步（立即）
客户满足以下任一条件，**立即同步到ERP**：
- ✅ 已下单
- ✅ 已签合同
- ✅ 已付款
- ✅ 销售标记"重要客户"

### 🟢 高质量自动同步（质量分≥80）

```
质量分数 = 
  手机号已验证 (30分) +
  公司名称完整 (30分) +
  营业执照验证 (20分) +
  商业意向≥80分 (20分)
```

### 🟡 中等质量条件同步（满足任一）
- 有手机号 + 明确询价
- 有公司名 + 营业执照
- 持续沟通7天+ & 消息50条+

### 🔴 低质量跳过（不同步）
- 只有微信昵称，无其他信息
- 商业意向＜30分
- 消息数＜5条
- 已标记为无效客户

---

## 📊 数据流向示意

```
┌─────────────────────────────────┐
│   微信客户 "张三"                 │
│   昵称: wx_zhangsan               │
│   信息: 无                        │
└────────────┬────────────────────┘
             │
        【聊天互动】
             │
             ▼
┌─────────────────────────────────┐
│   AI提取信息                      │
│   - 手机: 138****8888             │
│   - 公司: 深圳XX科技              │
│   - 意向: 询价                    │
└────────────┬────────────────────┘
             │
      【质量评分: 85分】
             │
             ▼
┌─────────────────────────────────┐
│   规则引擎判定                    │
│   ✅ 高质量客户                   │
│   ✅ 自动同步到ERP                │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   创建ERP客户                     │
│   客户编号: KH2025001             │
│   客户名称: 深圳XX科技            │
│   手机: 138****8888               │
│   来源: 微信咨询                  │
└────────────┬────────────────────┘
             │
      【回写本地】
             │
             ▼
┌─────────────────────────────────┐
│   微信界面显示                    │
│   "客户编号: KH2025001"           │
│   "已同步到ERP"                   │
└─────────────────────────────────┘
```

---

## 📝 数据库表说明

### 1. customers_unified（统一客户表）
- **用途**: 融合ERP和微信的客户数据
- **关键字段**:
  - `erp_customer_id` - ERP客户ID（权威标识）
  - `wechat_id` - 微信ID
  - `data_quality_score` - 数据质量分数
  - `intent_score` - 商业意向分数
  - `erp_sync_status` - 同步状态

### 2. erp_sync_logs（同步日志表）
- **用途**: 记录每次同步操作
- **字段**: 同步方向、动作、结果、耗时等

### 3. field_change_history（字段变更历史）
- **用途**: 追踪字段值的变化
- **字段**: 字段名、旧值、新值、来源、时间

### 4. erp_sync_rules（同步规则表）
- **用途**: 存储同步规则配置
- **可动态调整**: 通过SQL修改规则

### 5. erp_api_logs（API调用日志）
- **用途**: 记录所有ERP API调用
- **字段**: 端点、参数、响应、耗时

---

## 🔧 常用操作

### 查看待同步客户

```sql
SELECT * FROM v_pending_sync_customers LIMIT 10;
```

### 查看今日同步统计

```sql
SELECT * FROM v_sync_statistics WHERE sync_date = DATE('now');
```

### 手动标记客户需要同步

```sql
UPDATE customers_unified
SET erp_sync_status = 'pending'
WHERE wechat_id = 'wxid_xxx';
```

### 查看同步错误

```sql
SELECT * FROM erp_sync_logs
WHERE sync_result = 'failed'
ORDER BY synced_at DESC
LIMIT 20;
```

### 调整质量分数阈值

```sql
UPDATE erp_sync_config
SET config_value = '70'
WHERE config_key = 'min_quality_score';
```

---

## 📈 监控和维护

### 查看服务状态

```bash
# 查看进程
ps aux | grep start_erp_sync

# 查看日志
tail -f logs/erp_sync.log

# 查看最近的同步
sqlite3 storage/customer_manager.db \
  "SELECT * FROM erp_sync_logs ORDER BY synced_at DESC LIMIT 5;"
```

### 性能监控

```sql
-- 平均同步耗时
SELECT 
    sync_direction,
    AVG(sync_duration_ms) as avg_ms,
    MAX(sync_duration_ms) as max_ms
FROM erp_sync_logs
WHERE synced_at > datetime('now', '-1 day')
GROUP BY sync_direction;

-- ERP API响应时间
SELECT 
    api_endpoint,
    AVG(response_time_ms) as avg_ms,
    COUNT(*) as call_count
FROM erp_api_logs
WHERE called_at > datetime('now', '-1 day')
GROUP BY api_endpoint;
```

---

## 🆘 故障排查

### 问题1: 客户没有同步到ERP

**检查步骤**:
1. 查看客户质量分数：`SELECT data_quality_score, intent_score FROM customers_unified WHERE id=?`
2. 查看同步状态：`SELECT erp_sync_status, erp_sync_error FROM customers_unified WHERE id=?`
3. 查看匹配的规则：`SELECT erp_sync_rule, erp_sync_action FROM customers_unified WHERE id=?`

### 问题2: 同步失败

**查看错误日志**:
```sql
SELECT error_message, error_code
FROM erp_sync_logs
WHERE customer_id = ? AND sync_result = 'failed'
ORDER BY synced_at DESC LIMIT 1;
```

### 问题3: 数据冲突

**查看冲突处理**:
```sql
SELECT field_name, old_value, new_value, value_source, change_reason
FROM field_change_history
WHERE customer_id = ?
ORDER BY changed_at DESC;
```

---

## 📚 相关文档

| 文档 | 描述 |
|------|------|
| [ERP同步安装使用指南](docs/erp_api/ERP同步安装使用指南.md) | 详细的安装和配置指南 |
| [ERP智能自动同步方案](docs/erp_api/ERP智能自动同步方案.md) | 技术方案和设计文档 |
| [智邦国际ERP_客户管理API详细文档](docs/erp_api/智邦国际ERP_客户管理API详细文档.md) | ERP API接口文档 |
| [客户来源字段说明](docs/erp_api/客户来源字段说明.md) | 客户来源字段使用说明 |

---

## 💡 最佳实践

1. **首次使用建议**: 先在测试环境运行，观察同步效果
2. **规则调整**: 根据实际业务调整质量分数阈值
3. **定期清理**: 定期清理90天前的日志数据
4. **监控告警**: 设置同步失败率告警
5. **备份数据**: 定期备份数据库

---

## 🎯 核心优势总结

### ✅ 自动化
- 无需人工干预
- 规则自动判定
- 定时自动执行

### ✅ 高质量
- 低质量数据自动跳过
- ERP数据权威保证
- 完整的验证机制

### ✅ 可追溯
- 完整的同步日志
- 字段变更历史
- API调用记录

### ✅ 高性能
- 增量同步
- 批量处理
- 智能调度

---

## 📞 技术支持

如有问题，请查看：
1. 日志文件：`logs/erp_sync.log`
2. 测试脚本：`python3 test_erp_sync.py`
3. 文档目录：`docs/erp_api/`

---

**开发完成日期**: 2025-10-18  
**系统版本**: v1.0  
**维护状态**: ✅ 已完成，可投入生产使用

