# Cursor MCP 服务配置指南

## 概述

本指南将帮助您在 Cursor 编辑器中配置阿里云百炼的 MCP 服务，包括 AIOCR 和 Sequential Thinking 服务。

## 前提条件

1. 已安装 Cursor 编辑器
2. 拥有有效的阿里云百炼 API Key
3. 已设置环境变量 `QWEN_API_KEY`

## 配置步骤

### 1. 设置环境变量

在您的系统中设置环境变量：

```bash
# macOS/Linux
export QWEN_API_KEY=your-qwen-api-key-here

# Windows
set QWEN_API_KEY=your-qwen-api-key-here
```

### 2. 配置 Cursor MCP 服务

#### 方法 1: 使用配置文件

1. 复制项目中的 `cursor_mcp_config.json` 文件
2. 在 Cursor 设置中添加以下配置：

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
3. 添加服务器配置：

**AIOCR 服务：**
- 名称: `aiocr`
- 类型: `SSE`
- URL: `https://dashscope.aliyuncs.com/api/v1/mcps/ai-ocr/sse`
- 认证头: `Authorization: Bearer your-qwen-api-key-here`

**Sequential Thinking 服务：**
- 名称: `sequential-thinking`
- 类型: `SSE`
- URL: `https://dashscope.aliyuncs.com/api/v1/mcps/sequential-thinking/sse`
- 认证头: `Authorization: Bearer your-qwen-api-key-here`

### 3. 验证配置

#### 测试 AIOCR 服务

在 Cursor 中尝试以下操作：

1. 上传一个文档或图片
2. 使用 AIOCR 服务进行内容识别
3. 检查是否能够正确提取文本内容

#### 测试 Sequential Thinking 服务

在 Cursor 中尝试以下操作：

1. 提出一个复杂问题
2. 使用 Sequential Thinking 进行结构化分析
3. 检查是否能够生成逻辑清晰的思考步骤

## 可用服务功能

### AIOCR 服务

- **文档识别**: 支持 40+ 种文件格式
- **图片 OCR**: 提取图片中的文字内容
- **Markdown 转换**: 保留格式的文档转换

### Sequential Thinking 服务

- **结构化思考**: 将复杂问题分解为逻辑步骤
- **问题分解**: 将大问题拆分为子问题
- **决策分析**: 系统化分析多个选项
- **创意头脑风暴**: 生成创新想法和解决方案

## 使用示例

### 在 Cursor 中使用 AIOCR

```
用户: 请帮我分析这个文档的内容
助手: 我将使用 AIOCR 服务来识别文档内容...
[MCP 调用 AIOCR 服务]
结果: 文档识别完成，主要内容包括...
```

### 在 Cursor 中使用 Sequential Thinking

```
用户: 如何设计一个用户友好的登录界面？
助手: 我将使用 Sequential Thinking 来结构化分析这个问题...
[MCP 调用 Sequential Thinking 服务]
结果: 
1. 用户体验分析
2. 安全性考虑
3. 技术实现方案
4. 测试和优化策略
```

## 故障排除

### 常见问题

1. **服务连接失败**
   - 检查 API Key 是否正确设置
   - 确认网络连接正常
   - 验证 URL 地址是否正确

2. **认证失败**
   - 确认 API Key 有效
   - 检查 Bearer token 格式是否正确
   - 验证权限设置

3. **服务无响应**
   - 检查服务端点是否可用
   - 确认 SSE 协议支持
   - 查看 Cursor 日志中的错误信息

### 调试方法

1. **查看 Cursor 日志**
   - 打开开发者工具
   - 查看控制台中的 MCP 相关错误

2. **测试服务连接**
   - 使用项目中的测试脚本验证服务可用性
   - 检查网络连接和防火墙设置

3. **验证配置**
   - 确认配置文件格式正确
   - 检查环境变量设置

## 最佳实践

1. **安全性**
   - 不要在代码中硬编码 API Key
   - 使用环境变量管理敏感信息
   - 定期轮换 API Key

2. **性能优化**
   - 合理设置超时时间
   - 避免频繁调用服务
   - 使用缓存减少重复请求

3. **错误处理**
   - 实现优雅的降级机制
   - 记录详细的错误日志
   - 提供用户友好的错误提示

## 更新和维护

1. **定期更新**
   - 关注阿里云百炼的更新通知
   - 及时更新 API 版本
   - 测试新功能兼容性

2. **监控和告警**
   - 设置服务可用性监控
   - 配置错误率告警
   - 跟踪使用量和成本

## 支持资源

- [阿里云百炼官方文档](https://help.aliyun.com/zh/dashscope/)
- [Cursor 官方文档](https://cursor.sh/docs)
- [MCP 协议规范](https://modelcontextprotocol.io/)

## 联系支持

如果您在配置过程中遇到问题，可以：

1. 查看项目文档和示例
2. 提交 GitHub Issue
3. 联系技术支持团队
