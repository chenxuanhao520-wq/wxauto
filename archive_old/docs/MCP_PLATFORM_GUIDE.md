# MCP 中台使用指南

## 概述

MCP (Model Context Protocol) 中台是系统的统一服务接入层，支持多种 MCP 服务的集成和管理。目前主要集成了阿里云百炼的 AIOCR 服务，提供强大的文档识别能力。

## 核心功能

### 1. MCP 中台管理器
- 统一管理所有 MCP 服务
- 服务注册与发现
- 健康检查与监控
- 统计信息收集

### 2. AIOCR 客户端
- 文档识别 (doc_recognition)
- 文档转 Markdown (doc_to_markdown)
- 批量处理
- 支持 40+ 种文件格式

### 3. 系统集成
- 知识库文档处理
- 消息服务媒体处理
- 智能降级机制

## 快速开始

### 1. 环境配置

```bash
# 设置 Qwen API Key
export QWEN_API_KEY=your-qwen-api-key-here
export QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
export QWEN_MODEL=qwen-turbo
```

### 2. 基础使用

```python
from modules.mcp_platform import MCPManager

# 初始化 MCP 中台
manager = MCPManager()

# 获取 AIOCR 客户端
aiocr_client = manager.get_client("aiocr")

# 文档识别
result = await aiocr_client.doc_recognition("document.pdf")
if result["success"]:
    print(f"识别内容: {result['content']}")
```

### 3. 集成到文档处理器

```python
from modules.kb_service.document_processor import DocumentProcessor

# 启用 MCP AIOCR
processor = DocumentProcessor(use_mcp_aiocr=True)

# 处理文档（优先使用 MCP AIOCR）
result = processor.process_file(
    file_path="document.pdf",
    use_mcp_aiocr=True
)

print(f"处理方法: {result['processing_method']}")
```

### 4. 集成到消息服务

消息服务已自动集成 MCP AIOCR，支持：
- 图片消息 OCR 识别
- 文件消息内容提取
- 智能降级到本地处理

## 支持的文件格式

### MCP AIOCR 支持格式
```
PDF, DOC, DOCX, TXT, CSV, XLS, XLSX, PPT, PPTX, MD
JPEG, PNG, BMP, GIF, SVG, WEBP, ICO, TIFF
HTML, JSON, MOBI, LOG
GO, H, C, CPP, CS, JAVA, JS, CSS, PHP, PY, ASP
YAML, YML, INI, TS, TSX
```

### 本地解析器支持格式
```
PDF, DOC, DOCX, JPG, JPEG, PNG, BMP
```

## API 参考

### MCPManager

```python
class MCPManager:
    def get_service(self, name: str) -> Optional[MCPService]
    def get_client(self, name: str)
    def list_services(self) -> List[Dict[str, Any]]
    def health_check(self) -> Dict[str, Any]
    def get_stats(self) -> Dict[str, Any]
```

### AIOCRClient

```python
class AIOCRClient:
    async def doc_recognition(self, file_path: str, filename: str = None) -> Dict[str, Any]
    async def doc_to_markdown(self, file_path: str, filename: str = None) -> Dict[str, Any]
    async def batch_process(self, file_paths: List[str], output_format: str = "text") -> List[Dict[str, Any]]
    async def health_check(self) -> Dict[str, Any]
    def get_supported_formats(self) -> List[str]
    def is_format_supported(self, file_ext: str) -> bool
```

### DocumentProcessor 增强

```python
class DocumentProcessor:
    def __init__(self, use_ocr: bool = True, use_mcp_aiocr: bool = True)
    def process_file(self, file_path: str, use_mcp_aiocr: Optional[bool] = None) -> Dict[str, Any]
    async def batch_process_files(self, file_paths: List[str], use_mcp_aiocr: Optional[bool] = None) -> List[Dict[str, Any]]
    def get_supported_formats(self) -> Dict[str, List[str]]
    def is_mcp_aiocr_available(self) -> bool
    async def health_check(self) -> Dict[str, Any]
```

## 测试

### 运行完整测试
```bash
python3 test_mcp_platform.py
```

### 测试内容
1. MCP 中台管理器
2. AIOCR 客户端功能
3. 文档处理器集成
4. 消息服务集成
5. 批量处理

### 预期输出
```
🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬
MCP 中台完整测试
🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬🔬

使用 API Key: sk-1d7d593d85b146968...
...

🎉 所有测试通过！MCP 中台集成成功！
```

## 配置选项

### 环境变量
```bash
# 必需
QWEN_API_KEY=your-qwen-api-key-here

# 可选
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-turbo
```

### 服务配置
```python
# 启用/禁用 MCP AIOCR
processor = DocumentProcessor(use_mcp_aiocr=True)

# 单次处理指定方法
result = processor.process_file(
    file_path="document.pdf",
    use_mcp_aiocr=True  # 强制使用 MCP AIOCR
)
```

## 故障排除

### 常见问题

1. **MCP AIOCR 初始化失败**
   - 检查 `QWEN_API_KEY` 是否正确设置
   - 确认网络连接正常
   - 查看日志中的具体错误信息

2. **文档识别失败**
   - 检查文件格式是否支持
   - 确认文件路径正确
   - 查看文件大小是否超限

3. **降级到本地处理**
   - 这是正常现象，系统会自动降级
   - 本地处理能力依然很强
   - 不影响系统正常运行

### 日志级别
```python
import logging
logging.getLogger('modules.mcp_platform').setLevel(logging.DEBUG)
```

## 性能优化

### 批量处理
```python
# 批量处理多个文件
results = await aiocr_client.batch_process(
    file_paths=["doc1.pdf", "doc2.docx", "doc3.txt"],
    output_format="text"
)
```

### 缓存策略
- 文档处理器支持结果缓存
- 消息服务支持回复缓存
- 建议生产环境使用 Redis

## 扩展开发

### 添加新的 MCP 服务

1. 在 `MCPManager._init_services()` 中注册服务
2. 创建对应的客户端类
3. 实现健康检查和统计方法

### 自定义客户端
```python
class CustomMCPClient(MCPClient):
    async def custom_method(self, params):
        return await self._call_tool("custom_tool", params)
```

## 最佳实践

1. **错误处理**: 始终检查返回结果的 `success` 字段
2. **降级机制**: 利用系统的自动降级功能
3. **批量处理**: 对于大量文件，使用批量处理接口
4. **健康检查**: 定期检查服务健康状态
5. **日志记录**: 启用详细日志以便调试

## 更新日志

### v1.0.0 (2024-10-19)
- 初始版本发布
- 支持 AIOCR 服务集成
- 完整的文档处理器集成
- 消息服务媒体处理
- 批量处理功能
- 健康检查和监控
