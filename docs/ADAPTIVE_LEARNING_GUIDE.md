# 自适应学习使用指南

从零开始使用自适应对话风格学习功能。

---

## 🎯 这个功能是什么？

**让AI学习您的对话风格，实现个性化回复，越用越好！**

### 核心能力

1. **学习历史对话** → AI模仿原客服的说话方式
2. **用户画像** → 不同客户不同回复风格
3. **持续优化** → 从每次对话中学习

### 实际效果

**普通回复**：
```
客户: "充不了电"
AI: "请检查：① 电源连接 ② 充电枪接触 ③ 故障代码"
```

**个性化回复**（学习后）：
```
VIP客户（张总）: "7号桩充不了电"
AI: "张总您好，关于7号桩的问题，我立即为您查看。
     请问屏幕上有显示故障代码吗？我这边可以远程诊断。"

普通客户（李四）: "充不了电"
AI: "您好呀～别着急，先帮您看看哦
     ① 充电枪重新插一下
     ② 看看屏幕有没有显示代码
     您试试，有问题随时找我～ 😊"
```

---

## 🚀 快速开始

### 步骤1：升级数据库

```bash
# Windows
sqlite3 data\data.db < sql\upgrade_adaptive_learning.sql

# 验证
sqlite3 data\data.db "SELECT * FROM user_profiles LIMIT 1;"
```

### 步骤2：导入历史记录（可选）

#### 如果您有微信聊天记录

**方法A：使用WeChatMsg工具导出**

1. 下载WeChatMsg：https://github.com/LC044/WeChatMsg
2. 运行工具，导出聊天记录为SQLite
3. 导入到系统：

```bash
python import_wechat_history.py import \
    --file wechat_export.db \
    --groups "技术支持群" "VIP客户群"
```

**方法B：手动整理文本文件**

创建文件：`history.txt`

```
客户: 充电桩显示E03怎么办
客服: 好的，E03是通信故障呢～您先试试重新插拔充电枪

客户: 还是不行
客服: 嗯嗯，那可能需要重启一下。您断电30秒再试试

客户: 好了，谢谢
客服: 太好了～充电过程中有问题随时找我哦
```

然后导入：

```bash
python import_wechat_history.py import --file history.txt
```

#### 如果没有历史记录

**也没关系！** 系统会从新对话中自动学习。

### 步骤3：运行系统

```bash
# 系统会自动使用个性化功能
python main.py
```

系统会自动：
- 为每个用户构建画像
- 使用个性化Prompt
- 从对话中持续学习

---

## 👥 用户画像分类

### 自动分类

系统会自动将用户分为：

**客户类型**：
- **VIP**：绑定了公司名称、互动次数多、满意度高
- **普通**：一般客户
- **新客户**：首次互动

**技术水平**：
- **高**：使用专业术语（BMS、CAN总线、协议等）
- **中**：一般技术理解
- **低**：技术小白

**沟通风格**：
- **正式**：使用"您好"、"请问"等
- **友好**：一般沟通
- **随意**：使用"哈哈"、"嗯嗯"、emoji等

### 手动标记（可选）

```python
from adaptive_learning import UserProfiler
from storage.db import Database

db = Database("data/data.db")
profiler = UserProfiler(db)

# 获取画像
profile = profiler.get_or_create_profile("zhangzong", "张总")

# 手动标记为VIP
profile.customer_type = 'vip'
profile.company_name = '某某充电站运营公司'
profile.role = '运营商'

# 保存
profiler.save_profile(profile)
```

---

## 📊 个性化回复示例

### 示例1：VIP企业客户

**画像**：
```
客户类型：VIP
公司：某某充电站运营公司
技术水平：高
沟通风格：正式
```

**AI回复**：
```
张总您好，

关于7号桩的E03故障，我为您详细分析：

📊 故障信息：
- 故障代码：E03（通信故障）
- 可能原因：充电桩与车辆BMS通信异常

🔍 诊断建议：
1. 检查CAN总线连接（120Ω终端电阻）
2. 确认车辆BMS固件版本兼容性
3. 检查充电桩通信模块状态

💡 解决方案：
① 重启充电桩（断电30秒）
② 更新固件至v3.2版本
③ 如频繁出现，建议更换通信模块

是否需要安排工程师现场诊断？我可以立即为您预约。
```

**特点**：正式、详细、有数据、尊称

---

### 示例2：普通车主

**画像**：
```
客户类型：普通
技术水平：低
沟通风格：友好
```

**AI回复**：
```
您好呀～充不了电的话，别着急，咱们一步步来哦 😊

① 重新插一下充电枪
   把枪从车上拔下来，再插回去
   听到"咔哒"一声就是插好了

② 看看充电桩屏幕
   有没有显示E01、E03这种代码
   如果有，拍个照发给我

③ 试试旁边的充电桩
   有时候确实是桩的问题

您先试试，有问题随时找我哦～ 👍
```

**特点**：亲切、简单、有emoji、通俗易懂

---

## 🔄 持续学习机制

### 自动学习

**系统会自动**（无需手动操作）：

```
每次对话后：
  - 更新用户画像
  - 如果满意度≥4分 → 保存为"好例子"
  - 如果满意度<3分 → 分析问题，调整策略

每天凌晨：
  - 学习昨日高质量对话
  - 更新用户偏好

每周日：
  - 批量优化所有画像
  - 重新分析风格趋势
```

### 学习效果可视化

在飞书多维表格中：

```
用户画像统计
┌────────────────────────────────────┐
│ VIP客户：12人                       │
│ - 平均满意度：4.8分                 │
│ - 学习示例：平均8条                 │
│ - AI解决率：92%                     │
│                                     │
│ 普通客户：156人                     │
│ - 平均满意度：4.2分                 │
│ - 学习示例：平均5条                 │
│ - AI解决率：85%                     │
│                                     │
│ 新客户：23人                        │
│ - 平均满意度：3.9分                 │
│ - 学习示例：平均2条                 │
│ - AI解决率：78%                     │
└────────────────────────────────────┘

学习趋势（本月）
- 总学习次数：2,341次
- 画像更新：189次
- 新增示例：456条
- 平均满意度：4.1 → 4.3 ↑
```

---

## 💡 高级用法

### 1. 手动管理VIP客户

```python
# 标记VIP客户
python -c "
from adaptive_learning import UserProfiler
from storage.db import Database

db = Database('data/data.db')
profiler = UserProfiler(db)

profile = profiler.get_or_create_profile('zhangzong', '张总')
profile.customer_type = 'vip'
profile.company_name = '某某充电站运营公司'
profile.communication_style = 'formal'

profiler.save_profile(profile)
print('VIP客户设置完成')
"
```

### 2. 查看用户画像

```python
from adaptive_learning import UserProfiler
from storage.db import Database

db = Database('data/data.db')
profiler = UserProfiler(db)

# 查看画像
profile = profiler.get_profile('user_001')

print(f"客户类型：{profile.customer_type}")
print(f"沟通风格：{profile.communication_style}")
print(f"技术水平：{profile.technical_level}")
print(f"互动次数：{profile.total_interactions}")
print(f"平均满意度：{profile.avg_satisfaction}")
print(f"常见话题：{profile.common_topics}")
print(f"学习示例：{len(profile.conversation_examples)}条")
```

### 3. 测试个性化回复

```bash
# 测试VIP客户回复风格
python import_wechat_history.py test --user-type vip

# 测试普通客户
python import_wechat_history.py test --user-type regular

# 测试新客户
python import_wechat_history.py test --user-type newbie
```

---

## 📈 预期效果

### 实施前 vs 实施后

| 指标 | 实施前 | 实施后（预估） | 提升 |
|------|--------|---------------|------|
| 平均满意度 | 3.8分 | 4.3分 | +13% |
| AI解决率 | 70% | 85% | +15% |
| VIP客户满意度 | 4.0分 | 4.8分 | +20% |
| 新客户转化率 | 60% | 75% | +25% |

### 时间轴

**第1周**：
- 系统开始收集数据
- 自动构建初步画像

**第2-4周**：
- 画像逐渐完善
- 个性化效果显现

**第2个月**：
- 每个用户都有5-10条学习示例
- 回复风格明显更贴合

**第3个月**：
- 系统达到成熟状态
- "越用越好用"的效果明显

---

## 🎁 独特竞争力

### 与其他客服系统对比

| 功能 | 普通客服 | Dify等平台 | 您的系统 |
|------|---------|-----------|----------|
| 统一回复 | ✅ | ✅ | ✅ |
| 知识库检索 | ✅ | ✅ | ✅ |
| **对话风格学习** | ❌ | ❌ | ✅ **独有** |
| **用户画像** | ❌ | ❌ | ✅ **独有** |
| **个性化回复** | ❌ | ❌ | ✅ **独有** |
| **持续自我进化** | ❌ | ❌ | ✅ **独有** |

**这是您的核心竞争力！** 🎯

---

## 💰 成本分析

**一次性成本**（导入历史）：
```
使用GPT-4分析风格（可选）：¥10
使用规则分析（免费）：¥0
```

**日常成本**：
```
个性化Prompt：¥0（包含在对话token中）
Few-Shot示例：¥0（轻微增加token）
持续学习：¥0（自动化）
```

**总额外成本：几乎为零！**

---

## 🎊 立即开始

### 最简单的方式

```bash
# 1. 升级数据库
sqlite3 data\data.db < sql\upgrade_adaptive_learning.sql

# 2. 运行系统（自动启用）
python main.py

# 3. 完成！系统自动学习
```

**无需历史记录，从现在开始学习即可！**

### 如果有历史记录

```bash
# 导入历史
python import_wechat_history.py import --file wechat_backup.db

# 测试效果
python import_wechat_history.py test --user-type vip
```

---

## 📚 更多信息

详细技术方案：`docs/ADAPTIVE_LEARNING.md`

---

**立即升级，享受"越用越好"的AI客服！** 🚀

