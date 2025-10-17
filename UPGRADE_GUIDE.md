# 系统升级指南 v1.0 → v2.0

## 🎉 升级概览

本次升级将系统从 **Phase 0-1（基础框架）** 升级到 **Phase 2-4（完整AI能力）**，是一次重大功能升级。

**核心变化**：
- ✅ 从模板回复 → **真实AI对话**（OpenAI/DeepSeek）
- ✅ 从模拟检索 → **BM25知识库检索**
- ✅ 新增知识库管理工具
- ✅ 新增运维工具（健康检查、性能报告）

---

## 📋 升级前检查

### 1. 系统要求

| 项目 | v1.0 要求 | v2.0 要求 |
|------|----------|----------|
| Python | 3.10+ | 3.10+ |
| 操作系统 | Windows（真实微信） | Windows（真实微信） |
| 依赖包 | pyyaml, requests, pytest | + openai |

### 2. 必需配置

**v2.0 新增必需项**：
```bash
# OpenAI API Key（必需，用于真实AI对话）
OPENAI_API_KEY=sk-xxxxxxxxxxxxx

# 可选：DeepSeek 备用
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
```

### 3. 数据备份

升级前请备份数据库：

```bash
# 备份数据库
cp data/data.db data/data.db.backup_v1

# 备份日志
cp -r logs logs_backup_v1
```

---

## 🚀 升级步骤

### 步骤 1：更新依赖

```bash
# 安装新依赖
pip install openai>=1.0.0

# 或重新安装所有依赖
pip install -r requirements.txt
```

### 步骤 2：配置环境变量

```bash
# 设置 OpenAI API Key
export OPENAI_API_KEY=sk-your-key-here

# Windows
set OPENAI_API_KEY=sk-your-key-here
```

### 步骤 3：初始化知识库

```bash
# 添加示例文档到知识库
python kb_manager.py --action add

# 验证知识库
python kb_manager.py --action list
```

### 步骤 4：测试运行

```bash
# 测试模式（无需微信）
python main.py

# 观察日志，确认 AI 网关初始化成功
```

### 步骤 5：健康检查

```bash
# 运行健康检查
python ops_tools.py health

# 应该看到：
# ✅ 数据库正常
# ✅ AI 网关可用
# ✅ 知识库已加载
```

---

## 🆕 新功能使用指南

### 1. AI 对话功能

**自动启用**：设置 `OPENAI_API_KEY` 后自动启用

**工作流程**：
1. 用户提问
2. RAG 检索相关知识
3. AI 根据知识生成回答
4. 发送给用户

**示例对话**：
```
用户: @小助手 设备过热怎么办？

AI: 根据《故障排查手册 v1.5》：
① 立即断电
② 检查通风口是否堵塞
③ 等待冷却后再启动

长期过热可能损坏设备。如需进一步协助，请提供设备型号和使用环境。
```

### 2. 知识库管理

**添加文档**：
```bash
python kb_manager.py --action add
```

**查看文档**：
```bash
python kb_manager.py --action list
```

**测试检索**：
```bash
python kb_manager.py --action search --query "设备故障"
```

**自定义文档**（编程方式）：
```python
from rag.retriever import Retriever

retriever = Retriever()

# 添加自定义文档
chunks = [
    {
        'section': '第1章',
        'content': '你的知识内容...',
        'keywords': ['关键词1', '关键词2']
    }
]

retriever.add_document(
    document_name='自定义文档',
    document_version='v1.0',
    chunks=chunks
)

# 保存到数据库
retriever.save_to_db('data/data.db')
```

### 3. 运维工具

**每日健康检查**：
```bash
python ops_tools.py health
```

**生成性能报告**：
```bash
# 最近7天
python ops_tools.py report --days 7

# 最近30天
python ops_tools.py report --days 30
```

**日志轮转**：
```bash
# 超过50MB自动归档
python ops_tools.py rotate --max-log-size 50
```

**清理旧数据**：
```bash
# 清理90天前的数据
python ops_tools.py cleanup --days 90
```

---

## 🔄 配置迁移

### config.yaml 无需修改

`config.yaml` 文件无需修改，所有新功能配置已包含：

```yaml
# v2.0 新增配置（已存在于原 config.yaml）
llm:
  primary: openai:gpt-4o-mini  # AI 主提供商
  fallback: deepseek:chat       # AI 备用提供商
  max_tokens: 512
  temperature: 0.3

rag:
  bm25_topn: 50      # BM25 召回数量
  top_k: 4           # 最终返回证据数
  min_confidence: 0.75
```

### 新增环境变量

v2.0 新增以下可选环境变量：

```bash
# AI 提供商配置
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT=30

DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=30

# 数据库路径（可选）
DATABASE_PATH=data/data.db

# 日志配置（可选）
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

---

## 📊 功能对比

| 功能 | v1.0 | v2.0 |
|------|------|------|
| 消息监听 | ✅ | ✅ |
| @识别 | ✅ | ✅ |
| 去重/频控 | ✅ | ✅ |
| ACK确认 | ✅ | ✅ |
| 会话管理 | ✅ | ✅ |
| 响应生成 | ❌ 模板 | ✅ **AI生成** |
| 知识检索 | ❌ 模拟 | ✅ **BM25检索** |
| 知识库管理 | ❌ | ✅ **kb_manager.py** |
| 健康检查 | ❌ | ✅ **ops_tools.py** |
| 性能报告 | ❌ | ✅ **ops_tools.py** |
| 日志轮转 | ❌ | ✅ **ops_tools.py** |
| CSV导出 | ✅ | ✅ |

---

## 🐛 常见问题

### Q1: 升级后报错 "openai 未安装"

**解决**：
```bash
pip install openai>=1.0.0
```

### Q2: AI 网关初始化失败

**原因**：未设置 `OPENAI_API_KEY`

**解决**：
```bash
export OPENAI_API_KEY=sk-your-key-here
```

**影响**：不影响运行，会回退到模板响应

### Q3: 知识库为空

**解决**：
```bash
# 添加示例文档
python kb_manager.py --action add

# 或运行快速启动
python quickstart.py
```

### Q4: 所有测试是否兼容？

**答案**：是的

原有 36 个测试全部通过，新增 8 个 AI 网关测试。

```bash
# 运行所有测试
pytest tests/ -v

# 跳过需要 API Key 的测试
pytest tests/ -v -k "not real"
```

### Q5: 如何回退到 v1.0？

**临时回退**（不删除代码）：
```bash
# 使用模板响应（不调用AI）
unset OPENAI_API_KEY
python main.py
```

**完全回退**：
```bash
# 恢复备份
cp data/data.db.backup_v1 data/data.db

# 使用 git 恢复代码
git checkout v1.0
```

---

## ✅ 升级验证

升级完成后，执行以下检查：

### 1. 健康检查

```bash
python ops_tools.py health
```

**预期输出**：
```
✅ 数据库正常
✅ AI 网关可用
✅ 知识库已加载: X 个知识块
✅ 日志文件存在
```

### 2. 知识库检查

```bash
python kb_manager.py --action search --query "安装设备"
```

**预期输出**：
```
置信度: 0.85
找到 3 条证据:
1. 【产品安装指南 v2.1 - 第2章 安装步骤】...
```

### 3. 运行测试

```bash
pytest tests/ -v
```

**预期输出**：
```
====== 44 passed in X.XXs ======
```

### 4. 功能测试

```bash
# 运行演示
python demo.py

# 或运行快速启动
python quickstart.py
```

---

## 📞 支持

如遇到升级问题：

1. 查看 `logs/app.log` 日志
2. 运行健康检查 `python ops_tools.py health`
3. 参考 `CHANGELOG.md` 了解详细变更
4. 查阅 `README.md` 完整文档

---

**升级完成！享受全新的 AI 客服能力 🎉**

