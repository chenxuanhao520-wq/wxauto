# 智邦国际ERP - 客户管理API详细文档

**版本**: v1.0  
**生成时间**: 2025-10-18  
**基础地址**: `http://ls1.jmt.ink:46088`  
**文档说明**: 本文档包含完整的客户管理相关API接口说明，包括详细的请求参数、返回结果和Python调用示例。

---

## 目录

1. [对接须知](#对接须知)
2. [鉴权接口](#鉴权接口)
3. [客户管理](#客户管理)
4. [联系人管理](#联系人管理)
5. [通用数据类型](#通用数据类型)

---

## 对接须知

### 一、接口对接前注意事项

1. **OpenAPI接口面向智邦ERP成交客户**
2. **大多数接口都需要验证身份信息**，应当先调用登录接口获取到身份信息之后再调用其他接口
3. **所有的请求和响应数据编码皆为utf-8格式**

### 二、开发流程介绍

1. 首先了解智邦软件中手动添加单据的步骤
2. 熟悉智邦接口文档中各字段的含义
3. 了解第三方系统跟智邦接口文档中各字段的映射关系
4. 当调用过程中遇到字段含义不明确、调用方法不清楚，可通过售后渠道联系我司技术人员协助指导

---

## 鉴权接口

### 系统登录接口

**调用方式**: HTTP | POST  
**接口地址**: `http://ls1.jmt.ink:46088/webapi/v3/ov1/login`  
**请求类型**: application/json

#### 请求参数

| 字段名称 | 类型 | 必填 | 描述 |
|---------|------|------|------|
| user | string | 是 | 用户名，文本，必填，支持des加密和明文，如果是明文，内容需要加前缀txt: |
| password | string | 是 | 用户名密码，文本，必填，支持des加密和明文，如果是明文，内容需要加前缀txt: |
| serialnum | string | 是 | 用户串号，文本，必填，20位以内数字或字母随机组合即可 |
| rndcode | string | 否 | 随机验证码，文本，只有用户名和密码失败次数超过3次才会需要输入，否则无需提交该参数 |

#### Python请求范例

```python
import json
import requests

# 收集请求数据
dats = {
    "user": "txt:admin",      # 用户名
    "password": "txt:123456",  # 用户名密码
    "serialnum": "txt:abcd1234",  # 用户串号
    "rndcode": ""              # 随机验证码
}

# 注：本接口采用V1.0版本方式传参, 参数采用的是id-val键值对数组形式
datas = [{"id": key, "val": value} for key, value in dats.items()]
json_data = {"datas": datas}

# 执行网络请求
url = "http://ls1.jmt.ink:46088/sysa/mobilephone/login.asp"
headers = {"Content-Type": "application/json"}
response = requests.post(url, json=json_data, headers=headers)
result = response.text
print(result)
```

#### 输出参数

| 字段名称 | 类型 | 描述 |
|---------|------|------|
| header | object | 信息头对象 |
| status | int | 登陆状态 0=成功 其他=失败 |
| session | string | 会话状态信息, 即Token值 |
| appversion | string | 当前系统版本, 例如: 32.17 |

#### JSON返回示例

```json
{
  "header": {
    "status": 0,
    "message": "API鉴权成功.",
    "session": "..........................",
    "appversion": "32.17"
  }
}
```

---

### 退出系统

**调用方式**: HTTP | POST  
**接口地址**: `http://ls1.jmt.ink:46088/sysa/mobilephone/logout.asp`  
**请求类型**: application/json

#### 请求参数

无特定参数，只需要传session

#### Python请求范例

```python
{
  "session": "******",  # 当接口设置开启了token验证，此字段传鉴权接口返回的Session
  "datas": []
}
```

#### 返回结果

返回 **MessageClass** 类型，包含退出操作的执行结果。

---

## 客户管理

### 1. 分配新客户ID

**调用方式**: HTTP | POST  
**接口地址**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/add.asp`  
**请求类型**: application/json

#### 请求参数

| 字段名称 | 类型 | 必填 | 描述 |
|---------|------|------|------|
| edit | string | 否 | 修改模式，是否返回修改模式的数据，默认为空，二次开发时无用 |
| intsort | string | 否 | 客户类型，1: 单位客户、2: 个人客户，该参数也可在URL中定义 |

#### 请求范例

```json
{
  "session": "******",
  "datas": [
    {"id": "edit", "val": ""},
    {"id": "intsort", "val": ""}
  ]
}
```

#### 返回结果

返回 **BillClass** 类型，包含新分配的客户ID。

---

### 2. 单位客户添加

**调用方式**: HTTP | POST  
**接口地址**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/add.asp?intsort=1`  
**请求类型**: application/json

#### 请求参数（单位客户）

| 字段名称 | 类型 | 必填 | 描述 |
|---------|------|------|------|
| ord | int | 否 | 数据唯一标识，添加新客户需要传【分配新客户ID】接口返回的标识值，修改客户资料时传已经存在的客户资料标识 |
| name | string | 是 | 客户名称，必填，100字以内 |
| pym | string | 否 | 拼音码，200字以内 |
| khid | string | 否 | 客户编号，50字以内 |
| sort1 | string | 是 | 客户分类，必填，50字以内，来自树结构数据 |
| ly | int | 否 | **客户来源**，整型，枚举类型<br>如：173:陌生开发、171:网站注册、977:VIP、174:广告宣传、172:朋友介绍<br>**来自接口**: `/mobilephone/source.asp?enumid=13` |
| jf2 | int | 否 | 是否积分，整型，枚举类型，如：1:积分、0:不积分 |
| area | string | 否 | 客户区域，**来自接口**: `mobilephone/systemmanage/area_list.asp?stype=radio` |
| trade | int | 否 | 客户行业，整型，枚举类型<br>如：139:印刷、137:银行、968:电表、967:交流接触器、966:防水头<br>**来自接口**: `/mobilephone/source.asp?enumid=11` |
| jz | int | 否 | 价值评估，整型，枚举类型<br>如：175:很高、289:较高、176:一般、177:较低、290:很低<br>**来自接口**: `/mobilephone/source.asp?enumid=14` |
| credit | string | 否 | 信用等级，50字以内 |
| url | string | 否 | 客户网址，100字以内 |
| bz | string | 否 | 客户币种，50字以内，枚举类型，如：14:人民币 |
| hk_xz | decimal | 否 | 到款限制，数字 |
| address | string | 否 | 客户地址，200字以内 |
| lng | string | 否 | 经度，50字以内 |
| lat | string | 否 | 纬度，50字以内 |
| zip | string | 否 | 邮编，10字以内 |
| faren | string | 否 | 法人代表，50字以内 |
| zijin | decimal | 否 | 注册资本，数字 |
| pernum1 | int | 否 | 人员数量-销售，整型 |
| pernum2 | int | 否 | 人员数量-技术，整型 |
| date1 | datetime | 否 | 添加时间，日期 |
| person_name | string | 是 | 联系人姓名，必填，50字以内 |
| @personpym | string | 否 | 拼音码，50字以内 |
| sex | int | 否 | 性别，整型，枚举类型，如：男:男、女:女 |
| age | int | 否 | 年龄，整型 |
| year1 | datetime | 否 | 生日，日期 |
| part1 | string | 否 | 部门，50字以内 |
| job | string | 否 | 职务，50字以内 |
| phone | string | 否 | 办公电话，50字以内 |
| fax | string | 否 | 传真，50字以内 |
| mobile | string | 否 | 手机，50字以内 |
| phone2 | string | 否 | 家庭电话，50字以内 |
| email | string | 否 | 电子邮件，50字以内 |
| qq | string | 否 | QQ，20字以内 |
| weixinAcc | string | 否 | 微信，50字以内 |
| XiQueIntro | string | 否 | 喜鹊声声，50字以内 |
| msn | string | 否 | MSN，50字以内 |
| jg | string | 否 | 籍贯，50字以内 |
| product | string | 否 | 客户简介，4000字以内 |
| c2 | string | 否 | 合作现状，4000字以内 |
| c3 | string | 否 | 合作前景，4000字以内 |
| c4 | string | 否 | 跟进策略，4000字以内 |
| intro | string | 否 | 备注，4000字以内 |
| bank_1 | string | 否 | 开户银行1，50字以内 |
| bank_2 | string | 否 | 开户名称1，50字以内 |
| bank_7 | string | 否 | 银行行号1，50字以内 |
| bank_3 | string | 否 | 银行账号1，50字以内 |
| bank_4 | string | 否 | 税号1，50字以内 |
| bank_5 | string | 否 | 地址1，50字以内 |
| bank_6 | string | 否 | 电话1，50字以内 |
| bank2_1 | string | 否 | 开户银行2，50字以内 |
| bank2_2 | string | 否 | 开户名称2，50字以内 |
| bank2_7 | string | 否 | 银行行号2，50字以内 |
| bank2_3 | string | 否 | 银行账号2，50字以内 |
| bank2_4 | string | 否 | 税号2，50字以内 |
| bank2_5 | string | 否 | 地址2，50字以内 |
| bank2_6 | string | 否 | 电话2，50字以内 |
| fkdays | int | 否 | 账期，整型 |
| fkdate | int | 否 | 结算日期，整型，枚举类型，如：1:1、2:2、3:3、4:4、5:5 |

#### 返回结果

返回 **MessageClass** 类型，包含保存操作的执行结果。

---

### 3. 个人客户添加

**调用方式**: HTTP | POST  
**接口地址**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/add.asp?intsort=2`  
**请求类型**: application/json

#### 请求参数（个人客户）

个人客户参数与单位客户类似，主要区别：
- 没有 `faren`（法人代表）、`zijin`（注册资本）、`pernum1`、`pernum2`等单位客户特有字段
- 没有 `person_name`、`@personpym` 等联系人字段（因为个人客户本身就是联系人）
- `faren` 字段在个人客户中表示"所在单位"

---

### 4. 客户详情

**调用方式**: HTTP | POST  
**接口地址**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/add.asp?edit=1`  
**请求类型**: application/json

#### 请求参数

| 字段名称 | 类型 | 必填 | 描述 |
|---------|------|------|------|
| edit | string | 否 | 修改模式，是否返回修改模式的数据，默认为空，二次开发时无用 |
| intsort | string | 否 | 客户类型，1: 单位客户、2: 个人客户，该参数也可在URL中定义 |
| ord | int | 否 | 数据唯一标识，整数，泛指当前单据的数据标识值，如客户ID、合同ID等等，可从相应的列表接口获取该值 |
| _insert_rowindex | string | 否 |  |
| debug | string | 否 |  |

#### Python请求范例

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

#### 返回结果

返回 **BillClass** 类型，包含客户的详细信息。

**BillClass字段说明**:

| 字段名称 | 数据类型 | 详细说明 |
|---------|----------|----------|
| id | String | 单据类型的Id，一般二次开发扩展用，无实际业务含义 |
| caption | String | 当前单据的标题 |
| uitype | String | UI属性：单据UI标记 |
| value | String | 数据唯一标识，泛指当前单据的数据标识ID值，如客户ID、合同ID等等 |
| tools | ASPCollection | UI属性：当前单据前端操作功能集合，二次开发无用 |
| groups | ASPCollection | 单据所包含的字段组集合 |

---

### 5. 客户列表

**调用方式**: HTTP | POST  
**接口地址**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/list.asp`  
**请求类型**: application/json

#### 请求参数

| 字段名称 | 类型 | 必填 | 描述 |
|---------|------|------|------|
| datatype | string | 否 | 列表模式，默认为空:全部，addcontract：添加合同选择客户模式 |
| stype | string | 否 | 数据模式，默认为空:客户列表，1：客户池，2：待审核客户，3：已保护客户，4：已共享客户，5：被共享客户 |
| remind | int | 否 | 提醒类型，整型，147：最新客户 |
| **tjly** | **string** | **否** | **统计来源（即客户来源字段）** |
| tdate1 | string | 否 | 领用开始日期 |
| tdate2 | string | 否 | 领用结束日期 |
| checktype | string | 否 | 关联客户选择模式，radio 单选 |
| telsort | string | 否 | 客户分类 |
| Ismode | string | 否 | 供应商总览标识 |
| a_cateid | string | 否 | 销售人员 |
| khjz | string | 否 | 客户价值评估 |
| khhy | string | 否 | 客户行业 |
| khly | string | 否 | 客户来源 |
| a_date_0 | string | 否 | 添加开始日期 |
| a_date_1 | string | 否 | 添加结束日期 |
| telord | string | 否 | 客户id |
| name | string | 否 | 客户名称，文本，默认为空，模糊检索条件 |
| pym | string | 否 | 拼音码，文本，默认为空，模糊检索条件 |
| khid | string | 否 | 客户编号，文本，默认为空，模糊检索条件 |
| phone | string | 否 | 办公电话，文本，默认为空，模糊检索条件 |
| fax | string | 否 | 传真，文本，默认为空，模糊检索条件 |
| url | string | 否 | 客户网址，文本，默认为空，模糊检索条件 |
| catetype | int | 否 | 人员类型，整数，枚举类型：领用人员=1;放弃人员=2;添加人员=3;添加人员和领用人员=4;添加人员和放弃人员=5;保护人员=6;未保护人员=7 |
| cateid | string | 否 | 人员选择，文本，多选项检索条件，多个值之间用逗号隔开<br>**枚举数据接口**: `/mobilephone/systemManage/gate_list.asp?stype=check` |
| ly | string | 否 | 客户来源，文本，多选项检索条件，多个值之间用逗号隔开<br>**枚举数据接口**: `/mobilephone/source.asp?enumid=13` |
| jz | string | 否 | 价值评估，文本，多选项检索条件，多个值之间用逗号隔开<br>**枚举数据接口**: `/mobilephone/source.asp?enumid=14` |
| area | string | 否 | 客户区域，文本，多选项检索条件，多个值之间用逗号隔开<br>**枚举数据接口**: `/mobilephone/systemManage/area_list.asp?stype=check` |
| trade | string | 否 | 客户行业，文本，多选项检索条件，多个值之间用逗号隔开<br>**枚举数据接口**: `/mobilephone/source.asp?enumid=11` |
| address | string | 否 | 客户地址，文本，默认为空，模糊检索条件 |
| zip | string | 否 | 邮编，文本，默认为空，模糊检索条件 |
| intro | string | 否 | 备注，文本，默认为空，模糊检索条件 |
| date1_0 | string | 否 | 添加时间，文本，默认为空，日期段检索条件（起始日期） |
| date1_1 | string | 否 | 添加时间，文本，默认为空，日期段检索条件（截止日期） |
| searchKey | string | 否 | 快速检索条件，文本，对返回列表中所有文本列进行匹配筛选，默认为空 |
| pagesize | int | 否 | 每页记录数，整型，列表分页参数，默认为空，则每页显示20条记录 |
| pageindex | int | 否 | 数据页标，整型，列表分页参数，表示返回第几页数据，默认为空，则返回第1页数据 |
| _rpt_sort | string | 否 | 排序字段，文本，列表排序条件，内容为列名称，该内容前加负号表示倒序，不加表示正序 |

#### 返回结果

返回 **SourceClass** 类型，包含表格型数据。

**SourceClass字段说明**:

| 字段名称 | 数据类型 | 详细说明 |
|---------|----------|----------|
| type_ | String | 数据源的类型，不同的类型对应不同格式的数据 |
| table | tableClass对象 | 数据源表格对象，当type_属性为table时，该对象有值 |
| uitype | String | UI属性：数据源呈现的UI方式，二次开发可忽略 |

---

### 6. 客户指派

**调用方式**: HTTP | POST  
**接口地址**: `http://ls1.jmt.ink:46088/sysa/mobilephone/systemmanage/order.asp?datatype=tel`  
**请求类型**: application/json

#### 请求参数

| 字段名称 | 类型 | 必填 | 描述 |
|---------|------|------|------|
| ord | int | 否 | 数据唯一标识 |
| member1 | int | 是 | 指派方式，整型，必填，枚举类型，如：1:对所有用户公开、0:指派给以下用户 |
| member2 | string | 否 | 指派用户，文本，50字以内，来自树结构数据 |

---

### 7. 客户跟进（洽谈进展）

**调用方式**: HTTP | POST  
**接口地址**: `http://ls1.jmt.ink:46088/sysa/mobilephone/systemmanage/reply.asp?datatype=tel`  
**请求类型**: application/json

#### 请求参数

| 字段名称 | 类型 | 必填 | 描述 |
|---------|------|------|------|
| ord | int | 否 | 数据唯一标识 |
| intro | string | 是 | 选择模板，必填，1000字以内，枚举类型<br>如：106:谈的很好，让发合同、107:电话无人接听、108:现在还没考虑、109:今天谈的不错，让明天面谈、120:正在考虑中 |
| files | string | 否 | 添加附件，50字以内 |
| sort | int | 是 | 跟进方式，整型，必填，枚举类型<br>如：484:其他、483:上门、482:邮件、481:电话<br>**来自接口**: `/mobilephone/source.asp?enumid=98` |
| lead | int | 否 | 关联联系人，整型，枚举类型，如：0:不关联 |
| plantype | int | 是 | 日程类型，整型，必填，枚举类型<br>如：2:已完成日程、1:待完成日程、0:不生成 |
| @ret2_0 | datetime | 是 | 开始时间，日期，必填 |
| @ret2_1 | datetime | 是 | 结束时间，日期，必填 |
| @title2 | string | 是 | 日程内容，必填，1000字以内 |
| @intro2 | string | 是 | 完成情况，必填，1000字以内 |
| @cateid | string | 否 | 执行人员，4000字以内 |
| @remind | int | 是 | 是否提醒，整型，必填，枚举类型，如：0:提醒、1:不提醒 |
| @ret_0 | datetime | 是 | 开始时间，日期，必填 |
| @ret_1 | datetime | 是 | 结束时间，日期，必填 |
| @title1 | string | 是 | 日程内容，必填，1000字以内 |

---

### 8. 客户添加（新版V3接口）

**调用方式**: HTTP | POST  
**接口地址**: `http://ls1.jmt.ink:46088/webapi/v3/sales/customer/add`

**特别说明**: 这是新版API接口，采用JSON格式直接传参，不使用id-val键值对形式。

#### Token传参方式

在Http头中增加: `ZBAPI-Token: ******`（注: ****** 为具体的session值）

#### 请求参数（精选重点字段）

| 字段名称 | 类型 | 必填 | 描述 |
|---------|------|------|------|
| sort2 | int | 是 | 客户属性 1单位客户,2个人客户 |
| name | string | 是 | 客户名称 由策略控制是否必填；作为查重规则时要避免重复 |
| khid | string | 否 | 客户编号 由策略控制是否必填；作为查重规则时要避免重复；客户的唯一编号 |
| sort | string | 是 | 客户分类 必填 |
| sort1 | string | 是 | 跟进程度 必填 |
| ly | string | 否 | 客户来源 由策略控制是否必填 |
| area | string | 否 | 客户区域 由策略控制是否必填 |
| trade | string | 否 | 客户行业 由策略控制是否必填 |
| jz | string | 否 | 价值评估 由策略控制是否必填 |
| person_name | string | 是 | 联系人姓名 由策略控制是否必填 |
| mobile | string | 否 | 联系人手机 由策略控制是否必填；格式需满足11位的有效手机号码 |
| email | string | 否 | 联系人电子邮件 由策略控制是否必填 |

#### 输出参数

| 字段名称 | 类型 | 描述 |
|---------|------|------|
| Code | Int | 状态码，请求成功=200；请求失败=300；token验证失败=400；服务器内部错误=500 |
| Msg | String | 提示信息 |

---

## 联系人管理

### 1. 联系人添加

**调用方式**: HTTP | POST  
**接口地址**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/person/add.asp`  
**请求类型**: application/json

#### 请求参数

| 字段名称 | 类型 | 必填 | 描述 |
|---------|------|------|------|
| ord | int | 否 | 数据唯一标识 |
| company | int | 是 | 关联客户，整型，必填<br>**来自接口**: `mobilephone/salesManage/custom/list.asp?checktype=radio` |
| person_name | string | 是 | 联系人姓名，必填，50字以内 |
| pym | string | 否 | 拼音码，50字以内 |
| sex | string | 否 | 性别，文本，50字以内，枚举类型，如：男:男、女:女 |
| age | int | 否 | 年龄，整型 |
| year1 | datetime | 否 | 生日，日期 |
| part1 | string | 否 | 部门，50字以内 |
| job | string | 否 | 职务，50字以内 |
| phone | string | 否 | 办公电话，50字以内 |
| fax | string | 否 | 传真，50字以内 |
| mobile | string | 否 | 手机，50字以内 |
| mobile2 | string | 否 | 手机2，50字以内 |
| phone2 | string | 否 | 家庭电话，50字以内 |
| email | string | 否 | 电子邮件，50字以内 |
| qq | string | 否 | QQ，20字以内 |
| weixinAcc | string | 否 | 微信，50字以内 |
| XiQueIntro | string | 否 | 喜鹊声声，50字以内 |
| msn | string | 否 | MSN，50字以内 |
| jg | string | 否 | 籍贯，50字以内 |
| zip | string | 否 | 邮编，10字以内 |
| joy | string | 否 | 爱好特长，3000字以内 |
| intro | string | 否 | 备注，5000字以内 |

---

### 2. 联系人详情

**调用方式**: HTTP | POST  
**接口地址**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/person/add.asp?edit=1`  
**请求类型**: application/json

#### 请求参数

| 字段名称 | 类型 | 必填 | 描述 |
|---------|------|------|------|
| edit | string | 否 | 修改模式 |
| ord | int | 否 | 数据唯一标识 |
| _insert_rowindex | string | 否 |  |
| debug | string | 否 |  |

---

### 3. 联系人列表

**调用方式**: HTTP | POST  
**接口地址**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/person/list.asp`  
**请求类型**: application/json

#### 请求参数（精选）

| 字段名称 | 类型 | 必填 | 描述 |
|---------|------|------|------|
| stype | int | 否 | 列表模式，整型，默认为空:联系人列表，1:生日提醒 |
| company | int | 否 | 客户ID，整型，默认为空 |
| remind | string | 否 | 提醒类型，7:生日提醒 |
| checktype | string | 否 | 关联联系人选择模式，radio 单选 |
| person_name | string | 否 | 联系人姓名，文本，默认为空，模糊检索条件 |
| pym | string | 否 | 拼音码，文本，默认为空，模糊检索条件 |
| name | string | 否 | 客户名称，文本，默认为空，模糊检索条件 |
| mobile | string | 否 | 手机，文本，默认为空，模糊检索条件 |
| email | string | 否 | 电子邮件，文本，默认为空，模糊检索条件 |
| pagesize | int | 否 | 每页记录数 |
| pageindex | int | 否 | 数据页标 |

---

## 通用数据类型

### ZBDocument类型

所有接口返回结果统一为ZBDocument类型，该类型包含【接口状态】+【实际业务】两部分。

### MessageClass 类

消息对象，一般用于返回某些操作的执行情况，如保存信息，退出信息等等。

| 字段名称 | 数据类型 | 详细说明 |
|---------|----------|----------|
| title | String | 消息的标题 |
| text | String | 消息的正文 |
| url | String | 显示该消息后，系统应跳转的网址，二次开发无用 |
| wait | Integer | 该消息在前端的呈现时长，单位为秒 |
| target | String | 消息如果包含链接，链接的跳转方式，二次开发无用 |
| uitype | String | 消息的UI类型，二次开发无用 |
| data | String | 消息的附加数据，扩展用 |

### BillClass 类

单据对象，一般用于表示实际业务中由多个不同字段组成的数据结构，如客户详情、合同详情、合同添加等。

| 字段名称 | 数据类型 | 详细说明 |
|---------|----------|----------|
| id | String | 单据类型的Id，一般二次开发扩展用，无实际业务含义 |
| caption | String | 当前单据的标题 |
| uitype | String | UI属性：单据UI标记 |
| value | String | 数据唯一标识，泛指当前单据的数据标识ID值，如客户ID、合同ID等等 |
| tools | ASPCollection对象 | UI属性：当前单据前端操作功能集合，二次开发无用 |
| groups | ASPCollection对象 | 单据所包含的字段组集合 |

### SourceClass 类

数据源对象，用于表示几种数据：枚举型数据(options)、表格型数据（table）、文本数据等。

| 字段名称 | 数据类型 | 详细说明 |
|---------|----------|----------|
| type_ | String | 数据源的类型，不同的类型对应不同格式的数据 |
| table | tableClass对象 | 数据源表格对象，当type_属性为table时，该对象有值 |
| uitype | String | UI属性：数据源呈现的UI方式，二次开发可忽略 |

---

## 重要字段汇总

### 客户来源字段

在不同接口中，客户来源字段名称不同：

1. **客户列表接口** (`custom/list.asp`):
   - `tjly` - 统计来源（用于筛选）
   - `ly` - 客户来源（多选项检索，逗号分隔）
   - `khly` - 客户来源（单个值）

2. **客户添加/修改接口** (`custom/add.asp`):
   - `ly` - 客户来源（整型，枚举类型）

3. **枚举数据来源接口**:
   - `/mobilephone/source.asp?enumid=13` - 获取客户来源枚举值
   - 示例值：173:陌生开发、171:网站注册、977:VIP、174:广告宣传、172:朋友介绍

### 参数传递格式

#### V1.0版本接口（老版）
使用 id-val 键值对数组形式：
```python
datas = [{"id": "name", "val": "测试公司"}]
json_data = {"session": "******", "datas": datas}
```

#### V3版本接口（新版）
使用标准JSON格式，Token在Header中传递：
```python
headers = {"ZBAPI-Token": "******"}
json_data = {"name": "测试公司", "sort2": 1}
```

---

## 附录：常用枚举数据接口

| 接口 | 用途 |
|------|------|
| `/mobilephone/source.asp?enumid=13` | 客户来源枚举 |
| `/mobilephone/source.asp?enumid=11` | 客户行业枚举 |
| `/mobilephone/source.asp?enumid=14` | 价值评估枚举 |
| `/mobilephone/source.asp?enumid=98` | 跟进方式枚举 |
| `/mobilephone/systemManage/gate_list.asp?stype=check` | 人员选择枚举 |
| `/mobilephone/systemManage/area_list.asp?stype=check` | 客户区域枚举 |
| `/mobilephone/systemManage/telsort_list.asp?stype=check` | 客户分类枚举 |

---

**文档版本历史**:
- v1.0 (2025-10-18): 初始版本，基于手工复制的API文档整理

