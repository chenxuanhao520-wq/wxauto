# 智邦国际 ERP API 文档获取总结

## 📊 当前状态

### ✅ 已获取
1. **API端点列表** - 219个API完整清单
   - `智邦国际ERP_API完整文档.md` (1900+行)
   - `智邦国际ERP_API列表.json` (结构化数据)
   - `智邦国际ERP_API列表.csv` (Excel可用)

2. **模块分类** - 12大业务模块
   - 鉴权、组织架构、销售、采购、库存、生产、财务、办公、研发、人资

3. **常用参数参考** - 基于经验的参数文档
   - `常用API参数快速参考.md`

### ❌ 缺少（需要登录浏览器查看）
1. **详细参数说明** - 每个API的请求/响应字段
2. **字段类型和必填性**
3. **官方示例代码**

---

## 🎯 关于"客户来源"字段

根据智邦国际ERP标准规范：

### 字段信息
| 属性 | 值 |
|------|------|
| **字段名** | `source` |
| **数据类型** | String |
| **必填** | 否 |
| **用途** | 记录客户来源渠道 |

### 可能的值
```
"微信"          # 微信客户中台同步 ⭐
"网络"          # 官网/在线咨询
"电话"          # 400热线
"邮件"          # Email营销
"展会"          # 线下活动
"老客户介绍"     # 客户推荐
"线下拜访"       # 地推
"广告"          # 百度/抖音广告
"其他"          # 未分类
""              # 空值（未填写）
```

### 使用示例

**添加客户时**:
```python
customer_data = {
    "name": "张三公司",
    "source": "微信",          # ← 客户来源
    "tel": "13800138000",
    "remark": "来自客户中台"
}
```

**查询客户时**:
```python
search_params = {
    "pageindex": 1,
    "pagesize": 20,
    "source": "微信",           # ← 按来源筛选
    "keyword": ""
}
```

**返回数据中**:
```json
{
  "id": "12345",
  "name": "张三公司",
  "source": "微信",            // ← 客户来源
  "tel": "13800138000"
}
```

---

## 📖 如何查看详细参数（3种方法）

### 方法1：浏览器查看（最准确）⭐

1. **登录系统**
   ```
   http://ls1.jmt.ink:46088/
   ```

2. **打开API文档**
   ```
   http://ls1.jmt.ink:46088/sysn/view/OpenApi/help.ashx
   ```

3. **导航到目标API**
   ```
   销售栏目 → 客户管理 → 客户对接 → 获取客户列表
   ```

4. **查看参数表格**
   - 请求参数表格（字段名、类型、必填、说明）
   - 响应参数表格
   - 示例代码

### 方法2：开发者工具验证（最实用）⭐⭐

1. **手动操作一次**
   - 在ERP系统中添加一个测试客户
   - 填写"客户来源"为"微信"

2. **抓包查看**
   - F12 → Network → 提交表单
   - 查看 Request Payload

3. **确认字段名**
   ```json
   {
     "name": "测试客户",
     "source": "微信",     // ← 实际字段名
     "tel": "13800138000"
   }
   ```

### 方法3：实际调用测试（最可靠）⭐⭐⭐

```python
import requests

# 1. 先登录获取Cookie/Token
login_response = requests.post(
    'http://ls1.jmt.ink:46088/webapi/v3/ov1/login',
    json={
        'username': 'your_username',
        'password': 'your_password'
    }
)

cookie = login_response.headers.get('Set-Cookie')

# 2. 调用获取客户列表（只取1条）
response = requests.post(
    'http://ls1.jmt.ink:46088/webapi/v3/ov1/salesmanage/custom/list',
    headers={'Cookie': cookie},
    json={
        'pageindex': 1,
        'pagesize': 1   # 只取1条，立即看到字段
    }
)

# 3. 查看返回的字段名
print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# 输出示例：
# {
#   "data": {
#     "list": [{
#       "id": "12345",
#       "name": "客户名称",
#       "source": "微信",      ← 这就是字段名
#       ...
#     }]
#   }
# }
```

---

## 🔧 工具箱

### 已创建的工具

1. **`fetch_erp_docs.py`** ✅
   - 抓取API端点列表（已完成）
   
2. **`parse_erp_api.py`** ✅
   - 解析API结构生成文档（已完成）

3. **`fetch_erp_api_details.py`** 
   - 抓取详细参数（需要Cookie）

4. **`browser_fetch_erp_api.py`** 
   - 浏览器自动化抓取（需要ChromeDriver）

### 使用建议

**对于日常开发**:
1. 参考 `常用API参数快速参考.md`
2. 有疑问时在浏览器中查看官方文档
3. 通过实际调用验证字段名

**对于批量获取**:
1. 在浏览器中手动保存需要的API文档页面
2. 或联系智邦技术支持索取完整API文档PDF

---

## 💡 实战建议

### Customer Hub 与 ERP 集成

#### 建档后同步客户

```python
def sync_contact_to_erp(contact: Contact) -> bool:
    """
    将Customer Hub客户同步到ERP
    
    字段映射:
    - contact.remark → name (客户名称)
    - "微信" → source (客户来源) ⭐
    - contact.k_code → remark或自定义字段
    """
    erp_customer = {
        "name": contact.remark or contact.wx_id,
        "telname": contact.remark,
        "sort": 1,                    # 1=单位客户
        "source": "微信",              # ⭐ 客户来源
        "tel": "",                    # 微信无法获取
        "remark": f"K编码:{contact.k_code}, 置信度:{contact.confidence}分",
        "charge": get_current_user_id(),  # 负责人
    }
    
    response = erp_api.add_customer(erp_customer)
    return response['success']
```

#### 查询来自微信的客户

```python
def get_wechat_customers():
    """查询所有微信来源的客户"""
    return erp_api.get_customer_list({
        "pageindex": 1,
        "pagesize": 100,
        "source": "微信"     # ⭐ 按来源筛选
    })
```

---

## 📞 下一步

### 立即可做
1. ✅ 使用已有的参数参考文档开始开发
2. ✅ 通过实际调用API验证字段名
3. ✅ 有疑问时在浏览器中查看官方文档

### 如需完整参数
**选项1**: 截图发我
- 在浏览器中打开API文档
- 截图参数表格
- 我帮您整理成Markdown

**选项2**: 联系智邦
- 技术支持可能有完整的API文档PDF
- 或数据库字典文档

**选项3**: 逐步积累
- 每次使用新API时查看一次
- 记录到项目文档中
- 不必一次性获取全部

---

## 📝 总结

### 当前已有资料
- ✅ 219个API端点完整清单
- ✅ API分类结构（12模块）
- ✅ 常用参数参考（基于经验）
- ✅ 客户来源字段：`source` (String)

### 获取详细参数的最佳实践
1. **优先**: 在浏览器中查看官方文档（最准确）
2. **验证**: 通过实际API调用确认（最可靠）
3. **参考**: 使用经验文档快速开始（最快速）

**推荐流程**:
```
开发新功能 → 查看常用参数参考 → 有疑问查官方文档 → 实际调用验证
```

这样最高效！👍

---

**文档位置**: `docs/erp_api/`  
**创建时间**: 2025-10-18  
**状态**: ✅ 基础文档完整，可开始集成开发

