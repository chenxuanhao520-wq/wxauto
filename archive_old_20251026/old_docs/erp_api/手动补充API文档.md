# 智邦国际ERP API手动补充文档

**处理时间**: 2025-10-19 12:20:43  
**API数量**: 1  
**数据来源**: 手动提取和整理

---

## 获取客户详情

**调用方式**: POST  
**接口地址**: `/sysa/mobilephone/salesmanage/custom/add.asp?edit=1`  
**请求类型**: application/json  

### 请求参数

| 字段名称 | 类型 | 必填 | 描述 |
|----------|------|------|------|
| edit | string | 否 | 修改模式，是否返回修改模式的数据，默认为空，二次开发时无用 |
| intsort | string | 否 | 客户类型，1: 单位客户、2: 个人客户，该参数也可在URL中定义 |
| ord | int | 否 | 数据唯一标识，整数，泛指当前单据的数据标识值，如客户ID、合同ID等等，可从相应的列表接口获取该值 |
| _insert_rowindex | string | 否 |  |
| debug | string | 否 |  |

### Python调用示例

```python
import json
import requests

# 收集请求数据
dats = {
    "edit": "",          # 修改模式
    "intsort": "",       # 客户类型
    "ord": 0,            # 数据唯一标识
    "_insert_rowindex": "",
    "debug": ""
}

# 注：本接口采用V1.0版本方式传参, 参数采用的是id-val键值对数组形式
datas = [{"id": key, "val": value} for key, value in dats.items()]
json_data = {
    "session": "******",  # 当接口设置开启了token验证，此字段传鉴权接口返回的Session
    "datas": datas
}

# 执行网络请求
url = "http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/add.asp?edit=1"
headers = {"Content-Type": "application/json"}
response = requests.post(url, json=json_data, headers=headers)
result = response.text
print(result)
```

### 返回结果

接口返回结果统一为ZBDocument类型，该类型包含【接口状态】+【实际业务】两部分。在本接口中，实际业务数据类型为BillClass（单据对象）。

#### BillClass字段说明

| 字段名称 | 数据类型 | 详细说明 |
|----------|----------|----------|
| id | String | 单据类型的Id，一般二次开发扩展用，无实际业务含义 |
| caption | String | 当前单据的标题 |
| uitype | String | UI属性：单据UI标记 |
| value | String | 数据唯一标识，泛指当前单据的数据标识ID值，如客户ID、合同ID等等 |
| tools | ASPCollection | UI属性：当前单据前端操作功能集合，二次开发无用 |
| groups | ASPCollection | 单据所包含的字段组集合 |

---

