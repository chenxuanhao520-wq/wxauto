# 微信客服中台 ↔ 智邦ERP CRM 集成方案

**版本**: v1.0  
**创建时间**: 2025-10-18  
**目标**: 通过自动化集成，降低客户信息和跟进记录的维护工作量

---

## 📋 目录

1. [核心集成场景](#核心集成场景)
2. [客户编号维护](#客户编号维护)
3. [客户跟进记录维护](#客户跟进记录维护)
4. [其他关联动作](#其他关联动作)
5. [技术实现方案](#技术实现方案)
6. [数据流程图](#数据流程图)
7. [API调用示例](#api调用示例)

---

## 核心集成场景

### 一、客户信息同步（双向）

#### 场景1: 微信新客户 → ERP自动创建
**触发条件**: 
- 微信收到陌生人消息（未在ERP中存在）
- 客户中台识别为潜在客户（白名单/灰名单）

**自动化动作**:
1. ✅ 从微信获取：昵称、微信号、头像
2. ✅ 调用ERP接口 → 创建客户档案
3. ✅ 自动分配客户编号（ERP生成）
4. ✅ 回写微信中台 → 存储ERP客户ID和编号
5. ✅ 设置客户来源 = "微信咨询"（新建枚举值）

#### 场景2: ERP客户 → 微信中台关联
**触发条件**:
- ERP中已有客户，首次通过微信联系

**自动化动作**:
1. ✅ 通过手机号/公司名匹配ERP客户
2. ✅ 建立微信账号 ↔ ERP客户ID 的映射关系
3. ✅ 同步客户基本信息（分类、价值评估、跟进程度等）
4. ✅ 显示历史跟进记录

---

### 二、客户编号维护（核心需求）

#### 现状问题
- ❌ 微信客户只有昵称，难以管理
- ❌ 多个销售人员可能重复创建客户
- ❌ 无统一的客户编号体系

#### 解决方案

**方案A: ERP为主，自动生成编号**
```
微信新客户 
  → 检查是否已存在（手机号/公司名匹配）
  → 不存在：调用ERP【分配新客户ID】接口
  → 获取ERP自动生成的客户编号
  → 保存到微信中台的 customer_manager.customers 表
  → 在微信聊天界面显示"客户编号: KHXXX"
```

**方案B: 微信中台辅助，智能编号**
```
微信新客户
  → 中台生成临时编号（如 WX20251018001）
  → 销售确认后，同步到ERP
  → ERP分配正式编号（如 KH2025001）
  → 回写到微信中台，显示正式编号
```

**推荐**: 方案A，以ERP为客户主数据源

---

### 三、客户跟进记录维护（核心需求）

#### 现状问题
- ❌ 微信聊天记录散落，难以统计
- ❌ ERP中手动录入跟进记录，工作量大
- ❌ 跟进进度不同步，信息孤岛

#### 解决方案：自动化跟进记录

**3.1 微信消息 → ERP跟进记录**

| 触发事件 | 自动记录到ERP | API接口 |
|---------|-------------|---------|
| 客户发消息给销售 | 客户主动咨询 + 消息摘要 | `/systemmanage/reply.asp?datatype=tel` |
| 销售回复客户 | 销售跟进 + 回复要点 | 同上 |
| 发送产品资料/图片 | 发送资料：XXX产品 | 同上 |
| 客户询价 | 客户询价：具体内容 | 同上 |
| 预约上门/视频 | 预约线下沟通 | 同上 + 创建日程 |

**3.2 智能跟进方式识别**

```python
# 根据微信消息内容，自动识别跟进方式
message_keywords = {
    "电话": 481,      # 电话跟进
    "邮件": 482,      # 邮件跟进
    "上门": 483,      # 上门拜访
    "见面": 483,
    "微信": 484,      # 其他（微信）
    "default": 484
}
```

**3.3 跟进记录数据结构**

```python
follow_up_record = {
    "ord": customer_erp_id,           # ERP客户ID
    "intro": message_summary,         # 跟进内容摘要（AI生成）
    "sort": 484,                      # 跟进方式（微信=484）
    "plantype": 0,                    # 不生成日程
    # 如果需要创建待办
    "@title1": "回复客户XXX咨询",
    "@ret_0": datetime.now(),
    "@ret_1": datetime.now() + timedelta(hours=2)
}
```

---

## 其他关联动作

### 1. 客户分级自动更新

**触发条件**: 客户中台的置信打分变化

| 中台客户状态 | 自动更新到ERP |
|------------|-------------|
| WHITE (白名单) | 跟进程度 = "重点客户" |
| GRAY (灰名单) | 跟进程度 = "潜在客户" |
| BLACK (黑名单) | 跟进程度 = "暂不跟进" |

**API接口**: `/salesmanage/custom/add.asp` (修改客户)
**字段**: `sort1` (跟进程度)

---

### 2. 销售线索自动分配

**触发条件**: 
- 微信新客户加入（客户池）
- 中台判断为高价值客户

**自动化动作**:
1. 根据规则分配销售人员（地区/产品线/工作量）
2. 调用ERP【客户指派】接口
3. 通知销售人员（微信/钉钉）

**API接口**: `/systemmanage/order.asp?datatype=tel`

---

### 3. 商机/项目自动创建

**触发条件**: 
- 客户明确询价
- 客户要求报价
- 客户咨询具体产品

**自动化动作**:
1. AI识别商机信号（关键词：报价、采购、需求、预算）
2. 创建ERP项目/商机
3. 关联客户和产品

**API接口**: `/salesmanage/chance/add.asp` (项目管理)

---

### 4. 合同/订单关联

**触发条件**:
- 客户发送合同相关文件
- 讨论合同条款
- 确认下单

**自动化动作**:
1. 识别合同关键信息（金额、产品、数量）
2. 提醒销售在ERP中创建合同
3. 自动填充部分信息

**API接口**: `/salesmanage/contract/add.asp` (合同管理)

---

### 5. 客户标签同步

**微信中台 → ERP**:
- 客户行业：自动识别并更新到ERP `trade` 字段
- 客户区域：根据IP/地址更新到ERP `area` 字段
- 价值评估：根据中台评分更新到ERP `jz` 字段

**ERP → 微信中台**:
- 同步客户分类、跟进程度、VIP等级
- 显示在微信聊天界面

---

### 6. 产品咨询统计

**自动化统计**:
- 哪些产品被咨询最多
- 哪些客户咨询了哪些产品
- 咨询转化率

**数据来源**:
- 微信消息中提取产品关键词
- 关联ERP产品列表
- 生成咨询报表

---

### 7. 售后服务关联

**触发条件**:
- 客户反馈问题/投诉
- 客户要求维修/退换货

**自动化动作**:
1. 创建ERP售后服务单
2. 分配服务人员
3. 跟踪处理进度

**API接口**: `/salesmanage/service/add.asp` (售后服务)

---

### 8. 客户沟通历史归档

**自动化归档**:
- 重要的微信聊天记录 → ERP附件
- 客户发送的文件 → ERP文档管理
- 语音消息转文字 → ERP备注

---

## 技术实现方案

### 架构设计

```
┌─────────────────┐
│  微信客服中台    │
│  (wxauto-1)     │
└────────┬────────┘
         │
         ├─ 1. 消息监听
         ├─ 2. 客户识别
         ├─ 3. 智能分析
         │
         ▼
┌─────────────────┐
│  ERP集成服务     │
│  (新建模块)      │
├─────────────────┤
│ • 客户同步       │
│ • 跟进记录       │
│ • 商机创建       │
│ • 数据回写       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  智邦ERP API    │
│  (HTTP接口)     │
└─────────────────┘
```

---

### 数据库设计

#### 新增表：erp_customer_mapping（客户映射表）

```sql
CREATE TABLE erp_customer_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 微信中台信息
    wechat_id VARCHAR(100) NOT NULL,        -- 微信ID
    wechat_nickname VARCHAR(200),           -- 微信昵称
    customer_hub_contact_id INTEGER,        -- 中台联系人ID
    
    -- ERP信息
    erp_customer_id INTEGER,                -- ERP客户ID (ord)
    erp_customer_code VARCHAR(50),          -- ERP客户编号 (khid)
    erp_customer_name VARCHAR(200),         -- ERP客户名称
    erp_customer_type INTEGER,              -- 客户类型 1=单位 2=个人
    
    -- 同步状态
    sync_status VARCHAR(20),                -- pending/synced/failed
    last_sync_time DATETIME,                -- 最后同步时间
    sync_direction VARCHAR(20),             -- wechat_to_erp/erp_to_wechat
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(wechat_id, erp_customer_id)
);

CREATE INDEX idx_wechat_id ON erp_customer_mapping(wechat_id);
CREATE INDEX idx_erp_customer_id ON erp_customer_mapping(erp_customer_id);
```

#### 新增表：erp_followup_records（跟进记录同步表）

```sql
CREATE TABLE erp_followup_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 关联信息
    wechat_id VARCHAR(100) NOT NULL,        -- 微信ID
    erp_customer_id INTEGER NOT NULL,       -- ERP客户ID
    message_id VARCHAR(100),                -- 微信消息ID
    
    -- 跟进内容
    followup_type INTEGER,                  -- 跟进方式 481-484
    followup_content TEXT,                  -- 跟进内容
    ai_summary TEXT,                        -- AI生成的摘要
    
    -- 同步状态
    synced_to_erp BOOLEAN DEFAULT 0,
    erp_sync_time DATETIME,
    erp_response TEXT,                      -- ERP返回信息
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (erp_customer_id) REFERENCES erp_customer_mapping(erp_customer_id)
);
```

#### 扩展现有表：customer_manager.customers

```sql
-- 添加ERP关联字段
ALTER TABLE customers ADD COLUMN erp_customer_id INTEGER;
ALTER TABLE customers ADD COLUMN erp_customer_code VARCHAR(50);
ALTER TABLE customers ADD COLUMN erp_sync_status VARCHAR(20);
ALTER TABLE customers ADD COLUMN erp_last_sync_time DATETIME;
```

---

### 核心模块实现

#### 模块1: ERP客户同步服务 (`erp_sync/customer_sync.py`)

```python
"""
客户信息同步服务
"""
import requests
from datetime import datetime
from storage.db import get_db_connection

class ERPCustomerSync:
    def __init__(self, erp_config):
        self.base_url = erp_config['base_url']
        self.session_token = None
        
    def login(self, username, password):
        """登录ERP获取session"""
        url = f"{self.base_url}/webapi/v3/ov1/login"
        datas = [
            {"id": "user", "val": f"txt:{username}"},
            {"id": "password", "val": f"txt:{password}"},
            {"id": "serialnum", "val": "wxbot001"}
        ]
        response = requests.post(url, json={"datas": datas})
        result = response.json()
        if result['header']['status'] == 0:
            self.session_token = result['header']['session']
            return True
        return False
    
    def create_customer_in_erp(self, wechat_customer):
        """
        在ERP中创建新客户
        
        Args:
            wechat_customer: 微信客户信息 dict
            
        Returns:
            erp_customer_id, erp_customer_code
        """
        # Step 1: 分配新客户ID
        new_id = self._allocate_customer_id(
            customer_type=1  # 默认单位客户
        )
        
        # Step 2: 保存客户信息
        customer_data = {
            "ord": new_id,
            "name": wechat_customer['name'],
            "sort1": "潜在客户",  # 跟进程度
            "ly": self._get_source_enum("微信咨询"),  # 客户来源
            "person_name": wechat_customer['contact_name'],
            "mobile": wechat_customer.get('phone', ''),
            "weixinAcc": wechat_customer['wechat_id'],
            "intro": f"来自微信客服中台，添加时间：{datetime.now()}"
        }
        
        result = self._save_customer(customer_data, customer_type=1)
        
        if result['success']:
            # Step 3: 保存映射关系
            self._save_mapping(
                wechat_id=wechat_customer['wechat_id'],
                erp_customer_id=new_id,
                erp_customer_code=result['customer_code']
            )
            
            return new_id, result['customer_code']
        
        return None, None
    
    def _allocate_customer_id(self, customer_type=1):
        """分配新客户ID"""
        url = f"{self.base_url}/sysa/mobilephone/salesmanage/custom/add.asp"
        datas = [
            {"id": "edit", "val": ""},
            {"id": "intsort", "val": str(customer_type)}
        ]
        response = requests.post(url, json={
            "session": self.session_token,
            "datas": datas
        })
        result = response.json()
        # 从返回的BillClass中提取value（新客户ID）
        return result['data']['value']
    
    def _save_customer(self, customer_data, customer_type=1):
        """保存客户到ERP"""
        url = f"{self.base_url}/sysa/mobilephone/salesmanage/custom/add.asp?intsort={customer_type}"
        
        datas = [
            {"id": key, "val": value} 
            for key, value in customer_data.items()
        ]
        
        response = requests.post(url, json={
            "session": self.session_token,
            "cmdkey": "__sys_dosave",
            "datas": datas
        })
        
        result = response.json()
        # 解析返回结果
        return {
            "success": result['header']['status'] == 0,
            "message": result['data']['text'],
            "customer_code": customer_data.get('khid', '')  # 如果ERP自动生成需要再查询
        }
    
    def _save_mapping(self, wechat_id, erp_customer_id, erp_customer_code):
        """保存微信↔ERP映射关系"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO erp_customer_mapping
            (wechat_id, erp_customer_id, erp_customer_code, 
             sync_status, last_sync_time, sync_direction)
            VALUES (?, ?, ?, 'synced', ?, 'wechat_to_erp')
        ''', (wechat_id, erp_customer_id, erp_customer_code, datetime.now()))
        conn.commit()
        conn.close()
    
    def find_customer_by_phone(self, phone):
        """通过手机号在ERP中查找客户"""
        url = f"{self.base_url}/sysa/mobilephone/salesmanage/custom/list.asp"
        datas = [
            {"id": "phone", "val": phone},
            {"id": "pagesize", "val": 10}
        ]
        response = requests.post(url, json={
            "session": self.session_token,
            "cmdkey": "refresh",
            "datas": datas
        })
        result = response.json()
        # 解析返回的表格数据
        if result['data']['table']['rows']:
            return result['data']['table']['rows'][0]
        return None
```

---

#### 模块2: ERP跟进记录服务 (`erp_sync/followup_sync.py`)

```python
"""
跟进记录同步服务
"""
import requests
from datetime import datetime
from ai_gateway.gateway import AIGateway

class ERPFollowupSync:
    def __init__(self, erp_config, ai_gateway):
        self.base_url = erp_config['base_url']
        self.session_token = None
        self.ai_gateway = ai_gateway
        
        # 跟进方式映射
        self.followup_type_mapping = {
            "电话": 481,
            "邮件": 482,
            "上门": 483,
            "见面": 483,
            "拜访": 483,
            "微信": 484,
            "default": 484  # 默认为其他（微信）
        }
    
    def sync_wechat_message_to_erp(self, wechat_message):
        """
        将微信消息同步为ERP跟进记录
        
        Args:
            wechat_message: {
                'wechat_id': '微信ID',
                'content': '消息内容',
                'sender': 'customer/staff',
                'timestamp': datetime
            }
        """
        # 1. 获取ERP客户ID
        erp_customer = self._get_erp_customer(wechat_message['wechat_id'])
        if not erp_customer:
            print(f"未找到微信ID {wechat_message['wechat_id']} 对应的ERP客户")
            return False
        
        # 2. AI生成跟进摘要
        summary = self._generate_followup_summary(wechat_message)
        
        # 3. 识别跟进方式
        followup_type = self._detect_followup_type(wechat_message['content'])
        
        # 4. 创建跟进记录
        followup_data = {
            "ord": erp_customer['erp_customer_id'],
            "intro": summary,
            "sort": followup_type,
            "plantype": 0,  # 不生成日程
            # 如果客户询问重要问题，创建待办
            # "@title1": "回复客户咨询",
            # "@ret_0": datetime.now(),
            # "@ret_1": datetime.now() + timedelta(hours=2)
        }
        
        # 5. 调用ERP接口
        success = self._create_followup_in_erp(followup_data)
        
        # 6. 记录同步状态
        if success:
            self._save_followup_record(
                wechat_id=wechat_message['wechat_id'],
                erp_customer_id=erp_customer['erp_customer_id'],
                followup_type=followup_type,
                followup_content=wechat_message['content'],
                ai_summary=summary
            )
        
        return success
    
    def _generate_followup_summary(self, message):
        """使用AI生成跟进摘要"""
        prompt = f"""
        请将以下微信聊天内容总结为简洁的客户跟进记录（50字以内）：
        
        发送者: {'客户' if message['sender'] == 'customer' else '销售'}
        内容: {message['content']}
        时间: {message['timestamp']}
        
        要求：
        1. 提取关键信息（产品、需求、问题等）
        2. 简洁专业，适合CRM系统
        3. 不超过50字
        """
        
        response = self.ai_gateway.chat(prompt)
        return response.strip()
    
    def _detect_followup_type(self, content):
        """识别跟进方式"""
        for keyword, type_id in self.followup_type_mapping.items():
            if keyword in content:
                return type_id
        return self.followup_type_mapping['default']
    
    def _create_followup_in_erp(self, followup_data):
        """在ERP中创建跟进记录"""
        url = f"{self.base_url}/sysa/mobilephone/systemmanage/reply.asp?datatype=tel"
        
        datas = [
            {"id": key, "val": value}
            for key, value in followup_data.items()
        ]
        
        response = requests.post(url, json={
            "session": self.session_token,
            "cmdkey": "__sys_dosave",
            "datas": datas
        })
        
        result = response.json()
        return result['header']['status'] == 0
    
    def _get_erp_customer(self, wechat_id):
        """获取微信对应的ERP客户"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT erp_customer_id, erp_customer_code
            FROM erp_customer_mapping
            WHERE wechat_id = ?
        ''', (wechat_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'erp_customer_id': row[0],
                'erp_customer_code': row[1]
            }
        return None
    
    def _save_followup_record(self, wechat_id, erp_customer_id, 
                              followup_type, followup_content, ai_summary):
        """保存跟进记录到本地数据库"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO erp_followup_records
            (wechat_id, erp_customer_id, followup_type, 
             followup_content, ai_summary, synced_to_erp, erp_sync_time)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        ''', (wechat_id, erp_customer_id, followup_type, 
              followup_content, ai_summary, datetime.now()))
        conn.commit()
        conn.close()
```

---

#### 模块3: 集成调度服务 (`erp_sync/scheduler.py`)

```python
"""
ERP集成调度服务
自动触发各种同步任务
"""
import schedule
import time
from threading import Thread

class ERPSyncScheduler:
    def __init__(self, customer_sync, followup_sync):
        self.customer_sync = customer_sync
        self.followup_sync = followup_sync
        
    def start(self):
        """启动调度器"""
        # 每5分钟同步一次新客户
        schedule.every(5).minutes.do(self.sync_new_customers)
        
        # 每10分钟同步一次跟进记录
        schedule.every(10).minutes.do(self.sync_followup_records)
        
        # 每小时同步一次客户信息更新
        schedule.every(1).hours.do(self.sync_customer_updates)
        
        # 在后台线程运行
        thread = Thread(target=self._run_scheduler, daemon=True)
        thread.start()
    
    def _run_scheduler(self):
        """运行调度循环"""
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def sync_new_customers(self):
        """同步新客户到ERP"""
        print("[ERP同步] 开始同步新客户...")
        # 查找未同步的客户
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.* FROM customers c
            LEFT JOIN erp_customer_mapping m ON c.wechat_id = m.wechat_id
            WHERE m.id IS NULL
            AND c.bucket = 'WHITE'  -- 只同步白名单客户
            LIMIT 50
        ''')
        new_customers = cursor.fetchall()
        conn.close()
        
        for customer in new_customers:
            try:
                self.customer_sync.create_customer_in_erp({
                    'wechat_id': customer['wechat_id'],
                    'name': customer['name'] or customer['nickname'],
                    'contact_name': customer['nickname'],
                    'phone': customer.get('phone', '')
                })
                print(f"✅ 已同步客户: {customer['nickname']}")
            except Exception as e:
                print(f"❌ 同步客户失败 {customer['nickname']}: {e}")
    
    def sync_followup_records(self):
        """同步跟进记录到ERP"""
        print("[ERP同步] 开始同步跟进记录...")
        # 实现逻辑...
```

---

## 数据流程图

### 流程1: 微信新客户 → ERP

```
微信消息到达
    ↓
客户中台识别
    ↓
判断：是否新客户？
    ├─ 是 → 检查是否需要同步（白名单/灰名单）
    │         ↓
    │      调用ERP【分配新客户ID】
    │         ↓
    │      调用ERP【保存客户信息】
    │         ↓
    │      保存映射关系到本地数据库
    │         ↓
    │      在微信界面显示"客户编号: KHXXX"
    │
    └─ 否 → 查询已有映射关系
              ↓
           显示客户编号和基本信息
```

### 流程2: 微信消息 → ERP跟进记录

```
客户/销售发送消息
    ↓
AI分析消息内容
    ├─ 提取关键信息
    ├─ 生成跟进摘要
    └─ 识别跟进方式
    ↓
查询ERP客户ID
    ↓
调用ERP【客户跟进】接口
    ↓
保存同步记录
    ↓
在微信界面显示"已同步到ERP"
```

---

## API调用示例

### 完整示例：新客户同步

```python
# main.py - 集成到现有微信客服中台

from erp_sync.customer_sync import ERPCustomerSync
from erp_sync.followup_sync import ERPFollowupSync
from erp_sync.scheduler import ERPSyncScheduler

# 1. 初始化ERP同步服务
erp_config = {
    'base_url': 'http://ls1.jmt.ink:46088',
    'username': 'your_username',
    'password': 'your_password'
}

customer_sync = ERPCustomerSync(erp_config)
customer_sync.login(erp_config['username'], erp_config['password'])

followup_sync = ERPFollowupSync(erp_config, ai_gateway)
followup_sync.session_token = customer_sync.session_token

# 2. 启动自动同步调度器
scheduler = ERPSyncScheduler(customer_sync, followup_sync)
scheduler.start()

# 3. 在微信消息处理中集成
def on_wechat_message_received(message):
    """微信消息回调"""
    # 原有的消息处理逻辑
    # ...
    
    # 新增：同步跟进记录到ERP
    if message['type'] == 'text':
        followup_sync.sync_wechat_message_to_erp({
            'wechat_id': message['sender'],
            'content': message['content'],
            'sender': 'customer',
            'timestamp': datetime.now()
        })
```

---

## 配置文件示例

```yaml
# config.yaml - 新增ERP集成配置

erp_integration:
  enabled: true
  base_url: "http://ls1.jmt.ink:46088"
  
  # 认证信息
  auth:
    username: "your_username"
    password: "your_password"
    auto_login: true
  
  # 客户同步配置
  customer_sync:
    enabled: true
    auto_create: true  # 自动创建新客户
    sync_interval: 300  # 秒
    customer_source: "微信咨询"  # 客户来源（需在ERP中配置）
    default_category: "潜在客户"  # 默认跟进程度
    sync_conditions:
      - bucket: "WHITE"  # 白名单客户
      - bucket: "GRAY"   # 灰名单客户
  
  # 跟进记录同步配置
  followup_sync:
    enabled: true
    auto_sync: true  # 自动同步聊天记录
    sync_interval: 600  # 秒
    ai_summary: true  # 使用AI生成摘要
    min_message_length: 10  # 最小消息长度
    excluded_keywords:  # 排除的关键词（不同步）
      - "在吗"
      - "你好"
      - "再见"
  
  # 数据映射配置
  field_mapping:
    customer_name: "name"
    contact_name: "person_name"
    phone: "mobile"
    wechat: "weixinAcc"
    company: "faren"  # 个人客户的所在单位
  
  # 失败重试配置
  retry:
    max_attempts: 3
    retry_interval: 60  # 秒
```

---

## 总结与建议

### ✅ 推荐实施的集成功能（优先级排序）

1. **P0 - 必须实施**
   - ✅ 客户编号自动维护（ERP生成，中台显示）
   - ✅ 微信消息 → ERP跟进记录（AI摘要）

2. **P1 - 强烈推荐**
   - ✅ 客户信息双向同步
   - ✅ 客户分级自动更新
   - ✅ 新客户自动创建

3. **P2 - 可选功能**
   - ⭕ 商机/项目自动创建
   - ⭕ 产品咨询统计
   - ⭕ 销售线索自动分配

4. **P3 - 未来扩展**
   - ⭕ 合同/订单关联
   - ⭕ 售后服务关联
   - ⭕ 聊天记录归档

### 💡 降低维护工作量的关键点

1. **客户编号**: 一次创建，自动同步，微信聊天界面即可看到
2. **跟进记录**: AI自动生成摘要，无需手动录入
3. **客户信息**: 自动识别更新，减少重复劳动
4. **智能提醒**: 重要客户自动分配，及时跟进

### 🎯 下一步行动

1. **第一周**: 实现客户映射表和基础同步服务
2. **第二周**: 实现跟进记录自动同步（AI摘要）
3. **第三周**: 完善调度器和错误处理
4. **第四周**: 测试和优化

需要我帮您：
- 开始编写具体的代码实现？
- 创建数据库迁移脚本？
- 编写测试用例？

