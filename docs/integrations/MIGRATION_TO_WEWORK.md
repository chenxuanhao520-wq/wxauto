# 迁移到企业微信指南

本文档介绍如何从个人微信（wxauto）迁移到企业微信（官方API）。

---

## 🎯 为什么要迁移？

### 企业微信的优势

| 优势 | 说明 |
|------|------|
| ✅ **零封号风险** | 官方API，完全合规 |
| ✅ **更稳定** | 不依赖PC微信 |
| ✅ **更灵活** | 可部署在Linux服务器 |
| ✅ **功能更强** | 支持图文、卡片、审批等 |
| ✅ **易于运维** | 可自动化部署和监控 |
| ✅ **数据安全** | 企业级安全保障 |

### 代价

- ❌ 需要企业认证（免费，但需营业执照）
- ❌ 客户需要加入企业微信
- ❌ 迁移需要一定时间

---

## 📋 迁移步骤

### 步骤1：申请企业微信（1-3天）

1. **注册企业微信**
   - 访问：https://work.weixin.qq.com/
   - 注册企业
   - 提交企业认证（需营业执照）

2. **等待审核**
   - 通常1-3个工作日
   - 免费

---

### 步骤2：创建应用（10分钟）

1. **登录管理后台**
   - https://work.weixin.qq.com/wework_admin/

2. **创建自建应用**
   - 应用管理 → 自建 → 创建应用
   - 设置应用名称、Logo
   - 记录 **Agent ID**

3. **获取密钥**
   - 在应用详情页
   - 记录 **Corp ID**
   - 查看并记录 **Corp Secret**

4. **配置接收消息**
   - 设置API接收 → 设置URL和Token
   - 用于接收用户消息

---

### 步骤3：配置环境变量（1分钟）

```bash
# 企业微信配置
export WEWORK_CORP_ID=ww1234567890abcdef
export WEWORK_CORP_SECRET=1234567890abcdef1234567890abcdef
export WEWORK_AGENT_ID=1000001

# ⚠️ 不再需要这个：
# export USE_FAKE_ADAPTER=false  （删除）
```

---

### 步骤4：修改代码（1行）

**main.py 中修改：**

```python
# ========== 原来 ==========
if use_fake:
    self.wx_adapter = FakeWxAdapter(whitelisted_groups)
    logger.info("使用 FakeWxAdapter（测试模式）")
else:
    # Phase 1 真实环境替换
    from adapters.wxauto_adapter import WxAutoAdapter
    self.wx_adapter = WxAutoAdapter(whitelisted_groups)
    logger.info("使用 WxAutoAdapter（真实模式）")

# ========== 改为 ==========
if use_fake:
    self.wx_adapter = FakeWxAdapter(whitelisted_groups)
    logger.info("使用 FakeWxAdapter（测试模式）")
else:
    # 企业微信
    from adapters.wework_adapter import WeWorkAdapter
    self.wx_adapter = WeWorkAdapter()
    logger.info("使用 WeWorkAdapter（企业微信）")

# 仅此一行修改！其他代码完全不用动！
```

---

### 步骤5：移除wxauto依赖（可选）

```bash
# 卸载wxauto（不再需要）
pip uninstall wxauto

# 安装企业微信SDK（可选，也可以直接用requests）
pip install wechatpy

# 更新 requirements.txt
# 删除：wxauto>=3.9.0
# 添加：wechatpy>=1.8.0
```

---

### 步骤6：测试运行

```bash
# 运行系统
python main.py

# 应该看到：
# [INFO] 使用 WeWorkAdapter（企业微信）
# [INFO] 企业微信适配器初始化成功
```

---

### 步骤7：邀请客户（渐进式）

**方式1：逐个邀请**
```
1. 创建企业微信群
2. 邀请客户加入
3. 在群中@机器人测试
4. 确认无问题后继续邀请其他客户
```

**方式2：并行运行**
```
1. 保留个人微信版本（wxauto）
2. 启动企业微信版本（API）
3. 两个系统同时运行
4. 逐步迁移客户
5. 最终关闭个人微信版本
```

---

## 🔄 并行运行方案

在迁移期间，可以两套系统同时运行：

```bash
# 服务器1：个人微信（Windows）
export USE_FAKE_ADAPTER=false
export OPENAI_API_KEY=sk-xxxxx
python main.py  # 监听个人微信群

# 服务器2：企业微信（Linux）
export WEWORK_CORP_ID=ww1234...
export WEWORK_CORP_SECRET=1234...
export WEWORK_AGENT_ID=1000001
export OPENAI_API_KEY=sk-xxxxx
python main.py  # 监听企业微信群
```

**优势**：
- 平滑过渡
- 降低风险
- 客户自主选择

---

## 📊 功能对比

### 个人微信（wxauto）

**支持的功能**：
- ✅ 文本消息
- ✅ @识别
- ✅ 群聊
- ⚠️ 图片（理论支持，但复杂）
- ❌ 卡片、小程序

**限制**：
- 受PC微信功能限制
- 需要前台运行
- 有封号风险

---

### 企业微信（API）

**支持的功能**：
- ✅ 文本消息
- ✅ 图文消息
- ✅ Markdown
- ✅ 卡片消息
- ✅ 文件发送
- ✅ 应用消息
- ✅ 审批流程
- ✅ 日程安排

**限制**：
- API调用有频率限制（但足够用）
- 需要企业认证

---

## 💰 成本对比

| 项目 | 个人微信 | 企业微信 |
|------|---------|---------|
| 微信费用 | 免费 | 免费 |
| 认证费用 | 无需认证 | 免费（需营业执照） |
| 服务器 | Windows专机 | Linux服务器（更便宜） |
| 运维成本 | 需人工值守 | 可自动化 |
| AI费用 | 相同 | 相同 |

**总成本差异**：几乎没有差异

---

## 🐛 常见问题

### Q1: 迁移会丢失数据吗？

**A**: 不会

- 数据库保持不变
- 历史对话完整保留
- 只是换了消息发送方式

### Q2: 客户不愿意加企业微信怎么办？

**A**: 并行方案

- 保留个人微信版本（部分客户）
- 使用企业微信版本（愿意的客户）
- 两套系统同时运行

### Q3: 企业微信认证需要什么？

**A**: 营业执照

- 需要企业营业执照
- 个体工商户也可以
- 认证免费

### Q4: API有调用限制吗？

**A**: 有，但够用

- 消息发送：约10000次/天
- 对于客服场景完全足够
- 可申请提额

### Q5: 迁移需要多久？

**A**: 总计约1-2周

- 企业认证：1-3天
- 创建应用：10分钟
- 修改代码：5分钟
- 测试验证：1-2天
- 客户迁移：渐进式，1-2周

---

## 🎯 推荐的迁移路线图

### 第1周：准备

- [ ] 申请企业微信认证
- [ ] 创建企业微信应用
- [ ] 获取 Corp ID、Secret、Agent ID
- [ ] 修改并测试代码

### 第2周：小范围试点

- [ ] 邀请1-2个友好客户加入企业微信
- [ ] 在企业微信群测试所有功能
- [ ] 收集反馈，优化配置

### 第3-4周：逐步扩展

- [ ] 邀请更多客户加入
- [ ] 两套系统并行运行
- [ ] 监控稳定性

### 第5-8周：完成迁移

- [ ] 大部分客户迁移到企业微信
- [ ] 个人微信版本只保留少数客户
- [ ] 准备关闭个人微信版本

### 第2个月：稳定运营

- [ ] 完全使用企业微信
- [ ] 移除wxauto依赖
- [ ] 部署到Linux服务器（可选）

---

## 🚀 立即开始

### 如果想试试企业微信

```bash
# 1. 先在测试环境试试
# 访问：https://work.weixin.qq.com/
# 注册 → 创建应用 → 获取密钥

# 2. 配置
export WEWORK_CORP_ID=your_corp_id
export WEWORK_CORP_SECRET=your_secret
export WEWORK_AGENT_ID=1000001

# 3. 修改 main.py（一行代码）
# 4. 运行
python main.py

# 5. 测试发送消息
```

### 如果暂时继续用个人微信

```bash
# 启用所有防护措施
# 已自动启用拟人化
# 严格监控消息量
# 准备好迁移到企业微信的B计划
```

---

## 📚 相关文档

- `docs/WECHAT_SAFETY.md` - 个人微信防封号指南
- `adapters/wework_adapter.py` - 企业微信适配器代码
- `adapters/wxauto_adapter.py` - 个人微信适配器代码

---

**结论：企业微信不需要wxauto，是更好的长期方案！**

**最后更新**：2025-10-16

