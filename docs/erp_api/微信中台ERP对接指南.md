# 智邦ERP与微信中台对接指南

**生成时间**: 2025-10-19 12:43:10

---

## 🎯 核心对接场景

### 1. 客户信息同步

从微信中台同步客户信息到ERP系统

**相关API**: 单位客户添加, 个人客户添加, 客户列表, 客户详情, 客户修改

**关键字段**: `name, mobile, weixinAcc, ly, khid, address, intro`

#### 单位客户添加

- **接口**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/add.asp?intsort=1`
- **方式**: HTTP | POST
- **关键参数**:
  - `name` (string): 客户名称，文本，必填，100字以内
  - `khid` (string): 客户编号，文本，50字以内
  - `ly` (int): 客户来源，整型，枚举类型，如：173:陌生开发、171:网站注册、977:VIP、174:广告宣传、172:朋友介绍。
  - `address` (string): 客户地址，文本，200字以内
  - `mobile` (string): 手 机 ，文本，50字以内
  - `weixinAcc` (string): 微 信，文本，50字以内
  - `intro` (string): 备 注 ，文本，4000字以内

#### 个人客户添加

- **接口**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/add.asp?intsort=2`
- **方式**: HTTP | POST
- **关键参数**:
  - `name` (string): 客户名称，文本，必填，100字以内
  - `khid` (string): 客户编号，文本，50字以内
  - `ly` (int): 客户来源，整型，枚举类型，如：173:陌生开发、171:网站注册、977:VIP、174:广告宣传、172:朋友介绍。
  - `address` (string): 客户地址，文本，200字以内
  - `mobile` (string): 手 机 ，文本，50字以内
  - `weixinAcc` (string): 微 信，文本，50字以内
  - `intro` (string): 备 注 ，文本，4000字以内

#### 客户列表

- **接口**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/list.asp`
- **方式**: HTTP | POST
- **关键参数**:
  - `name` (string): 客户名称，文本，默认为空，模糊检索条件
  - `khid` (string): 客户编号，文本，默认为空，模糊检索条件
  - `ly` (string): 客户来源，文本，默认为空，多选项检索条件，枚举类型，多个值之间用逗号隔开(如：11,23...)。
  - `address` (string): 客户地址，文本，默认为空，模糊检索条件
  - `intro` (string): 备 注 ，文本，默认为空，模糊检索条件

#### 客户详情

- **接口**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/add.asp?edit=1`
- **方式**: HTTP | POST

#### 客户修改

- **接口**: `http://ls1.jmt.ink:46088/webapi/v3/sales/customer/edit`
- **方式**: HTTP | POST
- **关键参数**:
  - `name` (string): 客户名称 由策略控制是否必填；作为查重规则时要避免重复
  - `khid` (string): 客户编号 由策略控制是否必填；作为查重规则时要避免重复；客户的唯一编号
  - `ly` (string): 客户来源 由策略控制是否必填
  - `address` (string): 客户地址 由策略控制是否必填
  - `intro` (string): 备注 对写入客户的额外说明
  - `mobile` (string): 联系人手机 由策略控制是否必填；支持输入0-9的正整数，作为查重规则时要避免重复；格式需满足11位的有效手机号码
  - `weixinAcc` (string): 联系人微信 由策略控制是否必填；录入联系人的微信联系方式

---

### 2. 跟进记录同步

同步微信沟通记录到ERP跟进记录

**相关API**: 洽谈进展, 联系人添加, 联系人列表

**关键字段**: `ord, intro, person_name, mobile, email`

#### 洽谈进展

- **接口**: `http://ls1.jmt.ink:46088/sysa/mobilephone/systemmanage/reply.asp?datatype=tel`
- **方式**: HTTP | POST
- **关键参数**:
  - `ord` (int): 数据唯一标识，整型，通用型字段，一般添加新资料时不需要传该字段，修改资料时为对应资料的唯一标识字段值，可从相应的列表接口获取。
  - `intro` (string): 选择模板，文本，必填，1000字以内，枚举类型，如：106:谈的很好，让发合同。、107:电话无人接听。、108:现在还没考虑。、109:今天谈的不错，让明天面谈。、120:正在考虑中。

#### 联系人添加

- **接口**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/person/add.asp`
- **方式**: HTTP | POST
- **关键参数**:
  - `ord` (int): 数据唯一标识，整型，通用型字段，一般添加新资料时不需要传该字段，修改资料时为对应资料的唯一标识字段值，可从相应的列表接口获取。
  - `person_name` (string): 联系人姓名，文本，必填，50字以内
  - `mobile` (string): 手 机 ，文本，50字以内
  - `email` (string): 电子邮件，文本，50字以内
  - `intro` (string): 备　　注，文本，5000字以内

#### 联系人列表

- **接口**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/person/list.asp`
- **方式**: HTTP | POST
- **关键参数**:
  - `person_name` (string): 联系人姓名，文本，默认为空，模糊检索条件
  - `mobile` (string): 手 机 ，文本，默认为空，模糊检索条件
  - `email` (string): 电子邮件，文本，默认为空，模糊检索条件
  - `intro` (string): 联系人备注，文本，默认为空，模糊检索条件

---

### 3. 客户分配管理

根据中台评分自动分配客户给销售

**相关API**: 客户指派, 客户申请, 客户审批, 客户收回

**关键字段**: `ord, member1, member2`

#### 客户指派

- **接口**: `http://ls1.jmt.ink:46088/sysa/mobilephone/systemmanage/order.asp?datatype=tel`
- **方式**: HTTP | POST
- **关键参数**:
  - `ord` (int): 数据唯一标识，整型，通用型字段，一般添加新资料时不需要传该字段，修改资料时为对应资料的唯一标识字段值，可从相应的列表接口获取。
  - `member1` (int): 指派方式，整型，必填，枚举类型，如：1:对所有用户公开、0:指派给以下用户。
  - `member2` (string): 指派用户，文本，50字以内， 来自树结构数据：点击查看数据。

#### 客户申请

- **接口**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/apply.asp`
- **方式**: HTTP | POST
- **关键参数**:
  - `ord` (string): 数据唯一标识，客户ID值,可通过客户列表获取。

#### 客户审批

- **接口**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/approve.asp?__msgid=onsave`
- **方式**: HTTP | POST
- **关键参数**:
  - `ord` (string): 数据唯一标识，客户ID值,可通过客户列表获取。

#### 客户收回

- **接口**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/takeback.asp`
- **方式**: HTTP | POST
- **关键参数**:
  - `ord` (string): 数据唯一标识，客户ID值,可通过客户列表获取。

---

### 4. 客户来源追踪

标记客户来源为微信渠道

**相关API**: 客户添加, 客户修改

**关键字段**: `ly`

#### 单位客户添加

- **接口**: `http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/add.asp?intsort=1`
- **方式**: HTTP | POST
- **关键参数**:
  - `ly` (int): 客户来源，整型，枚举类型，如：173:陌生开发、171:网站注册、977:VIP、174:广告宣传、172:朋友介绍。

#### 客户修改

- **接口**: `http://ls1.jmt.ink:46088/webapi/v3/sales/customer/edit`
- **方式**: HTTP | POST
- **关键参数**:
  - `ly` (string): 客户来源 由策略控制是否必填

---

## 💡 实施建议

### 数据映射表

| 微信中台字段 | ERP字段 | 说明 |
|--------------|---------|------|
| contact.name | name | 客户名称 |
| contact.phone | mobile | 手机号码 |
| contact.wechat_id | weixinAcc | 微信号 |
| contact.company | name (单位客户) | 公司名称 |
| contact.source | ly | 客户来源（设置为"微信"） |
| contact.notes | intro | 备注信息 |
| thread.score | jz | 价值评估 |
| signal.content | product | 客户简介/沟通记录 |

### 同步策略

1. **准入条件**:
   - 手机号已验证
   - 客户名称完整
   - 通过白名单评分（score >= 60）

2. **同步时机**:
   - 客户从灰名单升级到白名单时
   - 客户完成首次成交时
   - 手动触发同步

3. **冲突解决**:
   - ERP客户编号(khid)为主键
   - 手机号去重
   - 微信号补充到ERP

