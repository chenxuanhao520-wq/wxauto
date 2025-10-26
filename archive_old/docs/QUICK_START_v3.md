# 🚀 v3.0 快速开始指南

欢迎使用微信客服中台 v3.0！本版本新增了多模型支持和多维表格集成。

---

## ✨ 新功能一览

### 1. 多模型支持（7个大模型）

现在支持：OpenAI、DeepSeek、Claude、通义千问、文心一言、Gemini、Moonshot

**特点**：
- 💰 **成本优化**：可选择性价比最高的模型
- 🔄 **自动降级**：主模型失败时自动切换备用
- 🎯 **按需选择**：不同场景使用不同模型
- ⚙️ **零代码配置**：只需设置环境变量

### 2. 多维表格集成

支持飞书和钉钉多维表格自动同步

**特点**：
- 📊 **数据可视化**：自动生成图表和仪表板
- 🔄 **自动同步**：定时批量同步消息日志
- 📈 **实时分析**：监控 AI 性能和成本
- 🎨 **灵活配置**：支持自定义字段映射

---

## 🎯 5分钟快速开始

### 步骤 1：选择一个大模型

```bash
# 方案A：OpenAI（推荐，质量最好）
export OPENAI_API_KEY=sk-your-openai-key

# 方案B：DeepSeek（性价比最高）
export DEEPSEEK_API_KEY=sk-your-deepseek-key

# 方案C：通义千问（国内稳定）
export QWEN_API_KEY=sk-your-qwen-key

# 可以配置多个，系统会按照 config.yaml 选择
```

### 步骤 2：运行系统

```bash
# 运行主程序
python main.py

# 或使用快速启动
python quickstart.py
```

### 步骤 3：测试对话

在微信群中 @ 机器人：

```
@小助手 如何安装设备？
```

机器人会使用你配置的 AI 模型回答问题！

---

## 🎨 可选：配置多维表格

### 飞书多维表格

```bash
# 1. 配置环境变量
export FEISHU_APP_ID=cli_xxxxx
export FEISHU_APP_SECRET=xxxxx
export FEISHU_BITABLE_TOKEN=bascnxxxxx
export FEISHU_TABLE_ID=tblxxxxx

# 2. 测试连接
python sync_to_bitable.py test --platform feishu

# 3. 同步数据
python sync_to_bitable.py sync --platform feishu --days 7
```

### 钉钉多维表格

```bash
# 1. 配置环境变量
export DINGTALK_APP_KEY=dingtalkxxxxx
export DINGTALK_APP_SECRET=xxxxx
export DINGTALK_BASE_ID=xxxxx
export DINGTALK_TABLE_ID=xxxxx

# 2. 测试连接
python sync_to_bitable.py test --platform dingtalk

# 3. 同步数据
python sync_to_bitable.py sync --platform dingtalk --days 7
```

---

## 📚 常用命令

### AI 模型测试

```bash
# 测试不同模型（修改 config.yaml 的 primary 配置）
python main.py

# 查看 AI 网关状态
python ops_tools.py health
```

### 多维表格操作

```bash
# 测试所有平台连接
python sync_to_bitable.py test --platform both

# 同步到所有平台
python sync_to_bitable.py sync --platform both --days 7

# 只同步飞书
python sync_to_bitable.py sync --platform feishu --days 30
```

### 知识库管理

```bash
# 添加示例文档
python kb_manager.py --action add

# 查看所有文档
python kb_manager.py --action list

# 测试检索
python kb_manager.py --action search --query "如何安装"
```

### 运维工具

```bash
# 健康检查
python ops_tools.py health

# 性能报告
python ops_tools.py report --days 7

# 日志轮转
python ops_tools.py rotate

# 清理旧数据
python ops_tools.py cleanup --days 90
```

---

## 🎯 推荐配置

### 配置 1：质量优先

```bash
# 主用 OpenAI，备用 Claude
export OPENAI_API_KEY=sk-xxxxx
export CLAUDE_API_KEY=sk-ant-xxxxx
```

```yaml
# config.yaml
llm:
  primary: openai:gpt-4o-mini
  fallback: claude:claude-3-5-sonnet
```

**适用场景**：对回答质量要求高，成本不敏感

### 配置 2：成本优先

```bash
# 主用 DeepSeek，备用 Gemini
export DEEPSEEK_API_KEY=sk-xxxxx
export GEMINI_API_KEY=xxxxx
```

```yaml
# config.yaml
llm:
  primary: deepseek:chat
  fallback: gemini:gemini-1.5-flash
```

**适用场景**：消息量大，需要控制成本

### 配置 3：国内优先

```bash
# 主用通义千问，备用文心一言
export QWEN_API_KEY=sk-xxxxx
export ERNIE_API_KEY=client_id:client_secret
```

```yaml
# config.yaml
llm:
  primary: qwen:qwen-max
  fallback: ernie:ernie-4.0
```

**适用场景**：需要国内稳定服务，避免网络问题

---

## 📊 功能对比

| 功能 | v1.0 | v2.0 | v3.0 |
|------|------|------|------|
| 大模型数量 | 0（模板） | 2 | **7** ✨ |
| 主备降级 | ❌ | ✅ | ✅ |
| 配置方式 | - | 需修改代码 | **环境变量** ✨ |
| 数据导出 | CSV | CSV | CSV + **多维表格** ✨ |
| 数据可视化 | ❌ | ❌ | **飞书/钉钉图表** ✨ |
| 知识库 | 模拟 | BM25 | BM25 |
| 运维工具 | ❌ | ✅ | ✅ |

---

## 🔍 详细文档

- **[大模型配置指南](docs/LLM_PROVIDERS.md)** - 7个模型的详细配置
- **[多维表格集成指南](docs/MULTITABLE_INTEGRATION.md)** - 飞书/钉钉完整教程
- **[v3.0 发布说明](docs/v3.0_RELEASE_NOTES.md)** - 完整更新日志
- **[README.md](README.md)** - 完整使用手册

---

## ❓ 常见问题

### Q1: 必须配置 API Key 吗？

**A**: 不是必须的。

- 未配置时，系统会回退到模板响应
- 但建议至少配置一个（推荐 DeepSeek，便宜）

### Q2: 可以同时配置多个模型吗？

**A**: 可以！

系统支持主备降级：
- 主模型失败时自动切换备用
- 提高系统可用性

### Q3: 多维表格必须配置吗？

**A**: 不是必须的，完全可选。

- 不配置也能正常使用
- 配置后可以享受数据可视化

### Q4: 哪个模型最便宜？

**A**: DeepSeek

- 成本：¥0.1/百万tokens
- 是 OpenAI 的 1/50
- 中文效果也很好

### Q5: 哪个模型质量最好？

**A**: 视场景而定

- **综合质量**: OpenAI GPT-4o
- **中文对话**: 通义千问、Moonshot
- **长文本**: Claude
- **速度**: Gemini

---

## 💡 最佳实践

### 1. 成本控制

```yaml
llm:
  max_tokens: 400        # 限制输出长度
  temperature: 0.3       # 降低随机性
```

### 2. 定时同步

在系统定时任务中添加：

```bash
# 每天凌晨同步到多维表格
0 2 * * * python sync_to_bitable.py sync --platform both --days 1
```

### 3. 监控成本

定期查看多维表格中的数据：
- 每个模型的 Token 消耗
- 平均单次对话成本
- 成本趋势

### 4. A/B 测试

尝试不同模型，对比：
- 回答质量（通过置信度）
- 响应速度（latency_ms）
- 用户满意度（status = 'answered'）

---

## 🎉 开始使用

```bash
# 1. 配置最简单的方案（DeepSeek）
export DEEPSEEK_API_KEY=sk-your-key

# 2. 初始化知识库
python kb_manager.py --action add

# 3. 运行系统
python main.py

# 4. 在微信群测试
@小助手 你好
```

就这么简单！享受全新的 AI 客服体验吧！ 🚀

---

**更新时间**：2025-10-16  
**版本**：v3.0.0

