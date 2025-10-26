# 智邦国际 ERP 常用 API 参数快速参考

> 基于智邦国际 ERP 32.17 版本  
> **注意**: 以下参数基于经验推测，实际使用时请以官方文档为准

---

## 📋 客户管理 API

### 获取客户列表

**端点**: `POST /webapi/v3/ov1/salesmanage/custom/list`

**请求参数**:

```json
{
  "pageindex": 1,              // 页码（从1开始）
  "pagesize": 20,              // 每页数量
  "keyword": "",               // 搜索关键词（客户名称/电话/备注）
  "sort": 0,                   // 客户类型: 0=全部, 1=单位客户, 2=个人客户
  "source": "",                // 客户来源（留空=全部）⭐
  "charge": "",                // 负责人ID（留空=全部）
  "starttime": "",             // 开始时间 "2025-01-01"
  "endtime": "",               // 结束时间 "2025-12-31"
  "status": ""                 // 状态: 0=待审核, 1=已审核, ""=全部
}
```

**响应字段**（推测）:

```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    "list": [
      {
        "id": "12345",                    // 客户ID
        "name": "张三公司",                // 客户名称（完整）
        "telname": "张三",                 // 客户简称
        "sort": 1,                         // 1=单位, 2=个人
        "source": "微信",                  // 客户来源 ⭐⭐⭐
        "linkman": "张经理",               // 联系人
        "tel": "13800138000",              // 电话
        "mobile": "13800138000",           // 手机
        "email": "zhang@example.com",      // 邮箱
        "address": "重庆市渝中区XX路",      // 地址
        "remark": "重要客户",               // 备注
        "charge": "1001",                  // 负责人ID
        "chargename": "李销售",            // 负责人姓名
        "addtime": "2025-01-01 10:00:00",  // 添加时间
        "lasttime": "2025-01-15 15:30:00", // 最后跟进时间
        "status": 1,                       // 0=待审核, 1=已审核
        "protect": 0,                      // 是否保护: 0=否, 1=是
        "level": "VIP",                    // 客户级别
        "industry": "制造业",              // 所属行业
        "scale": "100-500人",              // 企业规模
        "region": "重庆",                  // 所属区域
        "website": "www.example.com",      // 网址
        "fax": "",                         // 传真
        "zip": "400000"                    // 邮编
      }
    ],
    "total": 150,              // 总记录数
    "pageindex": 1,            // 当前页
    "pagesize": 20             // 每页数量
  }
}
```

---

### 添加客户

**端点**: `POST /webapi/v3/sales/customer/add`

**请求参数**（推测）:

```json
{
  "name": "张三公司",              // 客户名称（必填）
  "telname": "张三",               // 客户简称
  "sort": 1,                       // 1=单位客户, 2=个人客户（必填）
  "source": "微信",                // 客户来源 ⭐⭐⭐
  "linkman": "张经理",             // 联系人
  "tel": "13800138000",            // 电话
  "mobile": "13800138000",         // 手机
  "email": "zhang@example.com",    // 邮箱
  "address": "重庆市渝中区XX路",    // 地址
  "remark": "来自微信客户中台",     // 备注
  "charge": "1001",                // 负责人ID（当前用户ID）
  "level": "普通",                 // 客户级别
  "industry": "",                  // 所属行业
  "region": "重庆",                // 所属区域
  "k_code": "K3208",               // 自定义编码（可选）
  // 以下为扩展字段（根据系统配置）
  "field1": "",                    // 自定义字段1
  "field2": "",                    // 自定义字段2
  ...
}
```

**响应示例**:

```json
{
  "success": true,
  "message": "添加成功",
  "data": {
    "id": "12345"              // 新创建的客户ID
  }
}
```

---

### 获取客户详情

**端点**: `POST /webapi/v3/ov1/salesmanage/custom/add?edit=1&apihelptype=get`

**请求参数**:

```json
{
  "id": "12345"                // 客户ID
}
```

**响应**: 包含完整的客户信息（字段同"添加客户"）

---

## 🏷️ 客户来源字段详解

### 字段名: `source`

**可能的值**（基于智邦国际标准配置）:

| 值 | 说明 | 适用场景 |
|----|------|----------|
| `"微信"` | 微信渠道 | 客户中台同步 ⭐ |
| `"网络"` | 网站/在线咨询 | 官网表单提交 |
| `"电话"` | 电话咨询 | 400热线 |
| `"邮件"` | 邮件联系 | Email营销 |
| `"展会"` | 展会获取 | 线下活动 |
| `"老客户介绍"` | 转介绍 | 客户推荐 |
| `"线下拜访"` | 地推 | 销售外勤 |
| `"广告"` | 广告投放 | 百度/抖音广告 |
| `"其他"` | 其他渠道 | 未分类 |
| `""` | 空字符串 | 未填写 |

**注意**：
1. 客户来源通常是**系统预设的下拉选项**
2. 实际值需要在ERP系统中查看 `系统管理 → 客户来源设置`
3. 部分系统允许自定义来源名称

---

## 💡 如何确认实际字段名

### 方法1: 浏览器开发者工具（推荐）

1. 在ERP系统中手动添加一个客户
2. 打开开发者工具（F12）→ Network 标签
3. 提交表单
4. 查看提交的请求体（Request Payload）

**示例**:
```json
// 实际提交的数据
{
  "name": "测试客户",
  "source": "微信",     // ← 这就是字段名
  "tel": "13800138000"
}
```

### 方法2: API文档页面

访问并登录：
```
http://ls1.jmt.ink:46088/sysn/view/OpenApi/help.ashx
```

导航到：`销售栏目 → 客户管理 → 客户对接 → 获取客户列表`

查看参数表格。

---

## 📊 其他常用API参数

### 合同管理

**获取合同列表**: `POST /webapi/v3/ov1/salesmanage/contract/billlist`

```json
{
  "pageindex": 1,
  "pagesize": 20,
  "keyword": "",           // 合同编号/名称
  "custid": "",            // 客户ID
  "status": ""             // 合同状态
}
```

### 产品管理

**获取产品列表**: `POST /webapi/v3/ov1/salesmanage/product/billlist`

```json
{
  "pageindex": 1,
  "pagesize": 20,
  "keyword": "",           // 产品名称/编号
  "sortid": ""             // 产品分类ID
}
```

### 库存查询

**库存汇总**: `POST /webapi/v3/store/inventory/InventorySummary`

```json
{
  "pageindex": 1,
  "pagesize": 20,
  "productid": "",         // 产品ID
  "warehouseid": ""        // 仓库ID
}
```

---

## 🔗 Customer Hub 集成示例

### 建档后同步到ERP

```python
from customer_hub.service import CustomerHubService
import requests

def sync_contact_to_erp(contact_id: str):
    """将Customer Hub客户同步到ERP"""
    
    # 1. 从Customer Hub获取联系人
    hub = CustomerHubService()
    contact = hub.repo.get_contact_by_id(contact_id)
    
    if not contact:
        return False
    
    # 2. 映射字段
    erp_customer = {
        "name": contact.remark or contact.wx_id,
        "telname": contact.remark,
        "sort": 1,                    # 单位客户
        "source": "微信",              # 客户来源 ⭐
        "tel": "",                    # 从微信无法获取
        "remark": f"K编码: {contact.k_code}, 置信度: {contact.confidence}",
        "k_code": contact.k_code,     # 自定义字段（如果ERP支持）
    }
    
    # 3. 调用ERP API
    response = requests.post(
        'http://ls1.jmt.ink:46088/webapi/v3/sales/customer/add',
        headers={'Cookie': 'your_cookie'},
        json=erp_customer
    )
    
    if response.json().get('success'):
        erp_id = response.json()['data']['id']
        print(f"✅ 同步成功: ERP ID = {erp_id}")
        
        # 可以将 ERP ID 保存到 Contact 的扩展字段
        return True
    else:
        print(f"❌ 同步失败: {response.json().get('message')}")
        return False
```

---

## ⚠️ 重要提示

1. **以上参数为经验推测**
   - 实际字段名可能不同
   - 必填字段可能有差异
   - 数据类型需验证

2. **建议验证步骤**
   ```bash
   # 1. 在浏览器中查看官方文档
   # 2. 或实际调用API测试
   # 3. 根据错误提示调整参数
   ```

3. **字段名大小写**
   - 智邦国际通常使用**小写**字段名
   - 如 `pageindex` 而非 `pageIndex`
   - 部分新版API可能使用驼峰命名

4. **时间格式**
   - 通常为 `"YYYY-MM-DD"` 或 `"YYYY-MM-DD HH:mm:ss"`
   - 需要字符串格式，不是时间戳

---

## 🎯 针对您的问题：客户来源字段

**字段名**: `source`  
**数据类型**: String  
**用途**:
- 添加客户时: 指定来源
- 查询客户时: 按来源筛选
- 返回数据中: 显示客户来源

**推荐值**: `"微信"` （用于客户中台同步）

**验证方法**:
1. 在ERP系统中手动添加一个客户，填写来源为"微信"
2. 调用"获取客户列表"API
3. 查看返回的JSON中该客户的 `source` 字段值
4. 确认字段名和值格式

---

需要我帮您在浏览器中查看具体的参数文档吗？您可以：
1. 打开文档页面
2. 截图参数表格
3. 发给我，我帮您整理成完整的参数说明

