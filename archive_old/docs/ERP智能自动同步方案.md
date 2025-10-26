# ERP智能自动同步方案

**版本**: v3.0  
**更新时间**: 2025-10-18  
**核心理念**: ERP为主，本地融合，智能判定，自动同步

---

## 📋 目录

1. [设计思路](#设计思路)
2. [数据流向](#数据流向)
3. [智能判定规则](#智能判定规则)
4. [自动同步机制](#自动同步机制)
5. [冲突处理策略](#冲突处理策略)
6. [实施方案](#实施方案)

---

## 设计思路

### 核心原则

```
1. ERP是唯一权威数据源（Single Source of Truth）
2. 本地数据库作为融合层（Data Fusion Layer）
3. 微信信息作为补充源（Supplementary Source）
4. 自动规则判定变更（Rule-based Auto Sync）
5. 双向同步，但有优先级（Bidirectional with Priority）
```

### 架构图

```
┌─────────────────────────────────────────────────────┐
│              智邦ERP（权威数据源）                      │
│  • 客户主档案                                         │
│  • 客户编号（唯一标识）                                │
│  • 公司信息、联系人、跟进记录                          │
└──────────────────┬──────────────────────────────────┘
                   │
        【定时拉取】 │ 【智能推送】
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│          本地融合数据库（中台）                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  ERP数据 + 微信数据 = 融合数据                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • 客户基础信息（来自ERP）                             │
│  • 微信账号映射（本地维护）                            │
│  • 聊天记录（本地采集）                                │
│  • 补充字段（AI提取）                                  │
│  • 变更检测（Diff Engine）                            │
└──────────────────┬──────────────────────────────────┘
                   │
        【实时监听】 │ 【增量采集】
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│            微信客服（信息补充源）                        │
│  • 聊天内容                                           │
│  • 客户主动提供的信息                                  │
│  • AI提取的结构化数据                                  │
└─────────────────────────────────────────────────────┘
```

---

## 数据流向

### 流程1: ERP → 本地（定时拉取）

```python
# 每小时执行一次
def sync_from_erp():
    """从ERP拉取客户数据到本地"""
    
    # 1. 获取ERP所有客户（增量）
    erp_customers = erp_api.get_customers(
        updated_after=last_sync_time  # 只拉取有更新的
    )
    
    # 2. 更新本地数据库
    for erp_customer in erp_customers:
        local_customer = db.get_customer_by_erp_id(erp_customer['ord'])
        
        if local_customer:
            # 存在：更新ERP字段
            db.update_customer_erp_fields(
                local_id=local_customer.id,
                erp_data=erp_customer,
                sync_time=datetime.now()
            )
        else:
            # 不存在：创建新记录
            db.create_customer_from_erp(
                erp_data=erp_customer,
                source='erp_pull'
            )
    
    # 3. 记录同步时间
    db.update_sync_timestamp('erp_to_local', datetime.now())
```

### 流程2: 微信 → 本地（实时采集）

```python
# 微信消息回调
def on_wechat_message(message):
    """处理微信消息，提取并融合信息"""
    
    wechat_id = message['sender']
    content = message['content']
    
    # 1. 查找或创建本地记录
    customer = db.get_customer_by_wechat_id(wechat_id)
    if not customer:
        customer = db.create_customer_from_wechat({
            'wechat_id': wechat_id,
            'nickname': message['sender_name'],
            'source': 'wechat'
        })
    
    # 2. AI提取信息
    extracted_info = ai_extract_customer_info(content)
    
    # 3. 融合到本地记录（只更新微信字段）
    if extracted_info:
        db.merge_wechat_info(
            customer_id=customer.id,
            extracted_info=extracted_info,
            confidence=extracted_info['confidence']
        )
    
    # 4. 检查是否满足同步条件
    if should_sync_to_erp(customer):
        # 触发自动同步到ERP
        auto_sync_to_erp(customer)
```

### 流程3: 本地 → ERP（智能推送）

```python
def auto_sync_to_erp(customer):
    """智能判定后自动同步到ERP"""
    
    # 1. 判定同步类型
    sync_action = determine_sync_action(customer)
    
    if sync_action == 'CREATE':
        # 在ERP中创建新客户
        erp_customer_id = erp_api.create_customer({
            'name': customer.company_name or customer.real_name,
            'person_name': customer.real_name,
            'mobile': customer.phone,
            'weixinAcc': customer.wechat_id,
            'ly': get_source_enum('微信咨询'),
            # ... 其他字段
        })
        
        # 回写ERP ID到本地
        db.update_customer_erp_id(customer.id, erp_customer_id)
        
    elif sync_action == 'UPDATE':
        # 更新ERP客户信息
        changed_fields = get_changed_fields(customer)
        erp_api.update_customer(
            customer_id=customer.erp_customer_id,
            updates=changed_fields
        )
        
    elif sync_action == 'SKIP':
        # 不同步（信息不足或低质量）
        pass
    
    # 2. 记录同步日志
    db.log_sync_action(customer.id, sync_action, datetime.now())
```

---

## 智能判定规则

### 规则引擎架构

```python
class SyncRuleEngine:
    """同步规则引擎 - 自动判定是否同步及同步方式"""
    
    def __init__(self):
        self.rules = [
            # 规则优先级从高到低
            MandatorySyncRule(),      # 强制同步规则
            HighQualitySyncRule(),    # 高质量自动同步
            MediumQualitySyncRule(),  # 中等质量条件同步
            LowQualitySkipRule(),     # 低质量跳过
        ]
    
    def evaluate(self, customer):
        """
        评估客户是否应该同步到ERP
        
        Returns:
            {
                'action': 'CREATE'/'UPDATE'/'SKIP',
                'confidence': float,
                'reason': str,
                'matched_rule': str
            }
        """
        for rule in self.rules:
            result = rule.match(customer)
            if result['matched']:
                return {
                    'action': result['action'],
                    'confidence': result['confidence'],
                    'reason': result['reason'],
                    'matched_rule': rule.__class__.__name__
                }
        
        # 默认：跳过
        return {
            'action': 'SKIP',
            'confidence': 0.0,
            'reason': '未匹配任何规则',
            'matched_rule': 'Default'
        }
```

### 具体规则定义

#### 规则1: 强制同步规则（最高优先级）

```python
class MandatorySyncRule:
    """
    强制同步规则 - 满足任一条件立即同步
    
    适用场景：
    1. 客户已下单
    2. 客户已签合同
    3. 客户已付款
    4. 销售手动标记"重要客户"
    """
    
    def match(self, customer):
        # 检查是否有订单
        if customer.has_order:
            return {
                'matched': True,
                'action': 'CREATE' if not customer.erp_customer_id else 'UPDATE',
                'confidence': 1.0,
                'reason': '客户已下单，必须同步到ERP'
            }
        
        # 检查是否有合同
        if customer.has_contract:
            return {
                'matched': True,
                'action': 'CREATE' if not customer.erp_customer_id else 'UPDATE',
                'confidence': 1.0,
                'reason': '客户已签合同，必须同步到ERP'
            }
        
        # 检查是否已付款
        if customer.has_payment:
            return {
                'matched': True,
                'action': 'CREATE' if not customer.erp_customer_id else 'UPDATE',
                'confidence': 1.0,
                'reason': '客户已付款，必须同步到ERP'
            }
        
        # 检查是否手动标记
        if customer.marked_as_important:
            return {
                'matched': True,
                'action': 'CREATE' if not customer.erp_customer_id else 'UPDATE',
                'confidence': 1.0,
                'reason': '销售标记为重要客户'
            }
        
        return {'matched': False}
```

#### 规则2: 高质量自动同步

```python
class HighQualitySyncRule:
    """
    高质量自动同步规则
    
    必须同时满足：
    1. 手机号已验证
    2. 公司名称完整（非微信昵称）
    3. 商业意向≥80分
    """
    
    def match(self, customer):
        # 计算数据质量分数
        quality_score = self._calculate_quality_score(customer)
        
        # 高质量：≥80分
        if quality_score >= 80:
            return {
                'matched': True,
                'action': 'CREATE' if not customer.erp_customer_id else 'UPDATE',
                'confidence': quality_score / 100,
                'reason': f'高质量客户（{quality_score}分），自动同步'
            }
        
        return {'matched': False}
    
    def _calculate_quality_score(self, customer):
        """计算数据质量分数"""
        score = 0
        
        # 1. 手机号（30分）
        if customer.phone and customer.phone_verified:
            score += 30
        elif customer.phone:
            score += 15
        
        # 2. 公司名称（30分）
        if customer.company_name and len(customer.company_name) >= 4:
            if not any(kw in customer.company_name for kw in ['先生', '女士', '老板']):
                score += 30
        
        # 3. 营业执照（20分）
        if customer.business_license_verified:
            score += 20
        
        # 4. 商业意向（20分）
        if customer.intent_score >= 80:
            score += 20
        elif customer.intent_score >= 60:
            score += 15
        elif customer.intent_score >= 40:
            score += 10
        
        return score
```

#### 规则3: 中等质量条件同步

```python
class MediumQualitySyncRule:
    """
    中等质量条件同步
    
    满足以下任一组合：
    1. 手机号 + 明确询价
    2. 公司名 + 营业执照
    3. 持续沟通7天+ & 消息50条+
    """
    
    def match(self, customer):
        # 组合1: 手机号 + 明确询价
        if customer.phone and customer.has_quote_request:
            return {
                'matched': True,
                'action': 'CREATE' if not customer.erp_customer_id else 'UPDATE',
                'confidence': 0.75,
                'reason': '有手机号且明确询价'
            }
        
        # 组合2: 公司名 + 营业执照
        if customer.company_name and customer.business_license_uploaded:
            return {
                'matched': True,
                'action': 'CREATE' if not customer.erp_customer_id else 'UPDATE',
                'confidence': 0.8,
                'reason': '公司信息完整'
            }
        
        # 组合3: 持续深度沟通
        if (customer.conversation_days >= 7 and 
            customer.message_count >= 50):
            return {
                'matched': True,
                'action': 'CREATE' if not customer.erp_customer_id else 'UPDATE',
                'confidence': 0.7,
                'reason': '持续深度沟通，客户意向明确'
            }
        
        return {'matched': False}
```

#### 规则4: 低质量跳过

```python
class LowQualitySkipRule:
    """
    低质量跳过规则
    
    满足任一条件则不同步：
    1. 只有微信昵称，无其他信息
    2. 商业意向＜30分
    3. 消息数＜5条
    4. 被标记为"无效客户"
    """
    
    def match(self, customer):
        # 无基本信息
        if (not customer.phone and 
            not customer.company_name and 
            not customer.real_name):
            return {
                'matched': True,
                'action': 'SKIP',
                'confidence': 0.0,
                'reason': '信息不足，暂不同步'
            }
        
        # 意向过低
        if customer.intent_score < 30:
            return {
                'matched': True,
                'action': 'SKIP',
                'confidence': 0.0,
                'reason': '商业意向过低'
            }
        
        # 互动太少
        if customer.message_count < 5:
            return {
                'matched': True,
                'action': 'SKIP',
                'confidence': 0.0,
                'reason': '互动次数不足'
            }
        
        # 标记为无效
        if customer.marked_as_invalid:
            return {
                'matched': True,
                'action': 'SKIP',
                'confidence': 0.0,
                'reason': '已标记为无效客户'
            }
        
        return {'matched': False}
```

---

## 自动同步机制

### 同步时机

```yaml
sync_triggers:
  # 触发方式1: 定时同步
  scheduled:
    enabled: true
    intervals:
      - type: 'erp_to_local'
        cron: '0 */1 * * *'    # 每小时从ERP拉取
      - type: 'local_to_erp'
        cron: '*/30 * * * *'   # 每30分钟推送到ERP
  
  # 触发方式2: 事件触发
  event_driven:
    enabled: true
    events:
      - event: 'customer_info_updated'    # 客户信息更新
        action: 'evaluate_and_sync'
      - event: 'phone_verified'           # 手机号验证通过
        action: 'auto_sync'
      - event: 'license_uploaded'         # 营业执照上传
        action: 'auto_sync'
      - event: 'quote_requested'          # 客户询价
        action: 'auto_sync'
  
  # 触发方式3: 规则触发
  rule_based:
    enabled: true
    check_interval: 300  # 每5分钟检查一次
    batch_size: 50       # 每批处理50个
```

### 变更检测机制

```python
class ChangeDetector:
    """变更检测器 - 检测哪些字段发生了变化"""
    
    # 字段优先级定义
    FIELD_PRIORITY = {
        'phone': 10,              # 手机号最重要
        'company_name': 9,
        'real_name': 8,
        'email': 7,
        'business_license': 6,
        'address': 5,
        'wechat_id': 4,
        'nickname': 1,            # 微信昵称优先级最低
    }
    
    def detect_changes(self, erp_data, local_data):
        """
        检测ERP数据和本地数据的差异
        
        Returns:
            {
                'has_changes': bool,
                'changes': [
                    {
                        'field': str,
                        'erp_value': any,
                        'local_value': any,
                        'priority': int,
                        'action': 'take_erp'/'take_local'/'merge'
                    }
                ]
            }
        """
        changes = []
        
        for field in self.FIELD_PRIORITY.keys():
            erp_value = erp_data.get(field)
            local_value = local_data.get(field)
            
            if erp_value != local_value:
                # 决定采用哪个值
                action = self._decide_value_source(
                    field, erp_value, local_value
                )
                
                changes.append({
                    'field': field,
                    'erp_value': erp_value,
                    'local_value': local_value,
                    'priority': self.FIELD_PRIORITY[field],
                    'action': action
                })
        
        return {
            'has_changes': len(changes) > 0,
            'changes': sorted(changes, key=lambda x: x['priority'], reverse=True)
        }
    
    def _decide_value_source(self, field, erp_value, local_value):
        """
        决定采用哪个数据源的值
        
        优先级规则：
        1. 如果ERP有值，本地没有 → take_erp
        2. 如果本地有值，ERP没有 → take_local（推送到ERP）
        3. 如果都有值但不同 → 根据字段类型和时间戳决定
        """
        if not erp_value and local_value:
            # ERP空，本地有 → 推送到ERP
            return 'take_local'
        
        if erp_value and not local_value:
            # ERP有，本地空 → 从ERP拉取
            return 'take_erp'
        
        if erp_value and local_value:
            # 都有值但不同 → 看字段类型
            if field in ['phone', 'company_name', 'real_name']:
                # 核心字段：以ERP为准（除非本地有验证标记）
                if hasattr(local_value, 'verified') and local_value.verified:
                    return 'take_local'  # 本地已验证，推送到ERP
                else:
                    return 'take_erp'    # 以ERP为准
            else:
                # 次要字段：以最新的为准
                return 'merge'
        
        return 'skip'
```

### 冲突解决策略

```python
class ConflictResolver:
    """冲突解决器"""
    
    def resolve(self, changes):
        """
        解决数据冲突
        
        策略：
        1. 核心字段以ERP为准（手机、公司名）
        2. 补充字段优先本地（微信号、聊天记录）
        3. 可验证字段优先已验证的
        4. 时间戳较新的优先
        """
        resolved = {}
        
        for change in changes:
            field = change['field']
            erp_value = change['erp_value']
            local_value = change['local_value']
            action = change['action']
            
            if action == 'take_erp':
                resolved[field] = {
                    'value': erp_value,
                    'source': 'erp',
                    'sync_direction': 'erp_to_local'
                }
            
            elif action == 'take_local':
                resolved[field] = {
                    'value': local_value,
                    'source': 'local',
                    'sync_direction': 'local_to_erp'
                }
            
            elif action == 'merge':
                # 合并策略：保留两者，标记来源
                resolved[field] = {
                    'erp_value': erp_value,
                    'local_value': local_value,
                    'merged': True,
                    'sync_direction': 'none'  # 需要人工决策
                }
        
        return resolved
```

---

## 实施方案

### 数据库设计

```sql
-- 融合客户表
CREATE TABLE customers_unified (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 唯一标识
    erp_customer_id INTEGER UNIQUE,           -- ERP客户ID（权威）
    erp_customer_code VARCHAR(50),            -- ERP客户编号
    wechat_id VARCHAR(100) UNIQUE,            -- 微信ID
    
    -- 基础信息（多源融合）
    company_name VARCHAR(200),                -- 公司名称
    company_name_source VARCHAR(20),          -- 来源：erp/wechat/ai
    company_name_verified BOOLEAN DEFAULT 0,
    
    real_name VARCHAR(100),                   -- 真实姓名
    real_name_source VARCHAR(20),
    
    phone VARCHAR(20),                        -- 手机号
    phone_source VARCHAR(20),
    phone_verified BOOLEAN DEFAULT 0,
    phone_verified_time DATETIME,
    
    email VARCHAR(100),
    email_source VARCHAR(20),
    
    -- 微信特有字段
    wechat_nickname VARCHAR(200),             -- 微信昵称
    wechat_avatar VARCHAR(500),               -- 微信头像
    
    -- ERP特有字段
    erp_customer_type INTEGER,                -- 1=单位 2=个人
    erp_follow_level VARCHAR(50),             -- 跟进程度
    erp_value_assessment VARCHAR(50),         -- 价值评估
    
    -- 补充字段（AI提取）
    extracted_company_info TEXT,              -- JSON：从聊天提取的公司信息
    extracted_product_interest TEXT,          -- JSON：感兴趣的产品
    business_license_info TEXT,               -- JSON：营业执照信息
    
    -- 商业意向
    intent_score FLOAT DEFAULT 0,
    intent_level VARCHAR(20),
    intent_signals TEXT,
    
    -- 同步状态
    erp_sync_status VARCHAR(20),              -- synced/pending/failed
    erp_last_pulled DATETIME,                 -- 最后从ERP拉取时间
    erp_last_pushed DATETIME,                 -- 最后推送到ERP时间
    
    local_updated_at DATETIME,                -- 本地最后更新时间
    erp_updated_at DATETIME,                  -- ERP最后更新时间
    
    -- 质量评分
    data_quality_score FLOAT DEFAULT 0,       -- 数据质量分数
    data_completeness FLOAT DEFAULT 0,        -- 数据完整度
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_erp_customer_id (erp_customer_id),
    INDEX idx_wechat_id (wechat_id),
    INDEX idx_erp_sync_status (erp_sync_status)
);

-- 同步日志表
CREATE TABLE sync_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    customer_id INTEGER NOT NULL,
    sync_direction VARCHAR(20),               -- erp_to_local/local_to_erp
    sync_type VARCHAR(20),                    -- pull/push/merge
    
    -- 同步详情
    changed_fields TEXT,                      -- JSON：变更的字段
    sync_action VARCHAR(20),                  -- create/update/skip
    sync_result VARCHAR(20),                  -- success/failed
    
    -- 规则信息
    matched_rule VARCHAR(100),                -- 匹配的规则
    rule_confidence FLOAT,                    -- 规则置信度
    
    -- 错误信息
    error_message TEXT,
    error_code VARCHAR(50),
    
    -- 性能指标
    sync_duration_ms INTEGER,                 -- 同步耗时（毫秒）
    
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers_unified(id)
);

-- 字段变更历史表
CREATE TABLE field_change_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    customer_id INTEGER NOT NULL,
    field_name VARCHAR(100),
    
    old_value TEXT,
    new_value TEXT,
    value_source VARCHAR(20),                 -- erp/wechat/ai/manual
    
    changed_by VARCHAR(100),                  -- 变更者（system/user_id）
    change_reason TEXT,                       -- 变更原因
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (customer_id) REFERENCES customers_unified(id),
    INDEX idx_customer_field (customer_id, field_name)
);
```

### 核心服务实现

```python
class UnifiedCustomerSyncService:
    """统一客户同步服务"""
    
    def __init__(self, erp_api, rule_engine, change_detector):
        self.erp_api = erp_api
        self.rule_engine = rule_engine
        self.change_detector = change_detector
    
    def sync_from_erp(self):
        """从ERP拉取客户数据"""
        print("[同步] 开始从ERP拉取客户数据...")
        
        # 1. 获取最后同步时间
        last_sync = self._get_last_sync_time('erp_to_local')
        
        # 2. 拉取增量数据
        erp_customers = self.erp_api.get_customers(
            updated_after=last_sync,
            page_size=100
        )
        
        synced_count = 0
        updated_count = 0
        created_count = 0
        
        for erp_customer in erp_customers:
            # 3. 查找本地记录
            local_customer = self._find_local_customer(
                erp_id=erp_customer['ord'],
                phone=erp_customer.get('mobile')
            )
            
            if local_customer:
                # 存在：检测变更并融合
                changes = self.change_detector.detect_changes(
                    erp_data=erp_customer,
                    local_data=local_customer
                )
                
                if changes['has_changes']:
                    self._merge_changes(local_customer.id, changes)
                    updated_count += 1
            else:
                # 不存在：创建新记录
                self._create_from_erp(erp_customer)
                created_count += 1
            
            synced_count += 1
        
        # 4. 更新同步时间戳
        self._update_sync_timestamp('erp_to_local')
        
        print(f"[同步完成] 总计:{synced_count}, 新建:{created_count}, 更新:{updated_count}")
    
    def sync_to_erp(self):
        """推送本地数据到ERP"""
        print("[同步] 开始推送数据到ERP...")
        
        # 1. 查找需要同步的客户
        pending_customers = self._get_pending_sync_customers()
        
        synced_count = 0
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for customer in pending_customers:
            # 2. 评估是否应该同步
            evaluation = self.rule_engine.evaluate(customer)
            
            # 3. 记录评估结果
            self._log_evaluation(customer.id, evaluation)
            
            # 4. 执行同步动作
            if evaluation['action'] == 'CREATE':
                success = self._create_in_erp(customer)
                if success:
                    created_count += 1
                    synced_count += 1
            
            elif evaluation['action'] == 'UPDATE':
                success = self._update_in_erp(customer)
                if success:
                    updated_count += 1
                    synced_count += 1
            
            elif evaluation['action'] == 'SKIP':
                skipped_count += 1
                self._mark_sync_skipped(customer.id, evaluation['reason'])
        
        print(f"[同步完成] 总计:{len(pending_customers)}, 创建:{created_count}, 更新:{updated_count}, 跳过:{skipped_count}")
    
    def _find_local_customer(self, erp_id=None, phone=None):
        """查找本地客户（支持多种匹配方式）"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 优先用ERP ID匹配
        if erp_id:
            cursor.execute(
                'SELECT * FROM customers_unified WHERE erp_customer_id = ?',
                (erp_id,)
            )
            row = cursor.fetchone()
            if row:
                conn.close()
                return dict(row)
        
        # 其次用手机号匹配
        if phone:
            cursor.execute(
                'SELECT * FROM customers_unified WHERE phone = ?',
                (phone,)
            )
            row = cursor.fetchone()
            if row:
                conn.close()
                return dict(row)
        
        conn.close()
        return None
    
    def _merge_changes(self, customer_id, changes):
        """融合变更"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for change in changes['changes']:
            field = change['field']
            action = change['action']
            
            if action == 'take_erp':
                # 更新为ERP的值
                cursor.execute(f'''
                    UPDATE customers_unified
                    SET {field} = ?,
                        {field}_source = 'erp',
                        erp_updated_at = ?
                    WHERE id = ?
                ''', (change['erp_value'], datetime.now(), customer_id))
                
                # 记录变更历史
                self._log_field_change(
                    customer_id, field,
                    old_value=change['local_value'],
                    new_value=change['erp_value'],
                    source='erp'
                )
            
            elif action == 'take_local':
                # 标记为需要推送到ERP
                cursor.execute('''
                    UPDATE customers_unified
                    SET erp_sync_status = 'pending'
                    WHERE id = ?
                ''', (customer_id,))
        
        conn.commit()
        conn.close()
```

### 配置文件

```yaml
# config.yaml

unified_sync:
  enabled: true
  
  # ERP拉取配置
  erp_pull:
    enabled: true
    interval: 3600                # 每小时
    batch_size: 100
    incremental: true             # 增量同步
    
  # ERP推送配置
  erp_push:
    enabled: true
    interval: 1800                # 每30分钟
    batch_size: 50
    auto_sync: true               # 自动同步（不需要审批）
    
  # 规则引擎配置
  rules:
    # 强制同步规则
    mandatory_sync:
      enabled: true
      conditions:
        - has_order
        - has_contract
        - has_payment
        - marked_as_important
    
    # 高质量自动同步
    high_quality_sync:
      enabled: true
      min_quality_score: 80
      required_fields:
        - phone_verified
        - company_name
      min_intent_score: 80
    
    # 中等质量条件同步
    medium_quality_sync:
      enabled: true
      combinations:
        - [phone, quote_request]
        - [company_name, business_license]
        - [conversation_days>=7, message_count>=50]
    
    # 低质量跳过
    low_quality_skip:
      enabled: true
      skip_conditions:
        - no_basic_info
        - intent_score<30
        - message_count<5
        - marked_as_invalid
  
  # 冲突处理
  conflict_resolution:
    strategy: 'priority_based'      # priority_based/timestamp/manual
    core_fields:                    # 核心字段以ERP为准
      - phone
      - company_name
      - erp_customer_code
    local_priority_fields:          # 本地优先字段
      - wechat_id
      - wechat_nickname
      - intent_score
    
  # 数据质量
  data_quality:
    min_score_for_sync: 60          # 最低质量分数
    verify_before_sync: true        # 同步前验证
    auto_fix_format: true           # 自动修正格式问题
```

---

## 使用示例

### 场景1: 从ERP拉取客户

```python
# 定时任务：每小时执行
def scheduled_pull_from_erp():
    sync_service = UnifiedCustomerSyncService(
        erp_api=erp_api,
        rule_engine=rule_engine,
        change_detector=change_detector
    )
    
    sync_service.sync_from_erp()
```

### 场景2: 微信信息自动融合

```python
# 微信消息处理
def on_message(message):
    wechat_id = message['sender']
    
    # 1. AI提取信息
    extracted = ai_extract_info(message['content'])
    
    if extracted:
        # 2. 更新本地客户
        customer = db.get_customer_by_wechat_id(wechat_id)
        if customer:
            db.update_customer_extracted_info(
                customer_id=customer.id,
                extracted_info=extracted
            )
            
            # 3. 触发同步评估
            sync_service = UnifiedCustomerSyncService(...)
            evaluation = rule_engine.evaluate(customer)
            
            # 4. 如果满足条件，自动同步
            if evaluation['action'] in ['CREATE', 'UPDATE']:
                sync_service.sync_to_erp_single(customer)
```

### 场景3: 定时推送到ERP

```python
# 定时任务：每30分钟执行
def scheduled_push_to_erp():
    sync_service = UnifiedCustomerSyncService(...)
    sync_service.sync_to_erp()
```

---

## 总结

### ✅ 优势

1. **无需人工审批** - 规则引擎自动判定
2. **ERP为主** - 数据权威性有保证
3. **本地融合** - 微信信息自动补充
4. **智能同步** - 根据数据质量自动决策
5. **双向流动** - ERP→本地→ERP形成闭环
6. **可追溯** - 完整的变更历史记录

### 📊 预期效果

- **同步准确率**: 95%+（规则自动判定）
- **数据完整度**: 提升50%+（融合多源数据）
- **人工工作量**: 减少90%+（自动化同步）
- **数据质量**: ERP数据干净，本地数据丰富

### 🎯 关键点

1. **以ERP为准** - 核心字段永远信任ERP
2. **智能融合** - 补充字段优先本地
3. **自动决策** - 规则引擎替代人工审批
4. **渐进同步** - 数据逐步完善，质量达标后自动同步

需要我帮您：
1. 实现规则引擎代码？
2. 创建数据库迁移脚本？
3. 开发同步服务？
4. 调整规则配置？

