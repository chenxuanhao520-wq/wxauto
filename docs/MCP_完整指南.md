# MCP 完整指南

## 📚 概述

本文档整合了 MCP (Model Context Protocol) 的配置、集成和使用指南。

**目录**:
- [配置指南](#配置指南) - 如何在 Cursor 中配置 MCP
- [集成总结](#集成总结) - 已集成功能概述
- [使用指南](#使用指南) - 实际使用方法

---

## ⚙️ 配置指南

### 前提条件

1. 已安装 Cursor 编辑器
2. 拥有有效的阿里云百炼 API Key
3. 已设置环境变量 `QWEN_API_KEY`

### 环境变量配置

```bash
# macOS/Linux
export QWEN_API_KEY=your-qwen-api-key-here

# Windows
set QWEN_API_KEY=your-qwen-api-key-here
```

### Cursor 配置

#### 方法 1: 使用配置文件

复制项目中的 `cursor_mcp_config.json` 并添加到 Cursor 设置:

```json
{
  "mcpServers": {
    "aiocr": {
      "type": "sse",
      "url": "https://dashscope.aliyuncs.com/api/v1/mcps/ai-ocr/sse",
      "headers": {
        "Authorization": "Bearer your-qwen-api-key-here"
      }
    },
    "sequential-thinking": {
      "type": "sse", 
      "url": "https://dashscope.aliyuncs.com/api/v1/mcps/sequential-thinking/sse",
      "headers": {
        "Authorization": "Bearer your-qwen-api-key-here"
      }
    }
  }
}
```

#### 方法 2: 通过 Cursor 设置界面

1. 打开 Cursor 设置 (Cmd/Ctrl + ,)
2. 搜索 "MCP" 或 "Model Context Protocol"
3. 添加服务器配置（见上方 JSON 配置）

---

## 🎯 集成总结

### 已集成的 MCP 服务

#### 1. AIOCR 服务

**功能**: 文档识别和转换

**工具**:
- `doc_recognition`: 文档转文本
- `doc_to_markdown`: 文档转 Markdown

**支持格式**: 40+ 种文档和图片格式

**应用场景**:
- 知识库文档上传自动处理
- 微信消息图片/文件识别
- 文档智能解析和归档

#### 2. Sequential Thinking 服务

**功能**: 结构化思考和问题分析

**工具**:
- `sequential_thinking`: 顺序思考分析
- `problem_decomposition`: 问题分解
- `decision_analysis`: 决策分析
- `creative_brainstorming`: 创意头脑风暴

**应用场景**:
- 复杂问题分析
- 决策支持
- 创意生成
- 战略规划

---

## 💡 使用指南

### 基础使用

```python
from modules.mcp_platform import MCPManager

# 初始化管理器
manager = MCPManager()

# 获取服务客户端
aiocr = manager.get_client("aiocr")
sequential_thinking = manager.get_client("sequential-thinking")

# 文档识别
result = await aiocr.call_tool("doc_recognition", {
    "url": "document.pdf"
})

# 结构化思考
analysis = await sequential_thinking.call_tool("sequential_thinking", {
    "problem": "分析充电桩故障原因"
})
```

### 系统集成

#### 集成到文档处理

```python
from modules.mcp_platform import MCPManager

manager = MCPManager()
aiocr = manager.get_client("aiocr")

# 文档识别
result = await aiocr.doc_recognition("document.pdf")
print(f"识别内容: {result['content']}")
```

---

## 🏗️ 技术架构

### 模块结构

```
modules/mcp_platform/
├── __init__.py                      # 模块初始化
├── mcp_manager.py                   # MCP 中台管理器
├── mcp_manager_v2.py                # MCP 管理器 v2
├── mcp_client.py                    # 通用 MCP 客户端
├── aiocr_client.py                  # AIOCR 客户端
└── sequential_thinking_client.py   # Sequential Thinking 客户端
```

### 核心类

#### MCPManager

```python
class MCPManager:
    """MCP 中台管理器"""
    
    def __init__(self):
        """初始化所有 MCP 服务"""
        
    def get_client(self, name: str):
        """获取指定服务的客户端"""
        
    def list_services(self) -> List[Dict]:
        """列出所有服务"""
        
    def health_check(self) -> Dict:
        """健康检查"""
```

---

## ✅ 验证配置

### 测试 AIOCR 服务

1. 在 Cursor 中上传一个文档或图片
2. 使用 AIOCR 服务进行内容识别
3. 检查是否能够正确提取文本内容

### 测试 Sequential Thinking 服务

1. 在 Cursor 中提出一个复杂问题
2. 使用 Sequential Thinking 进行结构化分析
3. 检查是否能够生成逻辑清晰的思考步骤

---

## 📖 相关文档

- [MCP 完整指南](./MCP_完整指南.md) - 本文档
- [ERP 对接指南](./erp_api/README.md)
- [快速开始指南](./guides/快速开始.md)

---

**版本**: v2.0  
**最后更新**: 2025-10-26
