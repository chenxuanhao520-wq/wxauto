# 大模型提供商配置指南

本文档介绍如何配置和使用系统支持的各个大模型提供商。

---

## 🎯 支持的提供商

系统已集成以下大模型提供商，只需配置相应的 API Key 即可使用：

| 提供商 | 模型示例 | 特点 | 推荐场景 |
|--------|----------|------|----------|
| **OpenAI** | gpt-4o, gpt-4o-mini | 质量高、稳定 | 生产环境首选 |
| **DeepSeek** | deepseek-chat | 性价比高、国内快 | 成本敏感场景 |
| **Anthropic Claude** | claude-3-5-sonnet | 长文本、推理能力强 | 复杂任务 |
| **阿里通义千问** | qwen-max, qwen-plus | 国内服务、稳定 | 国内部署 |
| **百度文心一言** | ernie-4.0 | 国内服务、中文优化 | 中文为主场景 |
| **Google Gemini** | gemini-1.5-flash | 速度快、多模态 | 需要快速响应 |
| **Moonshot (Kimi)** | moonshot-v1-8k | 长上下文、中文好 | 需要长上下文 |

---

## 🚀 快速配置

### 方式一：环境变量（推荐）

在 `.env` 文件或系统环境变量中配置：

```bash
# 选择一个主要提供商
export OPENAI_API_KEY=sk-your-openai-key
export OPENAI_MODEL=gpt-4o-mini

# 可选：配置备用提供商
export DEEPSEEK_API_KEY=sk-your-deepseek-key
```

### 方式二：修改 config.yaml

```yaml
llm:
  primary: openai:gpt-4o-mini  # 主提供商:模型
  fallback: deepseek:chat       # 备用提供商:模型
  max_tokens: 512
  temperature: 0.3
```

---

## 📋 详细配置说明

### 1. OpenAI

**获取 API Key**：
1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册/登录账号
3. 进入 API Keys 页面
4. 创建新的 API Key

**配置**：
```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=30
```

**可用模型**：
- `gpt-4o` - 最新旗舰模型
- `gpt-4o-mini` - 性价比模型（推荐）
- `gpt-4-turbo` - GPT-4 Turbo
- `gpt-3.5-turbo` - GPT-3.5

**定价参考**（2025年）：
- gpt-4o-mini: $0.15/1M tokens (输入) + $0.60/1M tokens (输出)
- gpt-4o: $2.50/1M tokens (输入) + $10/1M tokens (输出)

---

### 2. DeepSeek

**获取 API Key**：
1. 访问 [DeepSeek Platform](https://platform.deepseek.com/)
2. 注册账号
3. 获取 API Key

**配置**：
```bash
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=30
```

**可用模型**：
- `deepseek-chat` - 对话模型
- `deepseek-coder` - 代码专用模型

**定价参考**：
- deepseek-chat: ¥0.1/百万tokens（非常便宜）

**优势**：
- 💰 价格极低
- 🚀 国内访问快
- 🎯 中文效果好

---

### 3. Anthropic Claude

**获取 API Key**：
1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 创建账号
3. 获取 API Key

**配置**：
```bash
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_TIMEOUT=60
```

**可用模型**：
- `claude-3-5-sonnet-20241022` - 最新 Sonnet（推荐）
- `claude-3-opus-20240229` - 最强模型
- `claude-3-haiku-20240307` - 最快模型

**特点**：
- 📚 支持 200K token 上下文
- 🧠 推理能力强
- 📝 长文本处理优秀

---

### 4. 阿里通义千问

**获取 API Key**：
1. 访问 [阿里云百炼](https://bailian.console.aliyun.com/)
2. 开通服务
3. 获取 API Key

**配置**：
```bash
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-max
QWEN_TIMEOUT=30
```

**可用模型**：
- `qwen-max` - 最强模型
- `qwen-plus` - 性能均衡
- `qwen-turbo` - 速度优先

**优势**：
- 🇨🇳 国内服务，稳定
- 💬 中文理解优秀
- 💰 价格适中

---

### 5. 百度文心一言

**获取 API Key**：
1. 访问 [百度智能云](https://console.bce.baidu.com/qianfan/)
2. 开通千帆大模型平台
3. 创建应用，获取 API Key 和 Secret Key

**配置**：
```bash
# 特殊格式：client_id:client_secret
ERNIE_API_KEY=your_client_id:your_client_secret
ERNIE_MODEL=ernie-4.0
ERNIE_TIMEOUT=30
```

**可用模型**：
- `ernie-4.0` - 文心 4.0
- `ernie-3.5` - 文心 3.5
- `ernie-speed` - 速度优化版

**特点**：
- 🇨🇳 百度官方模型
- 📱 移动端优化
- 💬 中文对话能力强

---

### 6. Google Gemini

**获取 API Key**：
1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 创建 API Key

**配置**：
```bash
GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_BASE=https://generativelanguage.googleapis.com/v1beta/openai/
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TIMEOUT=30
```

**可用模型**：
- `gemini-1.5-flash` - 快速模型（推荐）
- `gemini-1.5-pro` - 专业模型

**特点**：
- ⚡ 速度快
- 🌐 多模态支持
- 🔓 免费额度较高

---

### 7. Moonshot (Kimi)

**获取 API Key**：
1. 访问 [Moonshot Platform](https://platform.moonshot.cn/)
2. 注册账号
3. 获取 API Key

**配置**：
```bash
MOONSHOT_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MOONSHOT_API_BASE=https://api.moonshot.cn/v1
MOONSHOT_MODEL=moonshot-v1-8k
MOONSHOT_TIMEOUT=30
```

**可用模型**：
- `moonshot-v1-8k` - 8K 上下文
- `moonshot-v1-32k` - 32K 上下文
- `moonshot-v1-128k` - 128K 上下文

**特点**：
- 📚 支持长上下文
- 💬 中文能力优秀
- 🇨🇳 国内服务

---

## ⚙️ 主备切换配置

系统支持主备提供商自动切换，当主提供商失败时自动使用备用：

### 配置方法

**方式一：config.yaml**
```yaml
llm:
  primary: openai:gpt-4o-mini      # 主提供商
  fallback: deepseek:chat           # 备用提供商
  enable_fallback: true
```

**方式二：代码初始化**
```python
from ai_gateway.gateway import AIGateway

gateway = AIGateway(
    primary_provider="openai",
    fallback_provider="deepseek",
    enable_fallback=True
)
```

### 降级流程

1. 优先使用主提供商
2. 主提供商失败（超时/错误）时，自动切换到备用
3. 所有提供商失败时，返回模板回复

---

## 💰 成本优化建议

### 策略一：按场景选择模型

```yaml
# 高质量要求 -> OpenAI GPT-4o
primary: openai:gpt-4o

# 一般场景 -> OpenAI GPT-4o-mini 或 DeepSeek
primary: openai:gpt-4o-mini
fallback: deepseek:chat

# 成本优先 -> DeepSeek
primary: deepseek:chat
```

### 策略二：控制 Token 使用

```yaml
llm:
  max_tokens: 400  # 限制输出长度
  temperature: 0.3 # 降低随机性，减少重试
```

### 策略三：使用缓存

系统自动缓存相似问题的回答，减少 API 调用。

---

## 🔍 测试和验证

### 测试单个提供商

```bash
# 设置环境变量
export OPENAI_API_KEY=sk-your-key

# 运行测试
python -c "
from ai_gateway.gateway import AIGateway
gateway = AIGateway('openai', enable_fallback=False)
response = gateway.generate('你好，请简单自我介绍')
print(response.content)
"
```

### 测试主备切换

```bash
# 设置两个提供商
export OPENAI_API_KEY=sk-invalid-key  # 故意设错
export DEEPSEEK_API_KEY=sk-your-deepseek-key

# 运行测试（应该自动降级到 DeepSeek）
python main.py
```

---

## 📊 性能对比

基于实际测试（供参考）：

| 提供商 | 平均响应时间 | 中文质量 | 成本 | 稳定性 |
|--------|-------------|----------|------|--------|
| OpenAI | 2-4s | ⭐⭐⭐⭐⭐ | 💰💰💰 | ⭐⭐⭐⭐⭐ |
| DeepSeek | 1-3s | ⭐⭐⭐⭐ | 💰 | ⭐⭐⭐⭐ |
| Claude | 3-6s | ⭐⭐⭐⭐⭐ | 💰💰💰💰 | ⭐⭐⭐⭐ |
| 通义千问 | 2-4s | ⭐⭐⭐⭐⭐ | 💰💰 | ⭐⭐⭐⭐⭐ |
| 文心一言 | 2-5s | ⭐⭐⭐⭐ | 💰💰 | ⭐⭐⭐⭐ |
| Gemini | 1-2s | ⭐⭐⭐ | 💰 | ⭐⭐⭐⭐ |
| Moonshot | 2-4s | ⭐⭐⭐⭐⭐ | 💰💰 | ⭐⭐⭐⭐ |

---

## 🐛 常见问题

### Q1: API Key 无效

**检查清单**：
- [ ] API Key 格式正确
- [ ] 环境变量已设置
- [ ] API Key 未过期
- [ ] 账户余额充足

### Q2: 请求超时

**解决方法**：
1. 增加超时时间：`OPENAI_TIMEOUT=60`
2. 检查网络连接
3. 使用国内提供商

### Q3: 返回错误内容

**可能原因**：
- 模型理解偏差
- system_prompt 不够明确
- temperature 设置过高

**解决**：
1. 优化 system_prompt
2. 降低 temperature (0.1-0.3)
3. 更换质量更高的模型

---

## 📚 依赖安装

```bash
# 基础依赖（所有提供商）
pip install openai requests

# Anthropic Claude
pip install anthropic

# 其他提供商使用 OpenAI 兼容接口，无需额外安装
```

---

**最后更新**：2025-10-16

