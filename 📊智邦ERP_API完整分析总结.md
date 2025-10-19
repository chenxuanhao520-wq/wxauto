# 智邦国际ERP API完整分析总结

**生成日期**: 2025-10-19  
**文档版本**: v1.0  
**API数量**: 158个完整接口  

---

## 📋 文档清单

本次整理已生成以下完整文档：

### 📖 核心文档

1. **[智邦ERP_API完整分析报告.md](./docs/erp_api/智邦ERP_API完整分析报告.md)**  
   - 158个API的完整分析
   - 对接场景详解
   - 完整代码示例
   - 字段映射表
   - 同步策略建议
   
2. **[微信中台ERP对接指南.md](./docs/erp_api/微信中台ERP对接指南.md)**  
   - 4大核心对接场景
   - 数据映射表
   - 同步策略和冲突解决

3. **[API快速参考表.md](./docs/erp_api/API快速参考表.md)**  
   - 158个API的快速索引表
   - 包含：API名称、接口地址、请求方式、分类

### 🔧 技术文档

4. **[销售栏目客户管理客户.md](./docs/erp_api/销售栏目客户管理客户.md)**  
   - 19个客户管理API详细说明
   - 包含：请求参数、响应参数、示例代码

5. **[智邦ERP_API完整索引.md](./docs/erp_api/智邦ERP_API完整索引.md)**  
   - 按模块分类的完整索引
   - 41个分类，158个API

6. **[智邦ERP_API完整数据.json](./docs/erp_api/智邦ERP_API完整数据.json)**  
   - 所有API的JSON格式数据
   - 便于程序化处理

### 💻 代码文件

7. **[zhibang_client_enhanced.py](./erp_sync/zhibang_client_enhanced.py)**  
   - 增强版Python SDK
   - 包含完整的客户管理、联系人管理、跟进记录等功能
   - 自动认证、错误重试、会话管理
   - 高级方法：`sync_customer_from_wechat()`

---

## 🎯 核心API速查

### 客户管理 (19个API)

| API名称 | 接口路径 | 用途 |
|---------|---------|------|
| 分配新客户ID | `/sysa/mobilephone/salesmanage/custom/add.asp` | 获取新客户唯一标识 |
| 单位客户添加 | `/sysa/mobilephone/salesmanage/custom/add.asp?intsort=1` | 添加企业客户 |
| 个人客户添加 | `/sysa/mobilephone/salesmanage/custom/add.asp?intsort=2` | 添加个人客户 |
| 客户列表 | `/sysa/mobilephone/salesmanage/custom/list.asp` | 查询客户，支持分页和筛选 |
| 客户详情 | `/sysa/mobilephone/salesmanage/custom/add.asp?edit=1` | 获取客户完整信息 |
| 客户修改 | `/webapi/v3/sales/customer/edit` | 更新客户资料 |
| 客户指派 | `/sysa/mobilephone/systemmanage/order.asp?datatype=tel` | 分配客户给销售 |
| 洽谈进展 | `/sysa/mobilephone/systemmanage/reply.asp?datatype=tel` | 添加跟进记录 |

### 联系人管理 (6个API)

| API名称 | 接口路径 | 用途 |
|---------|---------|------|
| 联系人添加 | `/sysa/mobilephone/salesmanage/person/add.asp` | 为客户添加联系人 |
| 联系人列表 | `/sysa/mobilephone/salesmanage/person/list.asp` | 查询联系人 |
| 联系人详情 | `/sysa/mobilephone/salesmanage/person/add.asp?edit=1` | 获取联系人信息 |

---

## 🔑 关键字段说明

### 客户来源字段 (ly)

**用途**: 标记客户来自哪个渠道

**可选值**:
- `171`: 网站注册 ⭐ **推荐用于微信渠道**
- `173`: 陌生开发
- `172`: 朋友介绍
- `174`: 广告宣传
- `977`: VIP

**使用建议**: 统一使用 `171` 标记所有来自微信中台的客户

---

### 客户编号字段 (khid)

**用途**: 客户的唯一标识符

**推荐格式**: `WX{中台客户ID}`

**示例**:
- 中台客户ID = 12345 → ERP客户编号 = `WX12345`
- 便于追溯客户来源
- 支持去重检查

---

### 价值评估字段 (jz)

**用途**: 评估客户价值等级

**映射规则**:

| 中台评分 | ERP价值评估值 | 说明 |
|---------|-------------|------|
| 90-100 | 175 | 很高 |
| 75-89 | 289 | 较高 |
| 60-74 | 176 | 一般 |
| 45-59 | 177 | 较低 |
| 0-44 | 290 | 很低 |

---

### 必填字段总结

**单位客户必填**:
- `ord`: 客户ID（通过"分配新客户ID"接口获取）
- `name`: 客户名称
- `sort1`: 客户分类（如"微信客户"）
- `person_name`: 联系人姓名

**个人客户必填**:
- `ord`: 客户ID
- `name`: 客户名称
- `sort1`: 客户分类

---

## 💡 快速对接示例

### 场景1: 同步单个客户到ERP

```python
from erp_sync.zhibang_client_enhanced import ZhibangERPClient

# 初始化客户端
client = ZhibangERPClient(
    base_url='http://ls1.jmt.ink:46088',
    username='your_username',
    password='your_password'
)

# 微信中台客户数据
contact = {
    'id': 12345,
    'type': 'company',
    'name': '张三',
    'company': '某某科技有限公司',
    'phone': '13800138000',
    'wechat_id': 'zhangsan_wx',
    'address': '北京市朝阳区xxx',
    'email': 'zhangsan@example.com'
}

# 对话线程数据
thread = {
    'score': 85,
    'summary': '客户对我们的产品很感兴趣，准备下周面谈'
}

# 同步到ERP
result = client.sync_customer_from_wechat(contact, thread)

print(f"同步结果: {result['status']}")
if result['status'] == 'success':
    print(f"ERP客户ID: {result['customer_id']}")
    print(f"客户编号: {result['khid']}")
```

---

### 场景2: 添加跟进记录

```python
# 查找客户
customer = client.find_customer_by_khid('WX12345')

if customer:
    # 添加跟进记录
    client.add_followup_record(
        customer_id=customer['ord'],
        template_id=106,  # 谈的很好，让发合同
        content='客户对产品非常满意，已发送报价单，等待回复'
    )
    print("✅ 跟进记录已添加")
```

---

### 场景3: 自动分配客户给销售

```python
# 根据评分自动分配
if thread['score'] >= 80:
    # 高分客户分配给金牌销售（假设ID为123）
    client.assign_customer(
        customer_id=customer['ord'],
        assign_type=0,  # 指派给特定用户
        user_ids='123'
    )
    print("✅ 已分配给金牌销售")
elif thread['score'] >= 60:
    # 中等客户分配给一般销售（假设ID为456）
    client.assign_customer(
        customer_id=customer['ord'],
        assign_type=0,
        user_ids='456'
    )
    print("✅ 已分配给销售")
else:
    # 低分客户放入公海
    client.assign_customer(
        customer_id=customer['ord'],
        assign_type=1,  # 对所有用户公开
        user_ids=''
    )
    print("✅ 已放入公海")
```

---

### 场景4: 批量查询客户

```python
# 查询所有来自微信的客户
customers = client.get_customer_list(
    page_size=100,
    page_index=1,
    filters={
        'ly': '171',  # 客户来源=网站注册（微信）
        '_rpt_sort': '-date1'  # 按添加时间倒序
    }
)

print(f"找到 {len(customers)} 个微信客户")
for cust in customers:
    print(f"  - {cust['name']} ({cust['khid']}) - {cust['mobile']}")
```

---

## ✅ 数据准入检查

在同步到ERP之前，建议进行以下检查：

```python
def check_admission(contact):
    """检查客户是否满足同步条件"""
    checks = {
        'has_mobile': bool(contact.get('phone') and len(contact.get('phone')) == 11),
        'has_name': bool(contact.get('name') and len(contact.get('name')) > 0),
        'has_company': bool(contact.get('company')) if contact.get('type') == 'company' else True,
        'phone_verified': contact.get('phone_verified', False),
        'score_pass': contact.get('score', 0) >= 60,
    }
    
    passed = all(checks.values())
    
    return {
        'passed': passed,
        'checks': checks,
        'reason': [k for k, v in checks.items() if not v] if not passed else []
    }

# 使用示例
admission = check_admission(contact)
if admission['passed']:
    result = client.sync_customer_from_wechat(contact, thread)
else:
    print(f"❌ 不满足准入条件: {admission['reason']}")
```

---

## 🔒 安全建议

### 1. 账号权限

- ✅ 创建专门的API账号
- ✅ 仅授予"客户管理"权限
- ❌ 不要使用超级管理员账号
- ❌ 禁止访问财务、库存等敏感模块

### 2. 数据保护

```python
# 脱敏处理
def mask_sensitive_data(customer):
    """脱敏敏感信息"""
    if customer.get('mobile'):
        customer['mobile'] = customer['mobile'][:3] + '****' + customer['mobile'][-4:]
    if customer.get('bank_3'):
        customer['bank_3'] = '****' + customer['bank_3'][-4:]
    return customer

# 在日志中使用脱敏数据
logger.info(f"同步客户: {mask_sensitive_data(customer)}")
```

### 3. 操作日志

```python
# 记录所有ERP操作
def log_operation(operation, data, result):
    db.session.add(ERPOperationLog(
        timestamp=datetime.now(),
        operation=operation,
        request_data=json.dumps(data),
        response_data=json.dumps(result),
        user=current_user.username
    ))
    db.session.commit()
```

---

## 📈 监控指标

建议监控以下指标：

| 指标 | 说明 | 告警阈值 |
|------|------|---------|
| 同步成功率 | 成功/总数 | < 80% |
| API响应时间 | 平均响应时长 | > 5秒 |
| 失败次数 | 1小时内失败数 | > 10次 |
| 重复客户数 | 客户编号冲突 | > 5个/天 |
| 会话过期次数 | 需要重新登录 | > 3次/小时 |

---

## 🚀 部署步骤

### 1. 安装依赖

```bash
cd "/Users/chenxuanhao/Desktop/wx au to/wxauto-1"
pip3 install requests pyyaml
```

### 2. 配置ERP连接信息

编辑 `config.yaml`:

```yaml
erp_integration:
  base_url: "http://ls1.jmt.ink:46088"
  username: "your_username"
  password: "your_password"
  
  # 同步配置
  sync:
    enabled: true
    auto_sync: true
    score_threshold: 60  # 最低评分要求
    
  # 字段映射
  customer_source_id: 171  # 客户来源：网站注册（代表微信）
  customer_category: "微信客户"  # 客户分类
```

### 3. 测试连接

```bash
python3 << 'EOF'
from erp_sync.zhibang_client_enhanced import ZhibangERPClient
import yaml

# 读取配置
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 创建客户端
erp_config = config['erp_integration']
client = ZhibangERPClient(
    base_url=erp_config['base_url'],
    username=erp_config['username'],
    password=erp_config['password']
)

print("✅ 连接成功!")
print(f"Session: {client.session[:30]}...")

# 测试获取客户列表
customers = client.get_customer_list(page_size=5)
print(f"📋 客户数量: {len(customers)}")
EOF
```

### 4. 启动同步服务

```bash
# 方式1: 手动同步
python3 -c "from erp_sync.sync_service import sync_customers; sync_customers()"

# 方式2: 定时同步（使用crontab）
# 每小时执行一次
# 0 * * * * cd /path/to/project && python3 -c "from erp_sync.sync_service import sync_customers; sync_customers()"
```

---

## 📞 联系支持

如有问题，请参考：

1. **API文档**: `docs/erp_api/` 目录下的完整文档
2. **代码示例**: `erp_sync/zhibang_client_enhanced.py` 中的完整实现
3. **对接指南**: `docs/erp_api/微信中台ERP对接指南.md`

---

## 🎉 总结

### ✅ 已完成

- [x] 解析158个API接口完整文档
- [x] 生成分类文档（41个模块）
- [x] 创建Python SDK（增强版）
- [x] 提供完整对接指南
- [x] 建立字段映射表
- [x] 编写示例代码
- [x] 制定同步策略
- [x] 提供安全建议

### 🎯 核心价值

1. **客户来源标记**: 使用 `ly=171` 统一标记微信客户
2. **唯一标识**: `WX{中台ID}` 格式的客户编号
3. **智能评估**: 评分自动映射到ERP价值等级
4. **完整API**: 158个接口全部解析完毕
5. **即用SDK**: Python客户端开箱即用

### 📦 交付物

- 6份完整文档
- 1个增强版SDK
- 1份JSON数据
- 完整代码示例
- 部署指南

---

**生成时间**: 2025-10-19 12:43:10  
**文档版本**: v1.0  
**状态**: ✅ 完成

