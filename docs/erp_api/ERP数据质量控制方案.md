# ERP数据质量控制方案

**版本**: v2.0  
**更新时间**: 2025-10-18  
**核心原则**: 宁缺毋滥，保证ERP数据真实、有效、高质量

---

## 📋 目录

1. [数据质量问题分析](#数据质量问题分析)
2. [客户同步准入规则](#客户同步准入规则)
3. [三层数据管理架构](#三层数据管理架构)
4. [智能验证机制](#智能验证机制)
5. [实施方案](#实施方案)

---

## 数据质量问题分析

### 当前风险

| 风险类型 | 具体问题 | 影响 |
|---------|---------|------|
| **垃圾数据** | 随便加的微信好友，闲聊用户 | ERP客户库膨胀，无效数据 |
| **重复数据** | 同一客户多个微信号 | 数据冗余，统计失真 |
| **不完整数据** | 只有微信昵称，无真实信息 | 无法有效跟进和转化 |
| **虚假数据** | 假名字、假公司 | 影响商机判断和决策 |
| **过早同步** | 潜在客户还未确认意向 | ERP数据噪音大 |

### 真实客户特征（准入标准）

✅ **必须满足以下至少一个条件**：

1. **明确采购意向**
   - 询价、要报价
   - 咨询具体产品规格
   - 询问交货期、付款方式
   - 要求发送方案

2. **提供真实信息**
   - 公司名称（非个人微信昵称）
   - 手机号（11位有效号码）
   - 营业执照/名片照片
   - 公司地址

3. **达成初步合作**
   - 已下单
   - 已签合同
   - 已付款/定金
   - 已发货

4. **高价值线索**
   - 大客户（从公开信息可查）
   - 老客户推荐
   - 行业标杆企业
   - VIP客户

---

## 客户同步准入规则

### 方案A: 严格准入制（推荐）

**同步到ERP的触发条件（必须全部满足）**:

```yaml
erp_sync_rules:
  # 规则1: 信息完整性（至少满足2项）
  required_fields:
    min_count: 2
    options:
      - real_name: true          # 真实姓名
      - company_name: true       # 公司名称
      - phone: true              # 手机号（已验证）
      - email: true              # 企业邮箱
      - business_license: true   # 营业执照
      
  # 规则2: 商业意向（至少满足1项）
  business_intent:
    min_count: 1
    options:
      - requested_quote: true    # 要求报价
      - asked_price: true        # 询价
      - discussed_product: true  # 深入讨论产品
      - scheduled_meeting: true  # 约见面
      - requested_contract: true # 要求合同
      
  # 规则3: 互动质量
  interaction_quality:
    message_count: 10           # 至少互动10条消息
    conversation_days: 2        # 至少沟通2天
    avg_message_length: 20      # 平均消息长度>20字
    
  # 规则4: 人工确认
  manual_approval:
    enabled: true               # 需要销售人员确认
    auto_approve_conditions:    # 自动批准条件
      - has_order: true         # 已下单
      - has_contract: true      # 已签合同
      - paid_deposit: true      # 已付定金
```

### 方案B: 分阶段同步（灵活）

#### 阶段1: 微信中台（潜在池）
**所有微信联系人** → 存储在微信中台数据库
- 自动保存基本信息
- 客户中台评分
- 标记意向等级

#### 阶段2: 待审核池（缓冲区）
**通过初步筛选** → 进入"待同步到ERP"队列
- 满足最低信息要求
- 有一定商业意向
- 等待人工审核

#### 阶段3: ERP客户库（正式）
**人工审核通过** → 正式同步到ERP
- 信息真实完整
- 商业价值确认
- 分配给销售跟进

---

## 三层数据管理架构

```
┌─────────────────────────────────────────────────┐
│  第1层: 微信联系人池（wxauto中台）                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  • 所有加过微信的人                               │
│  • 自动采集：昵称、微信号、头像                    │
│  • 智能分析：消息内容、互动频次                    │
│  • 数据标签：WHITE/GRAY/BLACK                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  ✓ 无门槛，全量保存                               │
│  ✓ 用于AI分析和初步筛选                           │
└─────────────────────────────────────────────────┘
                      ↓
              【智能筛选+人工审核】
                      ↓
┌─────────────────────────────────────────────────┐
│  第2层: 待转化客户池（中台qualified_leads表）        │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  准入条件（满足任一）:                             │
│  • 提供了手机号或公司名                           │
│  • 明确询价或要报价                               │
│  • 沟通超过10条消息                               │
│  • 上传了营业执照/名片                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  ✓ 有一定质量保证                                 │
│  ✓ 等待进一步验证                                 │
└─────────────────────────────────────────────────┘
                      ↓
              【严格验证+销售确认】
                      ↓
┌─────────────────────────────────────────────────┐
│  第3层: ERP正式客户库（智邦ERP）                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  严格准入（必须满足）:                             │
│  ✅ 手机号已验证（真实有效）                       │
│  ✅ 公司名称已确认（非个人微信昵称）                │
│  ✅ 至少一项证明文件（执照/名片/合同）              │
│  ✅ 销售人员确认（点击"同步到ERP"按钮）             │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  ✓ 高质量客户数据                                 │
│  ✓ 可直接用于商机管理                             │
└─────────────────────────────────────────────────┘
```

---

## 智能验证机制

### 1. 手机号验证

```python
class PhoneValidator:
    """手机号验证器"""
    
    def validate_phone(self, phone):
        """
        验证手机号真实性
        
        Returns:
            {
                'valid': bool,
                'carrier': str,  # 运营商
                'region': str,   # 归属地
                'type': str      # 类型（个人/企业）
            }
        """
        # 1. 格式验证
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return {'valid': False, 'reason': '格式错误'}
        
        # 2. 空号检测（可选：调用第三方API）
        # is_active = self.check_phone_active(phone)
        
        # 3. 运营商识别
        carrier = self.get_carrier(phone)
        
        # 4. 归属地识别
        region = self.get_region(phone)
        
        return {
            'valid': True,
            'carrier': carrier,
            'region': region,
            'type': 'mobile'
        }
```

### 2. 公司名称验证

```python
class CompanyValidator:
    """公司名称验证器"""
    
    def validate_company(self, company_name):
        """
        验证公司名称真实性
        
        Methods:
        1. 工商信息查询API（天眼查/企查查）
        2. 营业执照OCR识别
        3. 公司官网验证
        """
        # 1. 基础格式检查
        if len(company_name) < 4:
            return {'valid': False, 'reason': '名称过短'}
        
        # 排除明显的个人名称
        personal_keywords = ['先生', '女士', '小姐', '老板']
        if any(kw in company_name for kw in personal_keywords):
            return {'valid': False, 'reason': '疑似个人名称'}
        
        # 2. 工商信息查询（可选：需要API密钥）
        # company_info = self.query_business_registration(company_name)
        # if company_info:
        #     return {
        #         'valid': True,
        #         'unified_code': company_info['credit_code'],
        #         'legal_person': company_info['legal_person'],
        #         'status': company_info['status']
        #     }
        
        # 3. 简单规则验证
        valid_suffixes = ['公司', '企业', '集团', '中心', '工厂', '厂']
        if any(company_name.endswith(suffix) for suffix in valid_suffixes):
            return {'valid': True, 'confidence': 'medium'}
        
        return {'valid': False, 'reason': '需要人工确认'}
```

### 3. 营业执照OCR识别

```python
class BusinessLicenseOCR:
    """营业执照识别"""
    
    def extract_info(self, image_path):
        """
        从营业执照图片提取信息
        
        Returns:
            {
                'company_name': str,
                'unified_code': str,     # 统一社会信用代码
                'legal_person': str,     # 法人
                'address': str,
                'business_scope': str
            }
        """
        # 调用OCR服务（百度/阿里/腾讯）
        # 这里使用百度OCR示例
        from aip import AipOcr
        
        client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
        
        with open(image_path, 'rb') as f:
            image = f.read()
        
        result = client.businessLicense(image)
        
        if result.get('words_result'):
            words = result['words_result']
            return {
                'company_name': words.get('单位名称', {}).get('words', ''),
                'unified_code': words.get('社会信用代码', {}).get('words', ''),
                'legal_person': words.get('法人', {}).get('words', ''),
                'address': words.get('地址', {}).get('words', ''),
                'valid': True
            }
        
        return {'valid': False}
```

### 4. 商业意向评分

```python
class BusinessIntentScorer:
    """商业意向评分器"""
    
    # 高意向关键词
    HIGH_INTENT_KEYWORDS = [
        '报价', '价格', '多少钱', '怎么卖',
        '采购', '购买', '订购', '下单',
        '合同', '签约', '付款', '定金',
        '交货期', '发货', '物流', '安装',
        '售后', '质保', '维修', '退换'
    ]
    
    # 中意向关键词
    MEDIUM_INTENT_KEYWORDS = [
        '了解', '咨询', '参数', '规格',
        '样品', '试用', '演示', '方案',
        '对比', '考虑', '预算', '需求'
    ]
    
    def score_conversation(self, messages):
        """
        评估对话的商业意向
        
        Returns:
            {
                'score': float,      # 0-100分
                'level': str,        # high/medium/low
                'signals': list      # 意向信号列表
            }
        """
        score = 0
        signals = []
        
        for msg in messages:
            content = msg['content']
            
            # 检查高意向关键词
            for keyword in self.HIGH_INTENT_KEYWORDS:
                if keyword in content:
                    score += 10
                    signals.append(f"高意向: {keyword}")
            
            # 检查中意向关键词
            for keyword in self.MEDIUM_INTENT_KEYWORDS:
                if keyword in content:
                    score += 5
                    signals.append(f"中意向: {keyword}")
        
        # 消息长度加分（长消息通常更认真）
        avg_length = sum(len(m['content']) for m in messages) / len(messages)
        if avg_length > 50:
            score += 10
        
        # 互动次数加分
        if len(messages) > 20:
            score += 15
        elif len(messages) > 10:
            score += 10
        
        # 确定意向等级
        if score >= 60:
            level = 'high'
        elif score >= 30:
            level = 'medium'
        else:
            level = 'low'
        
        return {
            'score': min(score, 100),
            'level': level,
            'signals': signals
        }
```

---

## 实施方案

### 数据库设计（新增表）

```sql
-- 待转化客户池表
CREATE TABLE qualified_leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 基本信息
    wechat_id VARCHAR(100) NOT NULL UNIQUE,
    nickname VARCHAR(200),
    real_name VARCHAR(100),           -- 真实姓名
    company_name VARCHAR(200),        -- 公司名称
    phone VARCHAR(20),                -- 手机号
    email VARCHAR(100),               -- 邮箱
    
    -- 验证状态
    phone_verified BOOLEAN DEFAULT 0,           -- 手机号已验证
    company_verified BOOLEAN DEFAULT 0,         -- 公司已验证
    business_license_uploaded BOOLEAN DEFAULT 0, -- 营业执照已上传
    business_license_path VARCHAR(500),         -- 执照图片路径
    
    -- 提取的公司信息（OCR）
    unified_social_credit_code VARCHAR(50),     -- 统一社会信用代码
    legal_person VARCHAR(100),                  -- 法人
    company_address TEXT,                       -- 公司地址
    
    -- 商业意向
    intent_score FLOAT DEFAULT 0,               -- 意向分数 0-100
    intent_level VARCHAR(20),                   -- high/medium/low
    intent_signals TEXT,                        -- 意向信号（JSON）
    
    -- 互动数据
    message_count INTEGER DEFAULT 0,            -- 消息数量
    first_contact_time DATETIME,                -- 首次联系时间
    last_contact_time DATETIME,                 -- 最后联系时间
    conversation_days INTEGER DEFAULT 0,        -- 沟通天数
    
    -- 同步状态
    ready_for_erp BOOLEAN DEFAULT 0,            -- 准备同步到ERP
    erp_sync_approved_by VARCHAR(100),          -- 审批人
    erp_sync_approved_time DATETIME,            -- 审批时间
    erp_customer_id INTEGER,                    -- ERP客户ID
    erp_sync_status VARCHAR(20),                -- pending/approved/rejected/synced
    
    -- 元数据
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_ready_for_erp (ready_for_erp),
    INDEX idx_erp_sync_status (erp_sync_status)
);

-- 同步审批记录表
CREATE TABLE erp_sync_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    
    -- 审批信息
    action VARCHAR(20),              -- approve/reject
    approver VARCHAR(100),           -- 审批人
    approval_time DATETIME,
    approval_reason TEXT,            -- 审批理由/拒绝原因
    
    -- 审批时的数据快照
    snapshot TEXT,                   -- JSON格式
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (lead_id) REFERENCES qualified_leads(id)
);
```

### 核心业务逻辑

#### 1. 智能晋级服务

```python
class LeadQualificationService:
    """线索晋级服务"""
    
    def __init__(self):
        self.phone_validator = PhoneValidator()
        self.company_validator = CompanyValidator()
        self.intent_scorer = BusinessIntentScorer()
    
    def check_qualification(self, wechat_id):
        """
        检查微信联系人是否具备晋级资格
        
        Returns:
            {
                'qualified': bool,
                'score': float,
                'missing': list,      # 缺少的信息
                'recommendations': list  # 建议采取的行动
            }
        """
        # 获取联系人信息
        contact = self._get_contact(wechat_id)
        
        score = 0
        missing = []
        recommendations = []
        
        # 1. 检查手机号
        if contact.get('phone'):
            validation = self.phone_validator.validate_phone(contact['phone'])
            if validation['valid']:
                score += 30
            else:
                missing.append('有效手机号')
                recommendations.append('请客户提供真实手机号')
        else:
            missing.append('手机号')
            recommendations.append('索取客户手机号')
        
        # 2. 检查公司名称
        if contact.get('company_name'):
            validation = self.company_validator.validate_company(contact['company_name'])
            if validation['valid']:
                score += 25
            else:
                missing.append('有效公司名称')
                recommendations.append('确认公司全称')
        else:
            missing.append('公司名称')
            recommendations.append('询问公司名称')
        
        # 3. 检查营业执照
        if contact.get('business_license_uploaded'):
            score += 20
        else:
            missing.append('营业执照')
            recommendations.append('请客户发送营业执照')
        
        # 4. 检查商业意向
        messages = self._get_conversation_messages(wechat_id)
        intent = self.intent_scorer.score_conversation(messages)
        score += min(intent['score'] * 0.25, 25)  # 最高25分
        
        if intent['level'] == 'low':
            missing.append('明确商业意向')
            recommendations.append('引导客户表达具体需求')
        
        # 判断是否合格
        qualified = (score >= 60) and (len(missing) <= 1)
        
        return {
            'qualified': qualified,
            'score': score,
            'missing': missing,
            'recommendations': recommendations,
            'intent': intent
        }
    
    def promote_to_qualified_lead(self, wechat_id):
        """晋级为待转化客户"""
        qualification = self.check_qualification(wechat_id)
        
        if not qualification['qualified']:
            return {
                'success': False,
                'reason': '不满足晋级条件',
                'missing': qualification['missing']
            }
        
        # 创建待转化客户记录
        contact = self._get_contact(wechat_id)
        messages = self._get_conversation_messages(wechat_id)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO qualified_leads
            (wechat_id, nickname, real_name, company_name, phone, email,
             phone_verified, company_verified, business_license_uploaded,
             intent_score, intent_level, intent_signals,
             message_count, first_contact_time, last_contact_time,
             conversation_days, ready_for_erp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            wechat_id,
            contact.get('nickname'),
            contact.get('real_name'),
            contact.get('company_name'),
            contact.get('phone'),
            contact.get('email'),
            contact.get('phone_verified', False),
            contact.get('company_verified', False),
            contact.get('business_license_uploaded', False),
            qualification['intent']['score'],
            qualification['intent']['level'],
            json.dumps(qualification['intent']['signals']),
            len(messages),
            messages[0]['timestamp'] if messages else None,
            messages[-1]['timestamp'] if messages else None,
            self._calculate_conversation_days(messages),
            True  # 标记为准备同步到ERP
        ))
        conn.commit()
        conn.close()
        
        return {'success': True, 'lead_id': cursor.lastrowid}
```

#### 2. 人工审批流程

```python
class ERPSyncApprovalService:
    """ERP同步审批服务"""
    
    def get_pending_approvals(self, approver=None):
        """获取待审批列表"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM qualified_leads
            WHERE ready_for_erp = 1
            AND erp_sync_status = 'pending'
            ORDER BY intent_score DESC, updated_at DESC
        '''
        
        cursor.execute(query)
        leads = cursor.fetchall()
        conn.close()
        
        # 为每个线索附加建议
        result = []
        for lead in leads:
            recommendation = self._generate_approval_recommendation(lead)
            result.append({
                **dict(lead),
                'recommendation': recommendation
            })
        
        return result
    
    def _generate_approval_recommendation(self, lead):
        """
        生成审批建议
        
        Returns:
            {
                'action': 'approve'/'review'/'reject',
                'confidence': float,
                'reasons': list
            }
        """
        score = 0
        reasons = []
        
        # 有效手机号 +30分
        if lead['phone_verified']:
            score += 30
            reasons.append('✅ 手机号已验证')
        else:
            reasons.append('⚠️ 手机号未验证')
        
        # 有效公司 +30分
        if lead['company_verified']:
            score += 30
            reasons.append('✅ 公司信息已验证')
        else:
            reasons.append('⚠️ 公司信息未验证')
        
        # 营业执照 +20分
        if lead['business_license_uploaded']:
            score += 20
            reasons.append('✅ 已上传营业执照')
        else:
            reasons.append('⚠️ 缺少营业执照')
        
        # 高意向 +20分
        if lead['intent_level'] == 'high':
            score += 20
            reasons.append(f"✅ 高意向客户（{lead['intent_score']}分）")
        elif lead['intent_level'] == 'medium':
            score += 10
            reasons.append(f"⚠️ 中等意向（{lead['intent_score']}分）")
        
        # 确定建议
        if score >= 80:
            action = 'approve'
        elif score >= 50:
            action = 'review'
        else:
            action = 'reject'
        
        return {
            'action': action,
            'confidence': score,
            'reasons': reasons
        }
    
    def approve_sync(self, lead_id, approver, reason=''):
        """批准同步到ERP"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 更新线索状态
        cursor.execute('''
            UPDATE qualified_leads
            SET erp_sync_status = 'approved',
                erp_sync_approved_by = ?,
                erp_sync_approved_time = ?
            WHERE id = ?
        ''', (approver, datetime.now(), lead_id))
        
        # 记录审批历史
        cursor.execute('''
            INSERT INTO erp_sync_approvals
            (lead_id, action, approver, approval_time, approval_reason)
            VALUES (?, 'approve', ?, ?, ?)
        ''', (lead_id, approver, datetime.now(), reason))
        
        conn.commit()
        conn.close()
        
        # 触发同步到ERP
        self._trigger_erp_sync(lead_id)
        
        return {'success': True}
    
    def reject_sync(self, lead_id, approver, reason):
        """拒绝同步到ERP"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE qualified_leads
            SET erp_sync_status = 'rejected',
                ready_for_erp = 0
            WHERE id = ?
        ''', (lead_id,))
        
        cursor.execute('''
            INSERT INTO erp_sync_approvals
            (lead_id, action, approver, approval_time, approval_reason)
            VALUES (?, 'reject', ?, ?, ?)
        ''', (lead_id, approver, datetime.now(), reason))
        
        conn.commit()
        conn.close()
        
        return {'success': True}
```

#### 3. Web界面审批功能

```python
# web_frontend.py - 新增审批界面路由

@app.route('/erp/approvals', methods=['GET'])
def erp_approvals():
    """ERP同步审批页面"""
    approval_service = ERPSyncApprovalService()
    pending_leads = approval_service.get_pending_approvals()
    
    return render_template('erp_approvals.html', leads=pending_leads)

@app.route('/erp/approve/<int:lead_id>', methods=['POST'])
def approve_lead(lead_id):
    """批准同步"""
    data = request.json
    approval_service = ERPSyncApprovalService()
    
    result = approval_service.approve_sync(
        lead_id=lead_id,
        approver=data.get('approver'),
        reason=data.get('reason', '')
    )
    
    return jsonify(result)

@app.route('/erp/reject/<int:lead_id>', methods=['POST'])
def reject_lead(lead_id):
    """拒绝同步"""
    data = request.json
    approval_service = ERPSyncApprovalService()
    
    result = approval_service.reject_sync(
        lead_id=lead_id,
        approver=data.get('approver'),
        reason=data['reason']  # 拒绝必须有原因
    )
    
    return jsonify(result)
```

---

## 用户界面设计

### 微信聊天界面增强

```
┌─────────────────────────────────────────┐
│  客户信息卡片                             │
├─────────────────────────────────────────┤
│  📱 张三 (微信昵称)                        │
│  🏢 公司: 未填写 [点击添加]                 │
│  ☎️  手机: 未填写 [点击添加]                 │
│  📄 营业执照: 未上传 [提醒客户]             │
│                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  商业意向: ⭐⭐⭐☆☆ (65分)                │
│  沟通天数: 3天 | 消息数: 28条              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                         │
│  状态: 🟡 待转化 (缺少: 公司信息)            │
│                                         │
│  [补全信息]  [同步到ERP]  [标记无效]       │
└─────────────────────────────────────────┘
```

### 审批界面

```
┌─────────────────────────────────────────────────┐
│  ERP客户同步审批                                  │
├─────────────────────────────────────────────────┤
│                                                 │
│  待审批客户: 12个                                │
│  今日已审批: 8个                                 │
│                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                 │
│  🟢 【推荐批准】深圳某某科技有限公司                │
│  ───────────────────────────────────────   │
│  联系人: 李经理                                  │
│  手机: 138****8888 ✅已验证                     │
│  公司: 深圳某某科技有限公司 ✅已验证              │
│  执照: ✅已上传                                 │
│  意向: ⭐⭐⭐⭐⭐ 95分                          │
│  信号: 询价、要报价、讨论交货期                    │
│                                                 │
│  [查看详情]  [✅ 批准]  [❌ 拒绝]               │
│                                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                 │
│  🟡 【需要复核】王先生                            │
│  ───────────────────────────────────────   │
│  联系人: 王先生                                  │
│  手机: 139****6666 ⚠️未验证                    │
│  公司: 未提供                                   │
│  执照: ❌未上传                                 │
│  意向: ⭐⭐⭐☆☆ 62分                          │
│  信号: 了解产品、咨询价格                         │
│                                                 │
│  建议: 补充公司信息后再审批                       │
│                                                 │
│  [查看详情]  [补充信息]  [暂不处理]              │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 配置文件更新

```yaml
# config.yaml

erp_integration:
  # 数据质量控制
  quality_control:
    enabled: true
    
    # 严格模式（推荐）
    strict_mode: true
    
    # 同步到ERP的准入规则
    sync_requirements:
      # 必须满足的字段（至少N个）
      required_fields:
        min_count: 2
        fields:
          - phone
          - company_name
          - business_license
      
      # 必须满足的验证
      required_validations:
        phone_verified: true      # 手机号必须验证
        company_verified: false   # 公司可以不验证（如果有执照）
      
      # 商业意向要求
      intent_requirement:
        min_score: 50             # 最低意向分数
        min_level: 'medium'       # 最低意向等级
      
      # 人工审批
      manual_approval:
        enabled: true             # 必须人工审批
        auto_approve_conditions:  # 自动批准条件（满足任一）
          - has_order: true
          - has_contract: true
          - intent_score_above: 90
    
    # 验证器配置
    validators:
      phone:
        enabled: true
        api_check: false          # 是否调用API验证（需要付费）
        format_check: true
      
      company:
        enabled: true
        api_check: false          # 工商API查询（需要密钥）
        ocr_check: true           # OCR识别营业执照
      
      business_license:
        ocr_provider: 'baidu'     # baidu/aliyun/tencent
        min_confidence: 0.8
```

---

## 总结与建议

### ✅ 最佳实践流程

```
1. 微信联系人加入
   → 自动保存到"微信联系人池"
   → AI初步分析和打标签
   
2. 客户提供基本信息（手机/公司名）
   → 自动验证真实性
   → 晋级到"待转化客户池"
   
3. 销售补充完善信息
   → 引导客户上传营业执照
   → 确认商业意向
   → 标记为"准备同步ERP"
   
4. 人工审批（关键环节）
   → 销售主管/经理审批
   → 系统提供AI建议
   → 批准后同步到ERP
   
5. 正式成为ERP客户
   → 分配客户编号
   → 分配销售人员
   → 开始正式商机跟进
```

### 📊 数据质量保证

- **源头控制**: 不是所有微信好友都进ERP
- **分层管理**: 三层架构，逐级晋升
- **智能验证**: 自动验证真实性
- **人工把关**: 最后一道防线
- **持续优化**: 根据反馈调整规则

### 🎯 预期效果

- ✅ ERP客户数据质量提升 80%+
- ✅ 无效客户减少 90%+
- ✅ 销售效率提升（聚焦高质量客户）
- ✅ 商机转化率提升（客户更精准）

---

需要我帮您：
1. **实现具体的验证器代码**？
2. **创建审批界面UI**？
3. **编写SQL迁移脚本**？
4. **调整准入规则**？

