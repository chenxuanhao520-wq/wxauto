# ERP智能自动同步系统 - 安装使用指南

**版本**: v1.0  
**创建时间**: 2025-10-18

---

## 📋 目录

1. [系统架构](#系统架构)
2. [安装步骤](#安装步骤)
3. [配置说明](#配置说明)
4. [数据库初始化](#数据库初始化)
5. [启动服务](#启动服务)
6. [功能测试](#功能测试)
7. [常见问题](#常见问题)

---

## 系统架构

```
┌─────────────────────────────────────────┐
│         智邦ERP（权威数据源）             │
└──────────────┬──────────────────────────┘
               │
        每小时自动拉取
               │
               ▼
┌─────────────────────────────────────────┐
│       本地融合数据库（中台）               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • ERP客户数据                           │
│  • 微信客户数据                          │
│  • AI提取的补充信息                      │
│  • 规则引擎自动判定                      │
└──────────────┬──────────────────────────┘
               │
        每30分钟自动推送
               │
               ▼
         自动同步到ERP
```

---

## 安装步骤

### 步骤1: 检查Python环境

```bash
python3 --version  # 确保是Python 3.7+
```

### 步骤2: 安装依赖包

```bash
pip3 install requests pyyaml schedule
```

或使用requirements.txt：

```bash
pip3 install -r requirements.txt
```

### 步骤3: 创建必要的目录

```bash
mkdir -p logs
```

---

## 配置说明

### 1. 编辑 config.yaml

在`config.yaml`文件中添加以下配置：

```yaml
# ERP集成配置
erp_integration:
  enabled: true
  base_url: "http://ls1.jmt.ink:46088"
  
  # ERP登录认证
  auth:
    username: "your_username"        # 替换为你的ERP用户名
    password: "your_password"        # 替换为你的ERP密码
    auto_login: true
  
  # ERP拉取配置
  erp_pull:
    enabled: true
    interval: 3600                   # 每小时拉取一次（秒）
    batch_size: 100
    incremental: true                # 增量同步
  
  # ERP推送配置
  erp_push:
    enabled: true
    interval: 1800                   # 每30分钟推送一次（秒）
    batch_size: 50
    auto_sync: true                  # 自动同步（不需要审批）
  
  # 同步规则
  rules:
    mandatory_sync:                  # 强制同步规则
      enabled: true
    
    high_quality_sync:               # 高质量自动同步
      enabled: true
      min_quality_score: 80
    
    medium_quality_sync:             # 中等质量条件同步
      enabled: true
    
    low_quality_skip:                # 低质量跳过
      enabled: true
  
  # 数据质量控制
  data_quality:
    min_score_for_sync: 60           # 最低质量分数
    verify_before_sync: true
    auto_fix_format: true
  
  # 启动时立即执行一次
  run_on_start: false
  
  # 日志配置
  logging:
    level: "INFO"
    file: "logs/erp_sync.log"
```

---

## 数据库初始化

### 1. 运行数据库升级脚本

```bash
sqlite3 storage/customer_manager.db < sql/upgrade_erp_integration.sql
```

或使用Python：

```python
import sqlite3

conn = sqlite3.connect('storage/customer_manager.db')

with open('sql/upgrade_erp_integration.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()
    conn.executescript(sql_script)

conn.close()
print("✅ 数据库升级完成")
```

### 2. 验证数据库表

```bash
sqlite3 storage/customer_manager.db "SELECT name FROM sqlite_master WHERE type='table';"
```

应该看到以下表：
- `customers_unified` - 统一客户表
- `erp_sync_logs` - 同步日志表
- `field_change_history` - 字段变更历史
- `erp_sync_config` - 同步配置
- `erp_sync_rules` - 同步规则
- `erp_api_logs` - API调用日志

---

## 启动服务

### 方式1: 直接运行Python脚本

```bash
python3 start_erp_sync.py
```

### 方式2: 后台运行（推荐）

```bash
nohup python3 start_erp_sync.py > logs/erp_sync_output.log 2>&1 &
```

查看运行状态：

```bash
ps aux | grep start_erp_sync
```

停止服务：

```bash
pkill -f start_erp_sync.py
```

### 方式3: 使用systemd（生产环境推荐）

创建服务文件 `/etc/systemd/system/erp-sync.service`：

```ini
[Unit]
Description=ERP智能自动同步服务
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/wxauto-1
ExecStart=/usr/bin/python3 /path/to/wxauto-1/start_erp_sync.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start erp-sync
sudo systemctl enable erp-sync  # 开机自启
sudo systemctl status erp-sync  # 查看状态
```

---

## 功能测试

### 1. 运行测试脚本

```bash
python3 test_erp_sync.py
```

测试内容：
- ✅ ERP登录测试
- ✅ 获取客户列表测试
- ✅ 规则引擎测试
- ✅ 变更检测器测试
- ✅ 完整同步流程测试

### 2. 查看日志

```bash
tail -f logs/erp_sync.log
```

### 3. 查询同步状态

```sql
-- 查看待同步客户
SELECT * FROM v_pending_sync_customers LIMIT 10;

-- 查看同步日志
SELECT * FROM erp_sync_logs ORDER BY synced_at DESC LIMIT 20;

-- 查看同步统计
SELECT * FROM v_sync_statistics;

-- 查看配置
SELECT * FROM erp_sync_config;
```

---

## 常见问题

### Q1: ERP登录失败？

**A:** 检查以下项：
1. config.yaml中的用户名密码是否正确
2. ERP服务器地址是否可访问：`ping ls1.jmt.ink`
3. 端口是否开放：`telnet ls1.jmt.ink 46088`

### Q2: 客户没有自动同步到ERP？

**A:** 检查客户是否满足同步规则：

```python
# 在Python中测试
from erp_sync.rule_engine import SyncRuleEngine

rule_engine = SyncRuleEngine()

# 模拟客户数据
customer = {
    'phone': '13800138000',
    'company_name': '测试公司',
    'intent_score': 50
}

evaluation = rule_engine.evaluate(customer)
print(f"同步动作: {evaluation['action']}")
print(f"原因: {evaluation['reason']}")
```

### Q3: 如何手动触发同步？

**A:** 

```python
from erp_sync.scheduler import ERPSyncScheduler

# 假设scheduler已启动
scheduler.trigger_sync_now(direction='both')  # both/pull/push
```

或直接修改数据库：

```sql
-- 将客户标记为pending，下次会自动同步
UPDATE customers_unified
SET erp_sync_status = 'pending'
WHERE id = 123;
```

### Q4: 如何调整同步规则？

**A:** 修改数据库中的规则表：

```sql
-- 查看当前规则
SELECT * FROM erp_sync_rules WHERE is_active = 1;

-- 禁用某个规则
UPDATE erp_sync_rules
SET is_active = 0
WHERE rule_name = 'low_intent';

-- 修改高质量分数阈值
UPDATE erp_sync_config
SET config_value = '70'
WHERE config_key = 'min_quality_score';
```

然后重新加载规则：

```python
from erp_sync.rule_engine import SyncRuleEngine

rule_engine = SyncRuleEngine()
rule_engine.reload_rules()  # 重新加载规则
```

### Q5: 同步太频繁或太慢？

**A:** 调整config.yaml中的间隔时间：

```yaml
erp_pull:
  interval: 7200  # 改为2小时

erp_push:
  interval: 3600  # 改为1小时
```

### Q6: 如何查看哪些字段发生了变更？

**A:** 查询变更历史表：

```sql
SELECT 
    c.company_name,
    fch.field_name,
    fch.old_value,
    fch.new_value,
    fch.value_source,
    fch.changed_at
FROM field_change_history fch
JOIN customers_unified c ON fch.customer_id = c.id
WHERE c.id = 123
ORDER BY fch.changed_at DESC;
```

### Q7: 数据冲突如何处理？

**A:** 系统自动处理冲突，策略如下：

1. **核心字段（手机、公司名）**: ERP优先（除非本地已验证）
2. **补充字段（微信信息）**: 本地优先
3. **其他字段**: 最新的优先

可以查看冲突处理日志：

```sql
SELECT * FROM field_change_history
WHERE change_reason LIKE '%冲突%'
ORDER BY changed_at DESC;
```

### Q8: 如何暂停同步？

**A:** 

方式1: 修改配置（临时）

```yaml
erp_integration:
  enabled: false
```

方式2: 停止服务

```bash
pkill -f start_erp_sync.py
```

---

## 性能优化

### 1. 批量大小调整

```yaml
erp_pull:
  batch_size: 200  # 增大批量，减少请求次数

erp_push:
  batch_size: 100  # 根据ERP性能调整
```

### 2. 数据库索引

已自动创建索引，如需额外优化：

```sql
CREATE INDEX IF NOT EXISTS idx_customers_quality_intent 
ON customers_unified(data_quality_score, intent_score);
```

### 3. 日志清理

定期清理旧日志：

```sql
-- 删除30天前的同步日志
DELETE FROM erp_sync_logs
WHERE synced_at < datetime('now', '-30 days');

-- 删除90天前的变更历史
DELETE FROM field_change_history
WHERE changed_at < datetime('now', '-90 days');
```

---

## 监控和维护

### 1. 每日健康检查

```sql
-- 今日同步统计
SELECT 
    sync_direction,
    sync_result,
    COUNT(*) as count
FROM erp_sync_logs
WHERE DATE(synced_at) = DATE('now')
GROUP BY sync_direction, sync_result;

-- 失败的同步
SELECT * FROM erp_sync_logs
WHERE sync_result = 'failed'
  AND DATE(synced_at) = DATE('now');
```

### 2. 设置告警

可以添加告警脚本：

```bash
#!/bin/bash
# check_erp_sync.sh

# 检查是否有失败的同步
failed_count=$(sqlite3 storage/customer_manager.db \
  "SELECT COUNT(*) FROM erp_sync_logs \
   WHERE sync_result='failed' AND synced_at > datetime('now', '-1 hour')")

if [ $failed_count -gt 10 ]; then
    echo "警告：最近1小时有${failed_count}个同步失败！"
    # 发送邮件或钉钉通知
fi
```

---

## 总结

✅ **已完成的功能**：
- ERP客户数据双向同步
- 智能规则引擎自动判定
- 变更检测和冲突处理
- 定时任务自动调度
- 完整的日志和监控

✅ **核心优势**：
- **无需人工审批** - 规则自动判定
- **保证数据质量** - 低质量自动跳过
- **ERP为主** - 权威数据不会被覆盖
- **本地融合** - 微信信息自动补充

需要帮助请查看日志：`logs/erp_sync.log`

