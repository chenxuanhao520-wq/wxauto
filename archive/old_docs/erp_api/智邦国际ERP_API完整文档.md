# 智邦国际 ERP OpenAPI 完整文档

**抓取时间**: 2025-10-18  
**来源**: http://ls1.jmt.ink:46088/sysn/view/OpenApi/help.ashx  
**版本**: 32.17  

---

**API 总数**: 219 个

## 📋 目录

- [概述](#概述)
- [对接须知](#对接须知)
- [鉴权接口](#鉴权接口)
- [组织架构](#组织架构)
- [销售栏目](#销售栏目)
- [采购栏目](#采购栏目)
- [库存栏目](#库存栏目)
- [生产栏目](#生产栏目)
- [财务栏目](#财务栏目)
- [办公栏目](#办公栏目)
- [研发](#研发)
- [人资栏目](#人资栏目)

---

## 概述

**URL**: `remark.html`


---

## 对接须知

**URL**: `infnotice.html`


---

## 鉴权接口

### 登录系统

**端点**: `/webapi/v3/ov1/login`

```http
POST /webapi/v3/ov1/login
```

### 退出系统

**端点**: `/webapi/v3/ov1/logout`

```http
POST /webapi/v3/ov1/logout
```


---

## 组织架构

### 部门管理

#### 部门对接

##### 部门列表

**端点**: `/webapi/v3/orgs/dept/list`

```http
POST /webapi/v3/orgs/dept/list
```

##### 部门添加

**端点**: `/webapi/v3/orgs/dept/add`

```http
POST /webapi/v3/orgs/dept/add
```

##### 部门修改

**端点**: `/webapi/v3/orgs/dept/edit`

```http
POST /webapi/v3/orgs/dept/edit
```

##### 部门详情

**端点**: `/webapi/v3/orgs/dept/detail`

```http
POST /webapi/v3/orgs/dept/detail
```

### 账号管理

#### 账号对接

##### 账号列表

**端点**: `/webapi/v3/orgs/user/list`

```http
POST /webapi/v3/orgs/user/list
```

##### 账号添加

**端点**: `/webapi/v3/orgs/user/add`

```http
POST /webapi/v3/orgs/user/add
```

##### 账号修改

**端点**: `/webapi/v3/orgs/user/edit`

```http
POST /webapi/v3/orgs/user/edit
```

##### 账号删除

**端点**: `/webapi/v3/orgs/user/delete`

```http
POST /webapi/v3/orgs/user/delete
```

##### 账号详情

**端点**: `/webapi/v3/orgs/user/detail`

```http
POST /webapi/v3/orgs/user/detail
```


---

## 销售栏目

### 客户管理

#### 客户对接

##### 分配新客户ID

**端点**: `/webapi/v3/ov1/salesmanage/custom/add?apihelptype=new`

```http
POST /webapi/v3/ov1/salesmanage/custom/add?apihelptype=new
```

##### 添加或修改单位客户

**端点**: `/webapi/v3/ov1/salesmanage/custom/add?intsort=1&apihelptype=save`

```http
POST /webapi/v3/ov1/salesmanage/custom/add?intsort=1&apihelptype=save
```

##### 添加或修改个人客户

**端点**: `/webapi/v3/ov1/salesmanage/custom/add?intsort=2&apihelptype=save`

```http
POST /webapi/v3/ov1/salesmanage/custom/add?intsort=2&apihelptype=save
```

##### 获取客户详情

    **端点**: `/sysa/mobilephone/salesmanage/custom/add.asp?edit=1`

**调用方式**: HTTP | POST  
**请求类型**: application/json

**请求参数**:
| 字段名称 | 类型 | 必填 | 描述 |
|---------|------|------|------|
| edit | string | 否 | 修改模式，是否返回修改模式的数据，默认为空，二次开发时无用 |
| intsort | string | 否 | 客户类型，1: 单位客户、2: 个人客户，该参数也可在URL中定义 |
| ord | int | 否 | 数据唯一标识，整数，泛指当前单据的数据标识值，如客户ID、合同ID等等，可从相应的列表接口获取该值 |
| _insert_rowindex | string | 否 |  |
| debug | string | 否 |  |

**Python调用示例**:
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

**返回结果**:
接口返回结果统一为ZBDocument类型，该类型包含【接口状态】+【实际业务】两部分。
在本接口中，实际业务数据类型为BillClass（单据对象）。

**BillClass字段说明**:
| 字段名称 | 数据类型 | 详细说明 |
|---------|----------|----------|
| id | String | 单据类型的Id，一般二次开发扩展用，无实际业务含义 |
| caption | String | 当前单据的标题 |
| uitype | String | UI属性：单据UI标记 |
| value | String | 数据唯一标识，泛指当前单据的数据标识ID值，如客户ID、合同ID等等 |
| tools | ASPCollection | UI属性：当前单据前端操作功能集合，二次开发无用 |
| groups | ASPCollection | 单据所包含的字段组集合 |

```http
POST /sysa/mobilephone/salesmanage/custom/add.asp?edit=1
```

##### 获取客户列表

**端点**: `/webapi/v3/ov1/salesmanage/custom/list`

```http
POST /webapi/v3/ov1/salesmanage/custom/list
```

##### 客户指派

**端点**: `/webapi/v3/ov1/systemmanage/order?datatype=tel&apihelptype=save`

```http
POST /webapi/v3/ov1/systemmanage/order?datatype=tel&apihelptype=save
```

##### 客户收回

**端点**: `/webapi/v3/ov1/salesmanage/custom/takeback`

```http
POST /webapi/v3/ov1/salesmanage/custom/takeback
```

##### 客户申请

**端点**: `/webapi/v3/ov1/salesmanage/custom/apply`

```http
POST /webapi/v3/ov1/salesmanage/custom/apply
```

##### 客户审批

**端点**: `/webapi/v3/ov1/salesmanage/custom/approve?__msgid=onsave`

```http
POST /webapi/v3/ov1/salesmanage/custom/approve?__msgid=onsave
```

##### 客户审核

**端点**: `/webapi/v3/ov1/salesManage/custom/approve_set?apihelptype=save`

```http
POST /webapi/v3/ov1/salesManage/custom/approve_set?apihelptype=save
```

##### 客户跟进

**端点**: `/webapi/v3/ov1/systemManage/reply?datatype=tel&apihelptype=save`

```http
POST /webapi/v3/ov1/systemManage/reply?datatype=tel&apihelptype=save
```

##### 客户共享

**端点**: `/webapi/v3/ov1/salesManage/custom/share?apihelptype=save`

```http
POST /webapi/v3/ov1/salesManage/custom/share?apihelptype=save
```

##### 客户保护

**端点**: `/webapi/v3/ov1/salesManage/custom/add?__msgid=profect`

```http
POST /webapi/v3/ov1/salesManage/custom/add?__msgid=profect
```

##### 客户放弃保护

**端点**: `/webapi/v3/ov1/salesManage/custom/add?__msgid=unprofect`

```http
POST /webapi/v3/ov1/salesManage/custom/add?__msgid=unprofect
```

##### 客户添加

**端点**: `/webapi/v3/sales/customer/add`

```http
POST /webapi/v3/sales/customer/add
```

##### 客户修改

**端点**: `/webapi/v3/sales/customer/edit`

```http
POST /webapi/v3/sales/customer/edit
```

#### 客户联系人对接

##### 添加或修改联系人

**端点**: `/webapi/v3/ov1/salesmanage/person/add?apihelptype=save`

```http
POST /webapi/v3/ov1/salesmanage/person/add?apihelptype=save
```

##### 获取联系人详情

**端点**: `/webapi/v3/ov1/salesmanage/person/add?edit=1&apihelptype=get`

```http
POST /webapi/v3/ov1/salesmanage/person/add?edit=1&apihelptype=get
```

##### 获取联系人列表

**端点**: `/webapi/v3/ov1/salesmanage/person/list`

```http
POST /webapi/v3/ov1/salesmanage/person/list
```

##### 联系人跟进

**端点**: `/webapi/v3/ov1/systemManage/reply?datatype=person&apihelptype=save`

```http
POST /webapi/v3/ov1/systemManage/reply?datatype=person&apihelptype=save
```

### 项目管理

#### 项目对接

##### 获取项目列表

**端点**: `/webapi/v3/ov1/salesmanage/chance/list`

```http
POST /webapi/v3/ov1/salesmanage/chance/list
```

##### 获取项目详情

**端点**: `/webapi/v3/ov1/salesmanage/chance/add?apihelptype=get`

```http
POST /webapi/v3/ov1/salesmanage/chance/add?apihelptype=get
```

##### 项目跟进

**端点**: `/webapi/v3/ov1/systemManage/reply?datatype=chance&apihelptype=save`

```http
POST /webapi/v3/ov1/systemManage/reply?datatype=chance&apihelptype=save
```

##### 项目审批

**端点**: `/webapi/v3/ov1/systemmanage/approve?dtype=25&apihelptype=save`

```http
POST /webapi/v3/ov1/systemmanage/approve?dtype=25&apihelptype=save
```

### 合同管理

#### 合同对接

##### 添加合同明细

**端点**: `/webapi/v3/ov1/salesmanage/contract/contractlist?__msgId=addToContract`

```http
POST /webapi/v3/ov1/salesmanage/contract/contractlist?__msgId=addToContract
```

##### 编辑合同明细列表

**端点**: `/webapi/v3/ov1/salesmanage/contract/contractlist`

```http
POST /webapi/v3/ov1/salesmanage/contract/contractlist
```

##### 编辑合同明细删除

**端点**: `/webapi/v3/ov1/salesmanage/contract/contractlist?__msgId=delete&batch=0`

```http
POST /webapi/v3/ov1/salesmanage/contract/contractlist?__msgId=delete&batch=0
```

##### 编辑合同明细

**端点**: `/webapi/v3/ov1/salesmanage/contract/contractlist_edit?apihelptype=save`

```http
POST /webapi/v3/ov1/salesmanage/contract/contractlist_edit?apihelptype=save
```

##### 编辑合同明细单位选择

**端点**: `/webapi/v3/ov1/salesmanage/contract/UnitChange?ord=0&__unit=0&company=0&apihelptype=get`

```http
POST /webapi/v3/ov1/salesmanage/contract/UnitChange?ord=0&__unit=0&company=0&apihelptype=get
```

##### 添加或修改合同

**端点**: `/webapi/v3/ov1/salesmanage/contract/add?apihelptype=save`

```http
POST /webapi/v3/ov1/salesmanage/contract/add?apihelptype=save
```

##### 合同关联客户

**端点**: `/webapi/v3/ov1/salesmanage/custom/list?datatype=addcontract&checktype=redio`

```http
POST /webapi/v3/ov1/salesmanage/custom/list?datatype=addcontract&checktype=redio
```

##### 合同关联对方代表

**端点**: `/webapi/v3/ov1/salesManage/person/list?checktype=radio`

```http
POST /webapi/v3/ov1/salesManage/person/list?checktype=radio
```

##### 获取合同列表

**端点**: `/webapi/v3/ov1/salesmanage/contract/billlist`

```http
POST /webapi/v3/ov1/salesmanage/contract/billlist
```

##### 合同洽谈进展

**端点**: `/webapi/v3/ov1/systemManage/reply?datatype=contract&apihelptype=save`

```http
POST /webapi/v3/ov1/systemManage/reply?datatype=contract&apihelptype=save
```

##### 合同共享

**端点**: `/webapi/v3/ov1/salesManage/contract/share?apihelptype=save`

```http
POST /webapi/v3/ov1/salesManage/contract/share?apihelptype=save
```

##### 合同审批

**端点**: `/webapi/v3/ov1/systemmanage/approve?dtype=2&apihelptype=save`

```http
POST /webapi/v3/ov1/systemmanage/approve?dtype=2&apihelptype=save
```

##### 合同详情

**端点**: `/webapi/v3/sales/contract/detail`

```http
POST /webapi/v3/sales/contract/detail
```

##### 合同审批修改

**端点**: `/webapi/v3/sales/contract/approve/edit`

```http
POST /webapi/v3/sales/contract/approve/edit
```

##### 合同审批记录详情

**端点**: `/webapi/v3/sales/contract/approve/approveStageList/detail`

```http
POST /webapi/v3/sales/contract/approve/approveStageList/detail
```

##### 合同添加

**端点**: `/webapi/v3/sale/contract/add`

```http
POST /webapi/v3/sale/contract/add
```

### 售后服务

#### 售后服务对接

##### 获取售后服务列表

**端点**: `/webapi/v3/ov1/salesmanage/service/list`

```http
POST /webapi/v3/ov1/salesmanage/service/list
```

##### 获取售后服务详情

**端点**: `/webapi/v3/ov1/salesmanage/service/add?apihelptype=get`

```http
POST /webapi/v3/ov1/salesmanage/service/add?apihelptype=get
```

##### 售后服务处理

**端点**: `/webapi/v3/ov1/salesmanage/service/chuli?apihelptype=save`

```http
POST /webapi/v3/ov1/salesmanage/service/chuli?apihelptype=save
```

### 售后维修

#### 售后维修对接

##### 添加或修改售后维修

**端点**: `/webapi/v3/ov1/salesmanage/repair/DealAdd?apihelptype=save`

```http
POST /webapi/v3/ov1/salesmanage/repair/DealAdd?apihelptype=save
```

##### 获取售后维修列表

**端点**: `/webapi/v3/ov1/salesmanage/repair/Deallist`

```http
POST /webapi/v3/ov1/salesmanage/repair/Deallist
```

##### 获取售后维修详情

**端点**: `/webapi/v3/ov1/salesmanage/repair/Dealcontent?apihelptype=get`

```http
POST /webapi/v3/ov1/salesmanage/repair/Dealcontent?apihelptype=get
```


---

## 采购栏目

### 采购管理

#### 采购对接

##### 获取采购列表

**端点**: `/webapi/v3/ov1/storemanage/caigou/list`

```http
POST /webapi/v3/ov1/storemanage/caigou/list
```

##### 获取采购详情

**端点**: `/webapi/v3/ov1/storemanage/caigou/add?apihelptype=get`

```http
POST /webapi/v3/ov1/storemanage/caigou/add?apihelptype=get
```

##### 获取采购审批

**端点**: `/webapi/v3/ov1/systemmanage/approve?dtype=3&apihelptype=save`

```http
POST /webapi/v3/ov1/systemmanage/approve?dtype=3&apihelptype=save
```

### 供应商管理

#### 供应商对接

##### 供应商详情

**端点**: `/webapi/v3/store/supplierDetail/detail`

```http
POST /webapi/v3/store/supplierDetail/detail
```

##### 供应商列表

**端点**: `/webapi/v3/store/supplierList`

```http
POST /webapi/v3/store/supplierList
```


---

## 库存栏目

### 库存查看

#### 库存查看对接

##### 获取库存详情

**端点**: `/webapi/v3/ov1/storemanage/store/content?apihelptype=get`

```http
POST /webapi/v3/ov1/storemanage/store/content?apihelptype=get
```

##### 获取库存查看列表

**端点**: `/webapi/v3/ov1/storemanage/store/list`

```http
POST /webapi/v3/ov1/storemanage/store/list
```

##### 产品库存明细列表

**端点**: `/webapi/v3/store/inventory/InventoryDetails`

```http
POST /webapi/v3/store/inventory/InventoryDetails
```

##### 产品库存汇总列表

**端点**: `/webapi/v3/store/inventory/InventorySummary`

```http
POST /webapi/v3/store/inventory/InventorySummary
```

#### 仓库对接

##### 获取仓库列表

**端点**: `/webapi/apiHelper/stock/Stock/GetWarehouses`

```http
POST /webapi/apiHelper/stock/Stock/GetWarehouses
```

##### 获取库位列表

**端点**: `/webapi/v3/uview/stock/Pages/WareHouse/SettingApiList`

```http
POST /webapi/v3/uview/stock/Pages/WareHouse/SettingApiList
```

##### 获取仓库列表（32.15及以后）

**端点**: `/webapi/v3/store/WareHouseStructList`

```http
POST /webapi/v3/store/WareHouseStructList
```

### 入库管理

#### 入库对接

##### 获取入库列表

**端点**: `/webapi/v3/ov1/storemanage/kuin/list`

```http
POST /webapi/v3/ov1/storemanage/kuin/list
```

##### 获取入库详情

**端点**: `/webapi/v3/ov1/storemanage/kuin/detail?apihelptype=get`

```http
POST /webapi/v3/ov1/storemanage/kuin/detail?apihelptype=get
```

##### 获取入库产品明细

**端点**: `/webapi/v3/ov1/storemanage/kuin/MoreKuinList`

```http
POST /webapi/v3/ov1/storemanage/kuin/MoreKuinList
```

##### 入库成本修改

**端点**: `/webapi/v3/store/kuin/costmodify/edit`

```http
POST /webapi/v3/store/kuin/costmodify/edit
```

##### 入库确认

**端点**: `/webapi/v3/store/kuin/surekuin/edit`

```http
POST /webapi/v3/store/kuin/surekuin/edit
```

##### 入库确认（32.15及以后）

**端点**: `/webapi/v3/store/KuInApplyEdit/edit`

```http
POST /webapi/v3/store/KuInApplyEdit/edit
```

##### 入库列表（32.15及以后）

**端点**: `/webapi/v3/store/KuInApplyList`

```http
POST /webapi/v3/store/KuInApplyList
```

#### 直接入库

##### 直接入库添加

**端点**: `/webapi/v3/store/kuin/add`

```http
POST /webapi/v3/store/kuin/add
```

### 出库管理

#### 出库对接

##### 出库确认

**端点**: `/webapi/v3/store/kuout/surekuout/edit`

```http
POST /webapi/v3/store/kuout/surekuout/edit
```

##### 出库详情

**端点**: `/webapi/v3/store/kuout/detail`

```http
POST /webapi/v3/store/kuout/detail
```

##### 出库列表

**端点**: `/webapi/v3/store/kuout/List`

```http
POST /webapi/v3/store/kuout/List
```

##### 库存操作修改

**端点**: `/webapi/v3/store/inventory/edit`

```http
POST /webapi/v3/store/inventory/edit
```

##### 库存操作详情

**端点**: `/webapi/v3/store/inventory/detail`

```http
POST /webapi/v3/store/inventory/detail
```

##### 出库确认（32.15及以后）

**端点**: `/webapi/v3/store/KuOutApplyEdit/edit`

```http
POST /webapi/v3/store/KuOutApplyEdit/edit
```

##### 出库列表（32.15及以后）

**端点**: `/webapi/v3/store/KuOutApplyList`

```http
POST /webapi/v3/store/KuOutApplyList
```

### 发货管理

#### 发货对接

##### 获取发货详情

**端点**: `/webapi/v3/ov1/storemanage/sent/detail?apihelptype=get`

```http
POST /webapi/v3/ov1/storemanage/sent/detail?apihelptype=get
```

##### 获取发货产品明细

**端点**: `/webapi/v3/ov1/storemanage/sent/moresendlist`

```http
POST /webapi/v3/ov1/storemanage/sent/moresendlist
```

##### 获取发货列表

**端点**: `/webapi/v3/ov1/storemanage/sent/list`

```http
POST /webapi/v3/ov1/storemanage/sent/list
```

### 产品管理

#### 产品对接

##### 获取产品单位列表

**端点**: `/webapi/apiHelper/sale/Product/GetProductUnitLists`

```http
POST /webapi/apiHelper/sale/Product/GetProductUnitLists
```

##### 获取产品分类信息

**端点**: `/webapi/v3/ov1/systemManage/product_sort_list?stype=check&apihelptype=get`

```http
POST /webapi/v3/ov1/systemManage/product_sort_list?stype=check&apihelptype=get
```

##### 获取发票类型列表

**端点**: `/webapi/apiHelper/sale/Product/GetInvoiceTypesLists`

```http
POST /webapi/apiHelper/sale/Product/GetInvoiceTypesLists
```

##### 获取产品列表

**端点**: `/webapi/v3/ov1/salesmanage/product/billlist`

```http
POST /webapi/v3/ov1/salesmanage/product/billlist
```

##### 获取产品详情

**端点**: `/webapi/v3/ov1/salesmanage/product/billService?apihelptype=get`

```http
POST /webapi/v3/ov1/salesmanage/product/billService?apihelptype=get
```

##### 产品加入合同

**端点**: `/webapi/v3/ov1/salesmanage/contract/contractlist?__msgId=addToContract`

```http
POST /webapi/v3/ov1/salesmanage/contract/contractlist?__msgId=addToContract
```

##### 产品批量添加

**端点**: `/webapi/v3/store/productbatch/add`

```http
POST /webapi/v3/store/productbatch/add
```

##### 产品添加

**端点**: `/webapi/v3/store/product/add`

```http
POST /webapi/v3/store/product/add
```

##### 产品修改

**端点**: `/webapi/v3/store/product/edit`

```http
POST /webapi/v3/store/product/edit
```


---

## 生产栏目

### 物料清单管理

#### 物料清单对接

##### 物料清单添加/修改(适用V32.10已有功能)

**端点**: `/webapi/apiHelper/produce/Bom/SaveBoms`

```http
POST /webapi/apiHelper/produce/Bom/SaveBoms
```

##### 物料清单列表(适用V32.10已有功能)

**端点**: `/webapi/apiHelper/produce/Bom/GetBoms`

```http
POST /webapi/apiHelper/produce/Bom/GetBoms
```

### 设备管理

#### 设备对接

##### 获取设备列表

**端点**: `/webapi/apiHelper/produce/Machine/GetMachines`

```http
POST /webapi/apiHelper/produce/Machine/GetMachines
```

##### 设备添加

**端点**: `/webapi/v3/produce/Machine/add`

```http
POST /webapi/v3/produce/Machine/add
```

### 工序管理

#### 岗位对接

##### 岗位列表

**端点**: `/webapi/v3/produceV2/workflow/workingprocedure/jobs/list`

```http
POST /webapi/v3/produceV2/workflow/workingprocedure/jobs/list
```

#### 工序分类对接

##### 工序分类列表

**端点**: `/webapi/v3/produceV2/workflow/workingprocedure/class/list`

```http
POST /webapi/v3/produceV2/workflow/workingprocedure/class/list
```

#### 工序对接

##### 工序添加

**端点**: `/webapi/v3/produceV2/workflow/workingprocedure/add`

```http
POST /webapi/v3/produceV2/workflow/workingprocedure/add
```

##### 工序修改

**端点**: `/webapi/v3/produceV2/workflow/workingprocedure/edit`

```http
POST /webapi/v3/produceV2/workflow/workingprocedure/edit
```

##### 工序详情

**端点**: `/webapi/v3/produceV2/workflow/workingprocedure/detail`

```http
POST /webapi/v3/produceV2/workflow/workingprocedure/detail
```

##### 工序列表

**端点**: `/webapi/v3/produceV2/workflow/workingprocedure/list`

```http
POST /webapi/v3/produceV2/workflow/workingprocedure/list
```

### 工艺路线管理

#### 工艺路线对接

##### 工艺路线添加

**端点**: `/webapi/v3/produceV2/workflow/workingflow/add`

```http
POST /webapi/v3/produceV2/workflow/workingflow/add
```

##### 工艺路线修改

**端点**: `/webapi/v3/produceV2/workflow/workingflow/edit`

```http
POST /webapi/v3/produceV2/workflow/workingflow/edit
```

##### 工艺路线详情

**端点**: `/webapi/v3/produceV2/workflow/workingflow/detail`

```http
POST /webapi/v3/produceV2/workflow/workingflow/detail
```

##### 工艺路线列表

**端点**: `/webapi/v3/produceV2/workflow/workingflow/list`

```http
POST /webapi/v3/produceV2/workflow/workingflow/list
```

### 派工管理

#### 派工对接

##### 派工添加

**端点**: `/webapi/apiHelper/produce/WorkAssigns/SaveWorkAssigns`

```http
POST /webapi/apiHelper/produce/WorkAssigns/SaveWorkAssigns
```

##### 获取派工列表

**端点**: `/webapi/apiHelper/produce/WorkAssigns/GetWorkAssigns`

```http
POST /webapi/apiHelper/produce/WorkAssigns/GetWorkAssigns
```

### 领料管理

#### 领料对接

##### 领料添加

**端点**: `/webapi/apiHelper/produce/MaterialOrder/SaveMaterialOrders`

```http
POST /webapi/apiHelper/produce/MaterialOrder/SaveMaterialOrders
```

##### 获取领料列表

**端点**: `/webapi/apiHelper/produce/MaterialOrder/GetMaterialOrders`

```http
POST /webapi/apiHelper/produce/MaterialOrder/GetMaterialOrders
```

### 生产质检管理

#### 生产质检对接

##### 生产质检任务添加

**端点**: `/webapi/apiHelper/produce/QualityTesting/SaveQualityTestingsTask`

```http
POST /webapi/apiHelper/produce/QualityTesting/SaveQualityTestingsTask
```

##### 获取生产质检任务列表

**端点**: `/webapi/apiHelper/produce/QualityTesting/GetQualityTestingTasks`

```http
POST /webapi/apiHelper/produce/QualityTesting/GetQualityTestingTasks
```

##### 生产质检添加/修改

**端点**: `/webapi/apiHelper/produce/QualityTesting/SaveQualityTestings`

```http
POST /webapi/apiHelper/produce/QualityTesting/SaveQualityTestings
```

##### 获取生产质检计划

**端点**: `/webapi/apiHelper/produce/QualityTesting/GetQualityTestingPlans`

```http
POST /webapi/apiHelper/produce/QualityTesting/GetQualityTestingPlans
```

##### 获取生产质检列表

**端点**: `/webapi/apiHelper/produce/QualityTesting/GetQualityTestings`

```http
POST /webapi/apiHelper/produce/QualityTesting/GetQualityTestings
```

##### 生产质检审核

**端点**: `/webapi/apiHelper/produce/QualityTesting/CheckQualityTestings`

```http
POST /webapi/apiHelper/produce/QualityTesting/CheckQualityTestings
```

##### 获取不合格原因列表

**端点**: `/webapi/apiHelper/produce/QualityTesting/GetUnQualiFiedList`

```http
POST /webapi/apiHelper/produce/QualityTesting/GetUnQualiFiedList
```

##### 获取报废原因列表

**端点**: `/webapi/apiHelper/produce/QualityTesting/GetScrapReasonList`

```http
POST /webapi/apiHelper/produce/QualityTesting/GetScrapReasonList
```

##### 获取质量等级列表

**端点**: `/webapi/apiHelper/produce/QualityTesting/GetQualityLevelList`

```http
POST /webapi/apiHelper/produce/QualityTesting/GetQualityLevelList
```

### 物料登记管理

#### 物料登记对接

##### 物料登记添加

**端点**: `/webapi/apiHelper/produce/MaterialRegister/SaveMaterialRegisters`

```http
POST /webapi/apiHelper/produce/MaterialRegister/SaveMaterialRegisters
```

##### 获取物料登记列表

**端点**: `/webapi/apiHelper/produce/MaterialRegister/GetMaterialRegisters`

```http
POST /webapi/apiHelper/produce/MaterialRegister/GetMaterialRegisters
```

### 工序汇报管理

#### 工序汇报计划

##### 工序汇报添加

**端点**: `/webapi/v3/produceV2/processreport/add`

```http
POST /webapi/v3/produceV2/processreport/add
```

##### 工序汇报删除

**端点**: `/webapi/v3/produceV2/processreport/delete`

```http
POST /webapi/v3/produceV2/processreport/delete
```

##### 工序汇报计划

**端点**: `/webapi/v3/produceV2/procedure/planlist`

```http
POST /webapi/v3/produceV2/procedure/planlist
```

##### 工序汇报详情

**端点**: `/webapi/v3/produceV2/processreport/detail`

```http
POST /webapi/v3/produceV2/processreport/detail
```

##### 工序汇报列表查询(明细)

**端点**: `/webapi/v3/produceV2/processreportlist/detail`

```http
POST /webapi/v3/produceV2/processreportlist/detail
```

##### 工序汇报列表查询(汇总)

**端点**: `/webapi/v3/produceV2/processreportlist/summary`

```http
POST /webapi/v3/produceV2/processreportlist/summary
```

##### 工序汇报修改

**端点**: `/webapi/v3/produceV2/processreport/edit`

```http
POST /webapi/v3/produceV2/processreport/edit
```

##### 获取工序任务列表

**端点**: `/webapi/v3/produceV2/ProcessReportTaskList/List`

```http
POST /webapi/v3/produceV2/ProcessReportTaskList/List
```


---

## 财务栏目

### 现金银行

#### 银行对接

##### 获取银行账户明细

**端点**: `/webapi/v3/ov1/financemanage/bank/add?apihelptype=get`

```http
POST /webapi/v3/ov1/financemanage/bank/add?apihelptype=get
```

##### 获取银行账户列表

**端点**: `/webapi/v3/ov1/financemanage/bank/list`

```http
POST /webapi/v3/ov1/financemanage/bank/list
```

### 收款开票管理

#### 收款对接

##### 获取收款详情

**端点**: `/webapi/v3/ov1/financemanage/moneyback/content?apihelptype=get`

```http
POST /webapi/v3/ov1/financemanage/moneyback/content?apihelptype=get
```

##### 获取收款列表

**端点**: `/webapi/v3/ov1/financemanage/moneyback/list`

```http
POST /webapi/v3/ov1/financemanage/moneyback/list
```

#### 开票对接

##### 获取开票详情

**端点**: `/webapi/v3/ov1/financemanage/invoiceback/content?apihelptype=get`

```http
POST /webapi/v3/ov1/financemanage/invoiceback/content?apihelptype=get
```

##### 获取开票列表

**端点**: `/webapi/v3/ov1/financemanage/invoiceback/list`

```http
POST /webapi/v3/ov1/financemanage/invoiceback/list
```

### 付款收票管理

#### 付款对接

##### 获取付款详情

**端点**: `/webapi/v3/ov1/financemanage/moneyout/content?apihelptype=get`

```http
POST /webapi/v3/ov1/financemanage/moneyout/content?apihelptype=get
```

##### 获取付款列表

**端点**: `/webapi/v3/ov1/financemanage/moneyout/list`

```http
POST /webapi/v3/ov1/financemanage/moneyout/list
```

### 费用管理

#### 费用申请对接

##### 添加费用申请

**端点**: `/webapi/v3/ov1/financemanage/apply/add?apihelptype=save`

```http
POST /webapi/v3/ov1/financemanage/apply/add?apihelptype=save
```

##### 编辑费用申请明细列表

**端点**: `/webapi/v3/ov1/financemanage/apply/mxlist`

```http
POST /webapi/v3/ov1/financemanage/apply/mxlist
```

##### 编辑费用申请明细删除

**端点**: `/webapi/v3/ov1/financemanage/apply/mxlist?__msgId=delete&batch=0`

```http
POST /webapi/v3/ov1/financemanage/apply/mxlist?__msgId=delete&batch=0
```

##### 编辑费用申请明细

**端点**: `/webapi/v3/ov1/financemanage/apply/mxedit?apihelptype=save`

```http
POST /webapi/v3/ov1/financemanage/apply/mxedit?apihelptype=save
```

##### 编辑费用申请明细类型选择

**端点**: `/webapi/v3/ov1/financemanage/apply/getsortfields?datatype=paysq&apihelptype=get`

```http
POST /webapi/v3/ov1/financemanage/apply/getsortfields?datatype=paysq&apihelptype=get
```

##### 获取费用申请详情

**端点**: `/webapi/v3/ov1/financemanage/apply/add?edit=1&apihelptype=get`

```http
POST /webapi/v3/ov1/financemanage/apply/add?edit=1&apihelptype=get
```

##### 获取费用申请列表

**端点**: `/webapi/v3/ov1/financemanage/apply/list`

```http
POST /webapi/v3/ov1/financemanage/apply/list
```

##### 费用申请提交审批

**端点**: `/webapi/v3/ov1/systemmanage/setapprove?__msgId=save&approve=7`

```http
POST /webapi/v3/ov1/systemmanage/setapprove?__msgId=save&approve=7
```

##### 费用申请审批

**端点**: `/webapi/v3/ov1/systemmanage/approve?dtype=7&apihelptype=save`

```http
POST /webapi/v3/ov1/systemmanage/approve?dtype=7&apihelptype=save
```

#### 费用使用对接

##### 添加费用使用

**端点**: `/webapi/v3/ov1/financemanage/employ/add?apihelptype=save`

```http
POST /webapi/v3/ov1/financemanage/employ/add?apihelptype=save
```

##### 费用使用关联申请单

**端点**: `/webapi/v3/ov1/financeManage/apply/list?datatype=1&checktype=radio`

```http
POST /webapi/v3/ov1/financeManage/apply/list?datatype=1&checktype=radio
```

##### 费用使用使用人员

**端点**: `/webapi/v3/ov1/systemManage/gate_list?sort=2&stype=radio`

```http
POST /webapi/v3/ov1/systemManage/gate_list?sort=2&stype=radio
```

##### 编辑费用使用明细列表

**端点**: `/webapi/v3/ov1/financemanage/employ/mxlist`

```http
POST /webapi/v3/ov1/financemanage/employ/mxlist
```

##### 编辑费用使用明细删除

**端点**: `/webapi/v3/ov1/financemanage/employ/mxlist?__msgId=delete&batch=0`

```http
POST /webapi/v3/ov1/financemanage/employ/mxlist?__msgId=delete&batch=0
```

##### 编辑费用使用明细

**端点**: `/webapi/v3/ov1/financemanage/employ/mxedit?apihelptype=save`

```http
POST /webapi/v3/ov1/financemanage/employ/mxedit?apihelptype=save
```

##### 编辑费用使用明细类型选择

**端点**: `/webapi/v3/ov1/financemanage/apply/getsortfields?apihelptype=get`

```http
POST /webapi/v3/ov1/financemanage/apply/getsortfields?apihelptype=get
```

##### 获取费用使用详情

**端点**: `/webapi/v3/ov1/financemanage/employ/add?edit=1&apihelptype=get`

```http
POST /webapi/v3/ov1/financemanage/employ/add?edit=1&apihelptype=get
```

##### 获取费用使用列表

**端点**: `/webapi/v3/ov1/financemanage/employ/list`

```http
POST /webapi/v3/ov1/financemanage/employ/list
```

#### 费用报销对接

##### 添加费用报销

**端点**: `/webapi/v3/ov1/financemanage/expenditure/add?apihelptype=save`

```http
POST /webapi/v3/ov1/financemanage/expenditure/add?apihelptype=save
```

##### 费用报销报销人员

**端点**: `/webapi/v3/ov1/systemManage/gate_list?sort=2&stype=radio`

```http
POST /webapi/v3/ov1/systemManage/gate_list?sort=2&stype=radio
```

##### 编辑费用报销明细列表

**端点**: `/webapi/v3/ov1/financemanage/expenditure/mxlist`

```http
POST /webapi/v3/ov1/financemanage/expenditure/mxlist
```

##### 获取费用报销详情

**端点**: `/webapi/v3/ov1/financemanage/expenditure/add?edit=1&apihelptype=get`

```http
POST /webapi/v3/ov1/financemanage/expenditure/add?edit=1&apihelptype=get
```

##### 获取费用报销列表

**端点**: `/webapi/v3/ov1/financemanage/expenditure/list`

```http
POST /webapi/v3/ov1/financemanage/expenditure/list
```

##### 费用报销审批

**端点**: `/webapi/v3/ov1/systemmanage/approve?dtype=4&apihelptype=save`

```http
POST /webapi/v3/ov1/systemmanage/approve?dtype=4&apihelptype=save
```

##### 费用报销出账

**端点**: `/webapi/v3/ov1/financeManage/expenditure/bankout?apihelptype=save`

```http
POST /webapi/v3/ov1/financeManage/expenditure/bankout?apihelptype=save
```

#### 费用借款对接

##### 添加费用借款

**端点**: `/webapi/v3/ov1/financemanage/borrow/add?edit=1&apihelptype=save`

```http
POST /webapi/v3/ov1/financemanage/borrow/add?edit=1&apihelptype=save
```

##### 费用借款借款人员

**端点**: `/webapi/v3/ov1/systemManage/gate_list?sort=2&stype=radio`

```http
POST /webapi/v3/ov1/systemManage/gate_list?sort=2&stype=radio
```

##### 获取费用借款详情

**端点**: `/webapi/v3/ov1/financemanage/borrow/add?apihelptype=get`

```http
POST /webapi/v3/ov1/financemanage/borrow/add?apihelptype=get
```

##### 获取费用借款列表

**端点**: `/webapi/v3/ov1/financemanage/borrow/list`

```http
POST /webapi/v3/ov1/financemanage/borrow/list
```

##### 费用借款审批

**端点**: `/webapi/v3/ov1/systemmanage/approve?dtype=6&apihelptype=save`

```http
POST /webapi/v3/ov1/systemmanage/approve?dtype=6&apihelptype=save
```

##### 费用借款出账

**端点**: `/webapi/v3/ov1/financemanage/borrow/chuzhang?apihelptype=save`

```http
POST /webapi/v3/ov1/financemanage/borrow/chuzhang?apihelptype=save
```

##### 费用借款返还

**端点**: `/webapi/v3/ov1/financeManage/reimburse/add?edit=1&datatype=borrow&apihelptype=save`

```http
POST /webapi/v3/ov1/financeManage/reimburse/add?edit=1&datatype=borrow&apihelptype=save
```

#### 费用返还对接

##### 添加费用返还

**端点**: `/webapi/v3/ov1/financemanage/reimburse/add?edit=1&apihelptype=save`

```http
POST /webapi/v3/ov1/financemanage/reimburse/add?edit=1&apihelptype=save
```

##### 费用返还关联借款单

**端点**: `/webapi/v3/ov1/financeManage/borrow/list?datatype=addreimburse&checktype=radio`

```http
POST /webapi/v3/ov1/financeManage/borrow/list?datatype=addreimburse&checktype=radio
```

##### 获取费用返还详情

**端点**: `/webapi/v3/ov1/financemanage/reimburse/add?apihelptype=get`

```http
POST /webapi/v3/ov1/financemanage/reimburse/add?apihelptype=get
```

##### 获取费用返还列表

**端点**: `/webapi/v3/ov1/financemanage/reimburse/list`

```http
POST /webapi/v3/ov1/financemanage/reimburse/list
```

##### 费用返还审批

**端点**: `/webapi/v3/ov1/systemmanage/approve?dtype=5&apihelptype=save`

```http
POST /webapi/v3/ov1/systemmanage/approve?dtype=5&apihelptype=save
```

##### 费用返还入账

**端点**: `/webapi/v3/ov1/financeManage/reimburse/ruzhang?apihelptype=save`

```http
POST /webapi/v3/ov1/financeManage/reimburse/ruzhang?apihelptype=save
```


---

## 办公栏目

### 公司公告

#### 公告对接

##### 添加或修改公司公告

**端点**: `/webapi/v3/ov1/officemanage/notice/add?apihelptype=save`

```http
POST /webapi/v3/ov1/officemanage/notice/add?apihelptype=save
```

##### 获取公司公告详情

**端点**: `/webapi/v3/ov1/officemanage/notice/add?edit=1&apihelptype=get`

```http
POST /webapi/v3/ov1/officemanage/notice/add?edit=1&apihelptype=get
```

##### 获取公司公告列表

**端点**: `/webapi/v3/ov1/officemanage/notice/list`

```http
POST /webapi/v3/ov1/officemanage/notice/list
```

### 工作互动

#### 工作互动对接

##### 添加或修改工作互动

**端点**: `/webapi/v3/ov1/officemanage/interaction/add?apihelptype=save`

```http
POST /webapi/v3/ov1/officemanage/interaction/add?apihelptype=save
```

##### 获取工作互动详情

**端点**: `/webapi/v3/ov1/officemanage/interaction/add?edit=1&apihelptype=get`

```http
POST /webapi/v3/ov1/officemanage/interaction/add?edit=1&apihelptype=get
```

##### 获取工作互动列表

**端点**: `/webapi/v3/ov1/officemanage/interaction/list`

```http
POST /webapi/v3/ov1/officemanage/interaction/list
```

##### 获取工作互动交流

**端点**: `/webapi/v3/ov1/officemanage/interaction/add?__msgid=replysave`

```http
POST /webapi/v3/ov1/officemanage/interaction/add?__msgid=replysave
```

##### 获取工作互动交流回复

**端点**: `/webapi/v3/ov1/officeManage/interaction/add?__msgid=rebacksave`

```http
POST /webapi/v3/ov1/officeManage/interaction/add?__msgid=rebacksave
```

### 日程管理

#### 日程对接

##### 添加或修改日程

**端点**: `/webapi/v3/ov1/officemanage/plan/add?apihelptype=save`

```http
POST /webapi/v3/ov1/officemanage/plan/add?apihelptype=save
```

##### 日程关联客户

**端点**: `/webapi/v3/ov1/salesManage/custom/list?checktype=radio`

```http
POST /webapi/v3/ov1/salesManage/custom/list?checktype=radio
```

##### 日程关联联系人

**端点**: `/webapi/v3/ov1/salesManage/person/list?checktype=radio`

```http
POST /webapi/v3/ov1/salesManage/person/list?checktype=radio
```

##### 日程关联项目

**端点**: `/webapi/v3/ov1/salesManage/chance/list?checktype=radio`

```http
POST /webapi/v3/ov1/salesManage/chance/list?checktype=radio
```

##### 获取日程详情

**端点**: `/webapi/v3/ov1/officemanage/plan/add?edit=1&apihelptype=get`

```http
POST /webapi/v3/ov1/officemanage/plan/add?edit=1&apihelptype=get
```

##### 获取日程列表

**端点**: `/webapi/v3/ov1/officemanage/plan/list`

```http
POST /webapi/v3/ov1/officemanage/plan/list
```

##### 日程洽谈进展

**端点**: `/webapi/v3/ov1/systemManage/reply?datatype=plan&apihelptype=save`

```http
POST /webapi/v3/ov1/systemManage/reply?datatype=plan&apihelptype=save
```

##### 日程总结

**端点**: `/webapi/v3/ov1/officeManage/plan/summary?apihelptype=save`

```http
POST /webapi/v3/ov1/officeManage/plan/summary?apihelptype=save
```

##### 日程点评

**端点**: `/webapi/v3/ov1/officeManage/plan/leaderdp?apihelptype=save`

```http
POST /webapi/v3/ov1/officeManage/plan/leaderdp?apihelptype=save
```

##### 添加或修改周报

**端点**: `/webapi/v3/ov1/officemanage/plan/add_week_month?sort=1&apihelptype=save`

```http
POST /webapi/v3/ov1/officemanage/plan/add_week_month?sort=1&apihelptype=save
```

##### 周报总结

**端点**: `/webapi/v3/ov1/officeManage/plan/summary?sort=1&apihelptype=save`

```http
POST /webapi/v3/ov1/officeManage/plan/summary?sort=1&apihelptype=save
```

##### 周报点评

**端点**: `/webapi/v3/ov1/officeManage/plan/leaderdp?sort=1&apihelptype=save`

```http
POST /webapi/v3/ov1/officeManage/plan/leaderdp?sort=1&apihelptype=save
```

##### 获取周报详情

**端点**: `/webapi/v3/ov1/officemanage/plan/add_week_month?edit=1&sort=1&apihelptype=get`

```http
POST /webapi/v3/ov1/officemanage/plan/add_week_month?edit=1&sort=1&apihelptype=get
```

##### 添加或修改月报

**端点**: `/webapi/v3/ov1/officemanage/plan/add_week_month?sort=2&apihelptype=save`

```http
POST /webapi/v3/ov1/officemanage/plan/add_week_month?sort=2&apihelptype=save
```

##### 月报总结

**端点**: `/webapi/v3/ov1/officeManage/plan/summary?sort=2&apihelptype=save`

```http
POST /webapi/v3/ov1/officeManage/plan/summary?sort=2&apihelptype=save
```

##### 月报点评

**端点**: `/webapi/v3/ov1/officeManage/plan/leaderdp?sort=2&apihelptype=save`

```http
POST /webapi/v3/ov1/officeManage/plan/leaderdp?sort=2&apihelptype=save
```

##### 获取月报详情

**端点**: `/webapi/v3/ov1/officemanage/plan/add_week_month?edit=1&sort=2&apihelptype=get`

```http
POST /webapi/v3/ov1/officemanage/plan/add_week_month?edit=1&sort=2&apihelptype=get
```

### 通讯录关联

#### 通讯录对接

##### 获取通讯录列表

**端点**: `/webapi/v3/ov1/officemanage/businesscard/list`

```http
POST /webapi/v3/ov1/officemanage/businesscard/list
```

##### 获取组织架构

**端点**: `/webapi/v3/ov1/officemanage/businesscard/list?sort=1&reportmodel=tree`

```http
POST /webapi/v3/ov1/officemanage/businesscard/list?sort=1&reportmodel=tree
```

##### 获取通讯录详情

**端点**: `/webapi/v3/ov1/officemanage/businesscard/content?apihelptype=get`

```http
POST /webapi/v3/ov1/officemanage/businesscard/content?apihelptype=get
```


---

## 研发

### 物料清单

#### 物料清单对接

##### 物料清单添加

**端点**: `/webapi/v3/produceV2/bom/add`

```http
POST /webapi/v3/produceV2/bom/add
```

##### 物料清单修改

**端点**: `/webapi/v3/produceV2/bom/edit`

```http
POST /webapi/v3/produceV2/bom/edit
```

##### 物料清单删除

**端点**: `/webapi/v3/produceV2/bom/delete`

```http
POST /webapi/v3/produceV2/bom/delete
```

##### 物料清单详情

**端点**: `/webapi/v3/produceV2/bom/detail`

```http
POST /webapi/v3/produceV2/bom/detail
```

##### 物料清单列表

**端点**: `/webapi/v3/produceV2/bom/list`

```http
POST /webapi/v3/produceV2/bom/list
```

### 物料替代

#### 物料替代对接

##### 物料替代添加

**端点**: `/webapi/v3/produce/material/substitution/add`

```http
POST /webapi/v3/produce/material/substitution/add
```

##### 物料替代修改

**端点**: `/webapi/v3/produce/material/substitution/edit`

```http
POST /webapi/v3/produce/material/substitution/edit
```

##### 物料替代详情

**端点**: `/webapi/v3/produce/material/substitution/detail`

```http
POST /webapi/v3/produce/material/substitution/detail
```

##### 物料替代列表

**端点**: `/webapi/v3/produce/material/substitution/list`

```http
POST /webapi/v3/produce/material/substitution/list
```


---

## 人资栏目

### 考勤管理

#### 考勤导入

##### 考勤导入添加

**端点**: `/webapi/v3/attendance/attendancemanage/record/add`

```http
POST /webapi/v3/attendance/attendancemanage/record/add
```


---

