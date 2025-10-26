# 智邦国际ERP - API完整索引

**生成时间**: 2025-10-19 09:58:11  
**API总数**: 219  
**已有详细文档**: 8个  

---

## 📊 API统计

- 总计: **219** 个API
- 已有详细参数: **8** 个
- 待补充: **211** 个

---

## 📋 分类索引

### 人资栏目/考勤管理/考勤导入 (1个)

⏳ **考勤导入添加**
   - 接口: `/webapi/v3/attendance/attendancemanage/record/add`
   - ID: 314

---

### 办公栏目/公司公告/公告对接 (3个)

⏳ **添加或修改公司公告**
   - 接口: `/webapi/v3/ov1/officemanage/notice/add?apihelptype=save`
   - ID: 192

⏳ **获取公司公告详情**
   - 接口: `/webapi/v3/ov1/officemanage/notice/add?edit=1&apihelptype=get`
   - ID: 193

⏳ **获取公司公告列表**
   - 接口: `/webapi/v3/ov1/officemanage/notice/list`
   - ID: 194

---

### 办公栏目/工作互动/工作互动对接 (5个)

⏳ **添加或修改工作互动**
   - 接口: `/webapi/v3/ov1/officemanage/interaction/add?apihelptype=save`
   - ID: 197

⏳ **获取工作互动详情**
   - 接口: `/webapi/v3/ov1/officemanage/interaction/add?edit=1&apihelptype=get`
   - ID: 198

⏳ **获取工作互动列表**
   - 接口: `/webapi/v3/ov1/officemanage/interaction/list`
   - ID: 199

⏳ **获取工作互动交流**
   - 接口: `/webapi/v3/ov1/officemanage/interaction/add?__msgid=replysave`
   - ID: 200

⏳ **获取工作互动交流回复**
   - 接口: `/webapi/v3/ov1/officeManage/interaction/add?__msgid=rebacksave`
   - ID: 201

---

### 办公栏目/日程管理/日程对接 (17个)

⏳ **添加或修改日程**
   - 接口: `/webapi/v3/ov1/officemanage/plan/add?apihelptype=save`
   - ID: 204

⏳ **日程关联客户**
   - 接口: `/webapi/v3/ov1/salesManage/custom/list?checktype=radio`
   - ID: 205

⏳ **日程关联联系人**
   - 接口: `/webapi/v3/ov1/salesManage/person/list?checktype=radio`
   - ID: 206

⏳ **日程关联项目**
   - 接口: `/webapi/v3/ov1/salesManage/chance/list?checktype=radio`
   - ID: 207

⏳ **获取日程详情**
   - 接口: `/webapi/v3/ov1/officemanage/plan/add?edit=1&apihelptype=get`
   - ID: 208

⏳ **获取日程列表**
   - 接口: `/webapi/v3/ov1/officemanage/plan/list`
   - ID: 209

⏳ **日程洽谈进展**
   - 接口: `/webapi/v3/ov1/systemManage/reply?datatype=plan&apihelptype=save`
   - ID: 210

⏳ **日程总结**
   - 接口: `/webapi/v3/ov1/officeManage/plan/summary?apihelptype=save`
   - ID: 211

⏳ **日程点评**
   - 接口: `/webapi/v3/ov1/officeManage/plan/leaderdp?apihelptype=save`
   - ID: 212

⏳ **添加或修改周报**
   - 接口: `/webapi/v3/ov1/officemanage/plan/add_week_month?sort=1&apihelptype=save`
   - ID: 213

⏳ **周报总结**
   - 接口: `/webapi/v3/ov1/officeManage/plan/summary?sort=1&apihelptype=save`
   - ID: 214

⏳ **周报点评**
   - 接口: `/webapi/v3/ov1/officeManage/plan/leaderdp?sort=1&apihelptype=save`
   - ID: 215

⏳ **获取周报详情**
   - 接口: `/webapi/v3/ov1/officemanage/plan/add_week_month?edit=1&sort=1&apihelptype=get`
   - ID: 216

⏳ **添加或修改月报**
   - 接口: `/webapi/v3/ov1/officemanage/plan/add_week_month?sort=2&apihelptype=save`
   - ID: 217

⏳ **月报总结**
   - 接口: `/webapi/v3/ov1/officeManage/plan/summary?sort=2&apihelptype=save`
   - ID: 218

⏳ **月报点评**
   - 接口: `/webapi/v3/ov1/officeManage/plan/leaderdp?sort=2&apihelptype=save`
   - ID: 219

⏳ **获取月报详情**
   - 接口: `/webapi/v3/ov1/officemanage/plan/add_week_month?edit=1&sort=2&apihelptype=get`
   - ID: 220

---

### 办公栏目/通讯录关联/通讯录对接 (3个)

⏳ **获取通讯录列表**
   - 接口: `/webapi/v3/ov1/officemanage/businesscard/list`
   - ID: 223

⏳ **获取组织架构**
   - 接口: `/webapi/v3/ov1/officemanage/businesscard/list?sort=1&reportmodel=tree`
   - ID: 224

⏳ **获取通讯录详情**
   - 接口: `/webapi/v3/ov1/officemanage/businesscard/content?apihelptype=get`
   - ID: 225

---

### 库存栏目/产品管理/产品对接 (9个)

⏳ **获取产品单位列表**
   - 接口: `/webapi/apiHelper/sale/Product/GetProductUnitLists`
   - ID: 89

⏳ **获取产品分类信息**
   - 接口: `/webapi/v3/ov1/systemManage/product_sort_list?stype=check&apihelptype=get`
   - ID: 90

⏳ **获取发票类型列表**
   - 接口: `/webapi/apiHelper/sale/Product/GetInvoiceTypesLists`
   - ID: 91

⏳ **获取产品列表**
   - 接口: `/webapi/v3/ov1/salesmanage/product/billlist`
   - ID: 92

⏳ **获取产品详情**
   - 接口: `/webapi/v3/ov1/salesmanage/product/billService?apihelptype=get`
   - ID: 93

⏳ **产品加入合同**
   - 接口: `/webapi/v3/ov1/salesmanage/contract/contractlist?__msgId=addToContract`
   - ID: 94

⏳ **产品批量添加**
   - 接口: `/webapi/v3/store/productbatch/add`
   - ID: 304

⏳ **产品添加**
   - 接口: `/webapi/v3/store/product/add`
   - ID: 305

⏳ **产品修改**
   - 接口: `/webapi/v3/store/product/edit`
   - ID: 306

---

### 库存栏目/入库管理/入库对接 (7个)

⏳ **获取入库列表**
   - 接口: `/webapi/v3/ov1/storemanage/kuin/list`
   - ID: 77

⏳ **获取入库详情**
   - 接口: `/webapi/v3/ov1/storemanage/kuin/detail?apihelptype=get`
   - ID: 78

⏳ **获取入库产品明细**
   - 接口: `/webapi/v3/ov1/storemanage/kuin/MoreKuinList`
   - ID: 79

⏳ **入库成本修改**
   - 接口: `/webapi/v3/store/kuin/costmodify/edit`
   - ID: 244

⏳ **入库确认**
   - 接口: `/webapi/v3/store/kuin/surekuin/edit`
   - ID: 245

⏳ **入库确认（32.15及以后）**
   - 接口: `/webapi/v3/store/KuInApplyEdit/edit`
   - ID: 309

⏳ **入库列表（32.15及以后）**
   - 接口: `/webapi/v3/store/KuInApplyList`
   - ID: 310

---

### 库存栏目/入库管理/直接入库 (1个)

⏳ **直接入库添加**
   - 接口: `/webapi/v3/store/kuin/add`
   - ID: 243

---

### 库存栏目/出库管理/出库对接 (7个)

⏳ **出库确认**
   - 接口: `/webapi/v3/store/kuout/surekuout/edit`
   - ID: 239

⏳ **出库详情**
   - 接口: `/webapi/v3/store/kuout/detail`
   - ID: 240

⏳ **出库列表**
   - 接口: `/webapi/v3/store/kuout/List`
   - ID: 241

⏳ **库存操作修改**
   - 接口: `/webapi/v3/store/inventory/edit`
   - ID: 248

⏳ **库存操作详情**
   - 接口: `/webapi/v3/store/inventory/detail`
   - ID: 249

⏳ **出库确认（32.15及以后）**
   - 接口: `/webapi/v3/store/KuOutApplyEdit/edit`
   - ID: 307

⏳ **出库列表（32.15及以后）**
   - 接口: `/webapi/v3/store/KuOutApplyList`
   - ID: 308

---

### 库存栏目/发货管理/发货对接 (3个)

⏳ **获取发货详情**
   - 接口: `/webapi/v3/ov1/storemanage/sent/detail?apihelptype=get`
   - ID: 84

⏳ **获取发货产品明细**
   - 接口: `/webapi/v3/ov1/storemanage/sent/moresendlist`
   - ID: 85

⏳ **获取发货列表**
   - 接口: `/webapi/v3/ov1/storemanage/sent/list`
   - ID: 86

---

### 库存栏目/库存查看/仓库对接 (3个)

⏳ **获取仓库列表**
   - 接口: `/webapi/apiHelper/stock/Stock/GetWarehouses`
   - ID: 74

⏳ **获取库位列表**
   - 接口: `/webapi/v3/uview/stock/Pages/WareHouse/SettingApiList`
   - ID: 299

⏳ **获取仓库列表（32.15及以后）**
   - 接口: `/webapi/v3/store/WareHouseStructList`
   - ID: 300

---

### 库存栏目/库存查看/库存查看对接 (4个)

⏳ **获取库存详情**
   - 接口: `/webapi/v3/ov1/storemanage/store/content?apihelptype=get`
   - ID: 71

⏳ **获取库存查看列表**
   - 接口: `/webapi/v3/ov1/storemanage/store/list`
   - ID: 72

⏳ **产品库存明细列表**
   - 接口: `/webapi/v3/store/inventory/InventoryDetails`
   - ID: 246

⏳ **产品库存汇总列表**
   - 接口: `/webapi/v3/store/inventory/InventorySummary`
   - ID: 247

---

### 未分类 (2个)

⏳ **概述**
   - 接口: `remark.html`
   - ID: 1

⏳ **对接须知**
   - 接口: `infnotice.html`
   - ID: 2

---

### 生产栏目/工序汇报管理/工序汇报计划 (8个)

⏳ **工序汇报添加**
   - 接口: `/webapi/v3/produceV2/processreport/add`
   - ID: 263

⏳ **工序汇报删除**
   - 接口: `/webapi/v3/produceV2/processreport/delete`
   - ID: 264

⏳ **工序汇报计划**
   - 接口: `/webapi/v3/produceV2/procedure/planlist`
   - ID: 265

⏳ **工序汇报详情**
   - 接口: `/webapi/v3/produceV2/processreport/detail`
   - ID: 266

⏳ **工序汇报列表查询(明细)**
   - 接口: `/webapi/v3/produceV2/processreportlist/detail`
   - ID: 267

⏳ **工序汇报列表查询(汇总)**
   - 接口: `/webapi/v3/produceV2/processreportlist/summary`
   - ID: 268

⏳ **工序汇报修改**
   - 接口: `/webapi/v3/produceV2/processreport/edit`
   - ID: 269

⏳ **获取工序任务列表**
   - 接口: `/webapi/v3/produceV2/ProcessReportTaskList/List`
   - ID: 317

---

### 生产栏目/工序管理/岗位对接 (1个)

⏳ **岗位列表**
   - 接口: `/webapi/v3/produceV2/workflow/workingprocedure/jobs/list`
   - ID: 315

---

### 生产栏目/工序管理/工序分类对接 (1个)

⏳ **工序分类列表**
   - 接口: `/webapi/v3/produceV2/workflow/workingprocedure/class/list`
   - ID: 316

---

### 生产栏目/工序管理/工序对接 (4个)

⏳ **工序添加**
   - 接口: `/webapi/v3/produceV2/workflow/workingprocedure/add`
   - ID: 256

⏳ **工序修改**
   - 接口: `/webapi/v3/produceV2/workflow/workingprocedure/edit`
   - ID: 257

⏳ **工序详情**
   - 接口: `/webapi/v3/produceV2/workflow/workingprocedure/detail`
   - ID: 258

⏳ **工序列表**
   - 接口: `/webapi/v3/produceV2/workflow/workingprocedure/list`
   - ID: 260

---

### 生产栏目/工艺路线管理/工艺路线对接 (4个)

⏳ **工艺路线添加**
   - 接口: `/webapi/v3/produceV2/workflow/workingflow/add`
   - ID: 253

⏳ **工艺路线修改**
   - 接口: `/webapi/v3/produceV2/workflow/workingflow/edit`
   - ID: 254

⏳ **工艺路线详情**
   - 接口: `/webapi/v3/produceV2/workflow/workingflow/detail`
   - ID: 255

⏳ **工艺路线列表**
   - 接口: `/webapi/v3/produceV2/workflow/workingflow/list`
   - ID: 259

---

### 生产栏目/派工管理/派工对接 (2个)

⏳ **派工添加**
   - 接口: `/webapi/apiHelper/produce/WorkAssigns/SaveWorkAssigns`
   - ID: 110

⏳ **获取派工列表**
   - 接口: `/webapi/apiHelper/produce/WorkAssigns/GetWorkAssigns`
   - ID: 111

---

### 生产栏目/物料清单管理/物料清单对接 (2个)

⏳ **物料清单添加/修改(适用V32.10已有功能)**
   - 接口: `/webapi/apiHelper/produce/Bom/SaveBoms`
   - ID: 97

⏳ **物料清单列表(适用V32.10已有功能)**
   - 接口: `/webapi/apiHelper/produce/Bom/GetBoms`
   - ID: 98

---

### 生产栏目/物料登记管理/物料登记对接 (2个)

⏳ **物料登记添加**
   - 接口: `/webapi/apiHelper/produce/MaterialRegister/SaveMaterialRegisters`
   - ID: 129

⏳ **获取物料登记列表**
   - 接口: `/webapi/apiHelper/produce/MaterialRegister/GetMaterialRegisters`
   - ID: 130

---

### 生产栏目/生产质检管理/生产质检对接 (9个)

⏳ **生产质检任务添加**
   - 接口: `/webapi/apiHelper/produce/QualityTesting/SaveQualityTestingsTask`
   - ID: 118

⏳ **获取生产质检任务列表**
   - 接口: `/webapi/apiHelper/produce/QualityTesting/GetQualityTestingTasks`
   - ID: 119

⏳ **生产质检添加/修改**
   - 接口: `/webapi/apiHelper/produce/QualityTesting/SaveQualityTestings`
   - ID: 120

⏳ **获取生产质检计划**
   - 接口: `/webapi/apiHelper/produce/QualityTesting/GetQualityTestingPlans`
   - ID: 121

⏳ **获取生产质检列表**
   - 接口: `/webapi/apiHelper/produce/QualityTesting/GetQualityTestings`
   - ID: 122

⏳ **生产质检审核**
   - 接口: `/webapi/apiHelper/produce/QualityTesting/CheckQualityTestings`
   - ID: 123

⏳ **获取不合格原因列表**
   - 接口: `/webapi/apiHelper/produce/QualityTesting/GetUnQualiFiedList`
   - ID: 124

⏳ **获取报废原因列表**
   - 接口: `/webapi/apiHelper/produce/QualityTesting/GetScrapReasonList`
   - ID: 125

⏳ **获取质量等级列表**
   - 接口: `/webapi/apiHelper/produce/QualityTesting/GetQualityLevelList`
   - ID: 126

---

### 生产栏目/设备管理/设备对接 (2个)

⏳ **获取设备列表**
   - 接口: `/webapi/apiHelper/produce/Machine/GetMachines`
   - ID: 101

⏳ **设备添加**
   - 接口: `/webapi/v3/produce/Machine/add`
   - ID: 324

---

### 生产栏目/领料管理/领料对接 (2个)

⏳ **领料添加**
   - 接口: `/webapi/apiHelper/produce/MaterialOrder/SaveMaterialOrders`
   - ID: 114

⏳ **获取领料列表**
   - 接口: `/webapi/apiHelper/produce/MaterialOrder/GetMaterialOrders`
   - ID: 115

---

### 研发/物料替代/物料替代对接 (4个)

⏳ **物料替代添加**
   - 接口: `/webapi/v3/produce/material/substitution/add`
   - ID: 320

⏳ **物料替代修改**
   - 接口: `/webapi/v3/produce/material/substitution/edit`
   - ID: 321

⏳ **物料替代详情**
   - 接口: `/webapi/v3/produce/material/substitution/detail`
   - ID: 322

⏳ **物料替代列表**
   - 接口: `/webapi/v3/produce/material/substitution/list`
   - ID: 323

---

### 研发/物料清单/物料清单对接 (5个)

⏳ **物料清单添加**
   - 接口: `/webapi/v3/produceV2/bom/add`
   - ID: 273

⏳ **物料清单修改**
   - 接口: `/webapi/v3/produceV2/bom/edit`
   - ID: 274

⏳ **物料清单删除**
   - 接口: `/webapi/v3/produceV2/bom/delete`
   - ID: 275

⏳ **物料清单详情**
   - 接口: `/webapi/v3/produceV2/bom/detail`
   - ID: 276

⏳ **物料清单列表**
   - 接口: `/webapi/v3/produceV2/bom/list`
   - ID: 277

---

### 组织架构/账号管理/账号对接 (5个)

⏳ **账号列表**
   - 接口: `/webapi/v3/orgs/user/list`
   - ID: 231

⏳ **账号添加**
   - 接口: `/webapi/v3/orgs/user/add`
   - ID: 278

⏳ **账号修改**
   - 接口: `/webapi/v3/orgs/user/edit`
   - ID: 279

⏳ **账号删除**
   - 接口: `/webapi/v3/orgs/user/delete`
   - ID: 280

⏳ **账号详情**
   - 接口: `/webapi/v3/orgs/user/detail`
   - ID: 281

---

### 组织架构/部门管理/部门对接 (4个)

⏳ **部门列表**
   - 接口: `/webapi/v3/orgs/dept/list`
   - ID: 228

⏳ **部门添加**
   - 接口: `/webapi/v3/orgs/dept/add`
   - ID: 232

⏳ **部门修改**
   - 接口: `/webapi/v3/orgs/dept/edit`
   - ID: 233

⏳ **部门详情**
   - 接口: `/webapi/v3/orgs/dept/detail`
   - ID: 234

---

### 财务栏目/付款收票管理/付款对接 (2个)

⏳ **获取付款详情**
   - 接口: `/webapi/v3/ov1/financemanage/moneyout/content?apihelptype=get`
   - ID: 144

⏳ **获取付款列表**
   - 接口: `/webapi/v3/ov1/financemanage/moneyout/list`
   - ID: 145

---

### 财务栏目/收款开票管理/开票对接 (2个)

⏳ **获取开票详情**
   - 接口: `/webapi/v3/ov1/financemanage/invoiceback/content?apihelptype=get`
   - ID: 140

⏳ **获取开票列表**
   - 接口: `/webapi/v3/ov1/financemanage/invoiceback/list`
   - ID: 141

---

### 财务栏目/收款开票管理/收款对接 (2个)

⏳ **获取收款详情**
   - 接口: `/webapi/v3/ov1/financemanage/moneyback/content?apihelptype=get`
   - ID: 137

⏳ **获取收款列表**
   - 接口: `/webapi/v3/ov1/financemanage/moneyback/list`
   - ID: 138

---

### 财务栏目/现金银行/银行对接 (2个)

⏳ **获取银行账户明细**
   - 接口: `/webapi/v3/ov1/financemanage/bank/add?apihelptype=get`
   - ID: 133

⏳ **获取银行账户列表**
   - 接口: `/webapi/v3/ov1/financemanage/bank/list`
   - ID: 134

---

### 财务栏目/费用管理/费用使用对接 (9个)

⏳ **添加费用使用**
   - 接口: `/webapi/v3/ov1/financemanage/employ/add?apihelptype=save`
   - ID: 158

⏳ **费用使用关联申请单**
   - 接口: `/webapi/v3/ov1/financeManage/apply/list?datatype=1&checktype=radio`
   - ID: 159

⏳ **费用使用使用人员**
   - 接口: `/webapi/v3/ov1/systemManage/gate_list?sort=2&stype=radio`
   - ID: 160

⏳ **编辑费用使用明细列表**
   - 接口: `/webapi/v3/ov1/financemanage/employ/mxlist`
   - ID: 161

⏳ **编辑费用使用明细删除**
   - 接口: `/webapi/v3/ov1/financemanage/employ/mxlist?__msgId=delete&batch=0`
   - ID: 162

⏳ **编辑费用使用明细**
   - 接口: `/webapi/v3/ov1/financemanage/employ/mxedit?apihelptype=save`
   - ID: 163

⏳ **编辑费用使用明细类型选择**
   - 接口: `/webapi/v3/ov1/financemanage/apply/getsortfields?apihelptype=get`
   - ID: 164

⏳ **获取费用使用详情**
   - 接口: `/webapi/v3/ov1/financemanage/employ/add?edit=1&apihelptype=get`
   - ID: 165

⏳ **获取费用使用列表**
   - 接口: `/webapi/v3/ov1/financemanage/employ/list`
   - ID: 166

---

### 财务栏目/费用管理/费用借款对接 (7个)

⏳ **添加费用借款**
   - 接口: `/webapi/v3/ov1/financemanage/borrow/add?edit=1&apihelptype=save`
   - ID: 176

⏳ **费用借款借款人员**
   - 接口: `/webapi/v3/ov1/systemManage/gate_list?sort=2&stype=radio`
   - ID: 177

⏳ **获取费用借款详情**
   - 接口: `/webapi/v3/ov1/financemanage/borrow/add?apihelptype=get`
   - ID: 178

⏳ **获取费用借款列表**
   - 接口: `/webapi/v3/ov1/financemanage/borrow/list`
   - ID: 179

⏳ **费用借款审批**
   - 接口: `/webapi/v3/ov1/systemmanage/approve?dtype=6&apihelptype=save`
   - ID: 180

⏳ **费用借款出账**
   - 接口: `/webapi/v3/ov1/financemanage/borrow/chuzhang?apihelptype=save`
   - ID: 181

⏳ **费用借款返还**
   - 接口: `/webapi/v3/ov1/financeManage/reimburse/add?edit=1&datatype=borrow&apihelptype=save`
   - ID: 182

---

### 财务栏目/费用管理/费用报销对接 (7个)

⏳ **添加费用报销**
   - 接口: `/webapi/v3/ov1/financemanage/expenditure/add?apihelptype=save`
   - ID: 168

⏳ **费用报销报销人员**
   - 接口: `/webapi/v3/ov1/systemManage/gate_list?sort=2&stype=radio`
   - ID: 169

⏳ **编辑费用报销明细列表**
   - 接口: `/webapi/v3/ov1/financemanage/expenditure/mxlist`
   - ID: 170

⏳ **获取费用报销详情**
   - 接口: `/webapi/v3/ov1/financemanage/expenditure/add?edit=1&apihelptype=get`
   - ID: 171

⏳ **获取费用报销列表**
   - 接口: `/webapi/v3/ov1/financemanage/expenditure/list`
   - ID: 172

⏳ **费用报销审批**
   - 接口: `/webapi/v3/ov1/systemmanage/approve?dtype=4&apihelptype=save`
   - ID: 173

⏳ **费用报销出账**
   - 接口: `/webapi/v3/ov1/financeManage/expenditure/bankout?apihelptype=save`
   - ID: 174

---

### 财务栏目/费用管理/费用申请对接 (9个)

⏳ **添加费用申请**
   - 接口: `/webapi/v3/ov1/financemanage/apply/add?apihelptype=save`
   - ID: 148

⏳ **编辑费用申请明细列表**
   - 接口: `/webapi/v3/ov1/financemanage/apply/mxlist`
   - ID: 149

⏳ **编辑费用申请明细删除**
   - 接口: `/webapi/v3/ov1/financemanage/apply/mxlist?__msgId=delete&batch=0`
   - ID: 150

⏳ **编辑费用申请明细**
   - 接口: `/webapi/v3/ov1/financemanage/apply/mxedit?apihelptype=save`
   - ID: 151

⏳ **编辑费用申请明细类型选择**
   - 接口: `/webapi/v3/ov1/financemanage/apply/getsortfields?datatype=paysq&apihelptype=get`
   - ID: 152

⏳ **获取费用申请详情**
   - 接口: `/webapi/v3/ov1/financemanage/apply/add?edit=1&apihelptype=get`
   - ID: 153

⏳ **获取费用申请列表**
   - 接口: `/webapi/v3/ov1/financemanage/apply/list`
   - ID: 154

⏳ **费用申请提交审批**
   - 接口: `/webapi/v3/ov1/systemmanage/setapprove?__msgId=save&approve=7`
   - ID: 155

⏳ **费用申请审批**
   - 接口: `/webapi/v3/ov1/systemmanage/approve?dtype=7&apihelptype=save`
   - ID: 156

---

### 财务栏目/费用管理/费用返还对接 (6个)

⏳ **添加费用返还**
   - 接口: `/webapi/v3/ov1/financemanage/reimburse/add?edit=1&apihelptype=save`
   - ID: 184

⏳ **费用返还关联借款单**
   - 接口: `/webapi/v3/ov1/financeManage/borrow/list?datatype=addreimburse&checktype=radio`
   - ID: 185

⏳ **获取费用返还详情**
   - 接口: `/webapi/v3/ov1/financemanage/reimburse/add?apihelptype=get`
   - ID: 186

⏳ **获取费用返还列表**
   - 接口: `/webapi/v3/ov1/financemanage/reimburse/list`
   - ID: 187

⏳ **费用返还审批**
   - 接口: `/webapi/v3/ov1/systemmanage/approve?dtype=5&apihelptype=save`
   - ID: 188

⏳ **费用返还入账**
   - 接口: `/webapi/v3/ov1/financeManage/reimburse/ruzhang?apihelptype=save`
   - ID: 189

---

### 采购栏目/供应商管理/供应商对接 (2个)

⏳ **供应商详情**
   - 接口: `/webapi/v3/store/supplierDetail/detail`
   - ID: 237

⏳ **供应商列表**
   - 接口: `/webapi/v3/store/supplierList`
   - ID: 238

---

### 采购栏目/采购管理/采购对接 (3个)

⏳ **获取采购列表**
   - 接口: `/webapi/v3/ov1/storemanage/caigou/list`
   - ID: 66

⏳ **获取采购详情**
   - 接口: `/webapi/v3/ov1/storemanage/caigou/add?apihelptype=get`
   - ID: 67

⏳ **获取采购审批**
   - 接口: `/webapi/v3/ov1/systemmanage/approve?dtype=3&apihelptype=save`
   - ID: 68

---

### 鉴权接口 (2个)

⏳ **登录系统**
   - 接口: `/webapi/v3/ov1/login`
   - ID: 11

⏳ **退出系统**
   - 接口: `/webapi/v3/ov1/logout`
   - ID: 12

---

### 销售栏目/合同管理/合同对接 (16个)

⏳ **添加合同明细**
   - 接口: `/webapi/v3/ov1/salesmanage/contract/contractlist?__msgId=addToContract`
   - ID: 42

⏳ **编辑合同明细列表**
   - 接口: `/webapi/v3/ov1/salesmanage/contract/contractlist`
   - ID: 43

⏳ **编辑合同明细删除**
   - 接口: `/webapi/v3/ov1/salesmanage/contract/contractlist?__msgId=delete&batch=0`
   - ID: 44

⏳ **编辑合同明细**
   - 接口: `/webapi/v3/ov1/salesmanage/contract/contractlist_edit?apihelptype=save`
   - ID: 45

⏳ **编辑合同明细单位选择**
   - 接口: `/webapi/v3/ov1/salesmanage/contract/UnitChange?ord=0&__unit=0&company=0&apihelptype=get`
   - ID: 46

⏳ **添加或修改合同**
   - 接口: `/webapi/v3/ov1/salesmanage/contract/add?apihelptype=save`
   - ID: 47

⏳ **合同关联客户**
   - 接口: `/webapi/v3/ov1/salesmanage/custom/list?datatype=addcontract&checktype=redio`
   - ID: 48

⏳ **合同关联对方代表**
   - 接口: `/webapi/v3/ov1/salesManage/person/list?checktype=radio`
   - ID: 49

⏳ **获取合同列表**
   - 接口: `/webapi/v3/ov1/salesmanage/contract/billlist`
   - ID: 50

⏳ **合同洽谈进展**
   - 接口: `/webapi/v3/ov1/systemManage/reply?datatype=contract&apihelptype=save`
   - ID: 51

⏳ **合同共享**
   - 接口: `/webapi/v3/ov1/salesManage/contract/share?apihelptype=save`
   - ID: 52

⏳ **合同审批**
   - 接口: `/webapi/v3/ov1/systemmanage/approve?dtype=2&apihelptype=save`
   - ID: 53

⏳ **合同详情**
   - 接口: `/webapi/v3/sales/contract/detail`
   - ID: 252

⏳ **合同审批修改**
   - 接口: `/webapi/v3/sales/contract/approve/edit`
   - ID: 285

⏳ **合同审批记录详情**
   - 接口: `/webapi/v3/sales/contract/approve/approveStageList/detail`
   - ID: 286

⏳ **合同添加**
   - 接口: `/webapi/v3/sale/contract/add`
   - ID: 296

---

### 销售栏目/售后服务/售后服务对接 (3个)

⏳ **获取售后服务列表**
   - 接口: `/webapi/v3/ov1/salesmanage/service/list`
   - ID: 56

⏳ **获取售后服务详情**
   - 接口: `/webapi/v3/ov1/salesmanage/service/add?apihelptype=get`
   - ID: 57

⏳ **售后服务处理**
   - 接口: `/webapi/v3/ov1/salesmanage/service/chuli?apihelptype=save`
   - ID: 58

---

### 销售栏目/售后维修/售后维修对接 (3个)

⏳ **添加或修改售后维修**
   - 接口: `/webapi/v3/ov1/salesmanage/repair/DealAdd?apihelptype=save`
   - ID: 61

⏳ **获取售后维修列表**
   - 接口: `/webapi/v3/ov1/salesmanage/repair/Deallist`
   - ID: 62

⏳ **获取售后维修详情**
   - 接口: `/webapi/v3/ov1/salesmanage/repair/Dealcontent?apihelptype=get`
   - ID: 63

---

### 销售栏目/客户管理/客户对接 (16个)

⏳ **分配新客户ID**
   - 接口: `/webapi/v3/ov1/salesmanage/custom/add?apihelptype=new`
   - ID: 15

⏳ **添加或修改单位客户**
   - 接口: `/webapi/v3/ov1/salesmanage/custom/add?intsort=1&apihelptype=save`
   - ID: 16

⏳ **添加或修改个人客户**
   - 接口: `/webapi/v3/ov1/salesmanage/custom/add?intsort=2&apihelptype=save`
   - ID: 17

✅ **获取客户详情**
   - 接口: `/webapi/v3/ov1/salesmanage/custom/add?edit=1&apihelptype=get`
   - ID: 18

✅ **获取客户列表**
   - 接口: `/webapi/v3/ov1/salesmanage/custom/list`
   - ID: 19

⏳ **客户指派**
   - 接口: `/webapi/v3/ov1/systemmanage/order?datatype=tel&apihelptype=save`
   - ID: 20

⏳ **客户收回**
   - 接口: `/webapi/v3/ov1/salesmanage/custom/takeback`
   - ID: 21

⏳ **客户申请**
   - 接口: `/webapi/v3/ov1/salesmanage/custom/apply`
   - ID: 22

⏳ **客户审批**
   - 接口: `/webapi/v3/ov1/salesmanage/custom/approve?__msgid=onsave`
   - ID: 23

⏳ **客户审核**
   - 接口: `/webapi/v3/ov1/salesManage/custom/approve_set?apihelptype=save`
   - ID: 24

✅ **客户跟进**
   - 接口: `/webapi/v3/ov1/systemManage/reply?datatype=tel&apihelptype=save`
   - ID: 25

⏳ **客户共享**
   - 接口: `/webapi/v3/ov1/salesManage/custom/share?apihelptype=save`
   - ID: 26

⏳ **客户保护**
   - 接口: `/webapi/v3/ov1/salesManage/custom/add?__msgid=profect`
   - ID: 27

⏳ **客户放弃保护**
   - 接口: `/webapi/v3/ov1/salesManage/custom/add?__msgid=unprofect`
   - ID: 28

⏳ **客户添加**
   - 接口: `/webapi/v3/sales/customer/add`
   - ID: 297

⏳ **客户修改**
   - 接口: `/webapi/v3/sales/customer/edit`
   - ID: 298

---

### 销售栏目/客户管理/客户联系人对接 (4个)

⏳ **添加或修改联系人**
   - 接口: `/webapi/v3/ov1/salesmanage/person/add?apihelptype=save`
   - ID: 30

⏳ **获取联系人详情**
   - 接口: `/webapi/v3/ov1/salesmanage/person/add?edit=1&apihelptype=get`
   - ID: 31

✅ **获取联系人列表**
   - 接口: `/webapi/v3/ov1/salesmanage/person/list`
   - ID: 32

⏳ **联系人跟进**
   - 接口: `/webapi/v3/ov1/systemManage/reply?datatype=person&apihelptype=save`
   - ID: 33

---

### 销售栏目/项目管理/项目对接 (4个)

⏳ **获取项目列表**
   - 接口: `/webapi/v3/ov1/salesmanage/chance/list`
   - ID: 36

⏳ **获取项目详情**
   - 接口: `/webapi/v3/ov1/salesmanage/chance/add?apihelptype=get`
   - ID: 37

⏳ **项目跟进**
   - 接口: `/webapi/v3/ov1/systemManage/reply?datatype=chance&apihelptype=save`
   - ID: 38

⏳ **项目审批**
   - 接口: `/webapi/v3/ov1/systemmanage/approve?dtype=25&apihelptype=save`
   - ID: 39

---

## 📖 如何获取详细参数

### 方式1: 手工复制（推荐）

1. 浏览器访问: http://ls1.jmt.ink:46088/sysn/view/OpenApi/help.ashx
2. 登录后，点击左侧菜单中的API
3. 复制右侧的参数表格
4. 粘贴到对应的文档中

### 方式2: 使用粘贴工具

```python
python3 粘贴保存工具.py
```

### 方式3: 基于现有文档开发

对于客户管理功能，已有以下API的详细文档：

- ✅ 个人客户添加
- ✅ 单位客户添加
- ✅ 客户列表
- ✅ 客户详情
- ✅ 客户跟进
- ✅ 系统登录
- ✅ 联系人列表
- ✅ 联系人添加

可以先基于这些API开发，其他API按需补充。

---

## 🎯 开发优先级建议

### P0 - 立即需要（已有详细文档）

1. ✅ **客户列表** - `/webapi/v3/ov1/salesmanage/custom/list`
2. ✅ **客户详情** - `/sysa/mobilephone/salesmanage/custom/add.asp?edit=1`
3. ✅ **单位客户添加** - `/sysa/mobilephone/salesmanage/custom/add.asp?intsort=1`
4. ✅ **客户跟进** - `/sysa/mobilephone/systemmanage/reply.asp?datatype=tel`
5. ✅ **联系人列表** - `/webapi/v3/ov1/salesmanage/person/list`
6. ✅ **系统登录** - `/webapi/v3/ov1/login`

### P1 - 后续补充

7. ⏳ 客户指派
8. ⏳ 客户收回
9. ⏳ 客户审批
10. ⏳ 联系人添加

### P2 - 扩展功能

- 项目管理相关API
- 合同管理相关API
- 产品管理相关API

---

## 📚 相关文档

| 文档 | 描述 |
|------|------|
| [智邦国际ERP_客户管理API详细文档.md](智邦国际ERP_客户管理API详细文档.md) | 客户管理核心API详细参数 |
| [客户来源字段说明.md](客户来源字段说明.md) | 客户来源字段使用指南 |
| [智邦ERP_完整API列表.json](智邦ERP_完整API列表.json) | 所有219个API的JSON列表 |
