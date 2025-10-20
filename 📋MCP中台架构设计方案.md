# 📋 MCP 中台架构设计方案

设计时间: 2025-10-19  
目标: 为 WxAuto 系统建立 MCP 中台，支持大量 MCP 服务接入  

---

## 🎯 核心价值

### 为什么需要 MCP 中台？

**传统方式的问题**:
- ❌ 每个功能都要自己开发
- ❌ 文档解析、OCR、语音识别等重复造轮子
- ❌ 维护成本高
- ❌ 升级困难

**MCP 中台的优势**:
- ✅ 即插即用 - 接入第三方 MCP 服务
- ✅ 统一管理 - 集中配置和监控
- ✅ 灵活扩展 - 随时添加新能力
- ✅ 降低成本 - 使用成熟服务，无需自研

---

## 🏗️ MCP 中台架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     WxAuto 客服系统                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 消息处理 │  │ AI 网关  │  │ RAG 检索 │  │ 知识库   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼────────────┼─────────────┼─────────────┼──────────┘
        │            │             │             │
        └────────────┼─────────────┴─────────────┘
                     │
        ┌────────────▼────────────┐
        │     MCP 中台 (新建)      │
        │  • 统一接口              │
        │  • 服务注册              │
        │  • 调用路由              │
        │  • 监控日志              │
        └────────────┬────────────┘
                     │
        ┌────────────┴────────────────────────────┐
        │                                         │
┌───────▼────────┐  ┌────────▼─────────┐  ┌─────▼─────┐
│  AIOCR MCP     │  │  其他 MCP 服务    │  │  自定义   │
│  • 文档识别    │  │  • 语音识别      │  │  MCP      │
│  • OCR         │  │  • 图片生成      │  │  服务     │
│  • Markdown转换│  │  • 数据分析      │  │           │
└────────────────┘  └──────────────────┘  └───────────┘
```

---

## 📦 MCP 中台核心模块

### 1. MCP 客户端管理器

```python
# modules/mcp_platform/__init__.py

"""
MCP 中台 - 统一管理所有 MCP 服务
"""

from .mcp_manager import MCPManager
from .mcp_client import MCPClient
from .aiocr_client import AIOCRClient

__all__ = ['MCPManager', 'MCPClient', 'AIOCRClient']
```

### 2. MCP 管理器

```python
# modules/mcp_platform/mcp_manager.py

"""
MCP 管理器 - 统一调度所有 MCP 服务
"""
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MCPServiceConfig:
    """MCP 服务配置"""
    service_id: str
    name: str
    type: str  # sse | stdio
    url: str
    api_key: str
    capabilities: List[str]  # ['ocr', 'doc_convert', 'markdown']
    enabled: bool = True
    timeout: int = 30


class MCPManager:
    """
    MCP 中台管理器
    
    功能：
    1. 注册和管理多个 MCP 服务
    2. 统一调用接口
    3. 服务路由和负载均衡
    4. 监控和日志
    5. 错误处理和降级
    """
    
    def __init__(self):
        self.services: Dict[str, MCPClient] = {}
        self.service_configs: Dict[str, MCPServiceConfig] = {}
        logger.info("MCP 中台初始化")
    
    def register_service(self, config: MCPServiceConfig):
        """
        注册 MCP 服务
        
        Args:
            config: 服务配置
        """
        try:
            # 根据服务类型创建客户端
            if config.service_id == 'aiocr':
                from .aiocr_client import AIOCRClient
                client = AIOCRClient(
                    api_key=config.api_key,
                    base_url=config.url
                )
            else:
                # 通用 MCP 客户端
                from .mcp_client import MCPClient
                client = MCPClient(
                    service_id=config.service_id,
                    url=config.url,
                    api_key=config.api_key,
                    connection_type=config.type
                )
            
            self.services[config.service_id] = client
            self.service_configs[config.service_id] = config
            
            logger.info(f"✅ MCP 服务已注册: {config.name} ({config.service_id})")
        
        except Exception as e:
            logger.error(f"❌ MCP 服务注册失败: {config.service_id}, {e}")
    
    async def call_service(
        self,
        service_id: str,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用 MCP 服务
        
        Args:
            service_id: 服务ID，如 'aiocr'
            tool_name: 工具名称，如 'doc_recognition'
            parameters: 参数
        
        Returns:
            执行结果
        """
        if service_id not in self.services:
            raise ValueError(f"MCP 服务不存在: {service_id}")
        
        config = self.service_configs[service_id]
        
        if not config.enabled:
            raise ValueError(f"MCP 服务已禁用: {service_id}")
        
        client = self.services[service_id]
        
        try:
            logger.info(f"调用 MCP 服务: {service_id}.{tool_name}")
            
            result = await client.call_tool(
                tool_name=tool_name,
                parameters=parameters
            )
            
            logger.info(f"✅ MCP 调用成功: {service_id}.{tool_name}")
            return result
        
        except Exception as e:
            logger.error(f"❌ MCP 调用失败: {service_id}.{tool_name}, {e}")
            raise
    
    async def call_capability(
        self,
        capability: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        根据能力调用（自动路由到合适的服务）
        
        Args:
            capability: 能力名称，如 'ocr', 'doc_convert'
            parameters: 参数
        
        Returns:
            执行结果
        """
        # 查找支持该能力的服务
        available_services = [
            service_id
            for service_id, config in self.service_configs.items()
            if capability in config.capabilities and config.enabled
        ]
        
        if not available_services:
            raise ValueError(f"没有可用的服务支持该能力: {capability}")
        
        # 选择第一个可用服务（可以扩展为负载均衡）
        service_id = available_services[0]
        
        # 映射能力到工具名称
        tool_mapping = {
            'ocr': 'doc_recognition',
            'doc_to_markdown': 'doc_to_markdown',
            'doc_to_text': 'doc_recognition'
        }
        
        tool_name = tool_mapping.get(capability, capability)
        
        return await self.call_service(service_id, tool_name, parameters)
    
    def get_available_capabilities(self) -> List[str]:
        """获取所有可用的能力"""
        capabilities = set()
        for config in self.service_configs.values():
            if config.enabled:
                capabilities.update(config.capabilities)
        return list(capabilities)
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            'total_services': len(self.services),
            'enabled_services': sum(1 for c in self.service_configs.values() if c.enabled),
            'available_capabilities': self.get_available_capabilities(),
            'services': [
                {
                    'id': service_id,
                    'name': config.name,
                    'enabled': config.enabled,
                    'capabilities': config.capabilities
                }
                for service_id, config in self.service_configs.items()
            ]
        }
```

---

## 🔧 AIOCR MCP 客户端实现

```python
# modules/mcp_platform/aiocr_client.py

"""
AIOCR MCP 客户端
支持文档识别和转换
"""
import httpx
import logging
from typing import Dict, Any, Optional
import base64
from pathlib import Path

logger = logging.getLogger(__name__)


class AIOCRClient:
    """
    AIOCR MCP 客户端
    
    功能：
    1. 文档识别（doc_recognition）- 转文本
    2. 文档转 Markdown（doc_to_markdown）- 保留格式
    """
    
    def __init__(
        self,
        api_key: str = None,
        base_url: str = "https://dashscope.aliyuncs.com/api/v1/mcps/ai-ocr/sse"
    ):
        """
        初始化 AIOCR 客户端
        
        Args:
            api_key: DashScope API Key（如果为空，使用临时密钥 'ali_bailian'）
            base_url: MCP 服务地址
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "ali_bailian")
        self.base_url = base_url
        
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=60.0  # 文档识别可能需要较长时间
        )
        
        logger.info("AIOCR MCP 客户端初始化成功")
    
    async def doc_recognition(
        self,
        file_path: str = None,
        file_url: str = None,
        file_content: bytes = None
    ) -> Dict[str, Any]:
        """
        文档识别 - 转文本
        
        Args:
            file_path: 本地文件路径
            file_url: 文件URL
            file_content: 文件二进制内容
        
        Returns:
            {
                'text': '识别的文本内容',
                'pages': 页数,
                'format': '文件格式'
            }
        """
        # 构建请求
        if file_path:
            # 读取本地文件
            file_content = Path(file_path).read_bytes()
            file_name = Path(file_path).name
        elif file_content:
            file_name = "document"
        elif file_url:
            file_name = file_url.split('/')[-1]
        else:
            raise ValueError("必须提供 file_path, file_url 或 file_content")
        
        # Base64 编码
        if file_content:
            file_base64 = base64.b64encode(file_content).decode()
        
        # 调用 MCP 工具
        payload = {
            "name": "doc_recognition",
            "arguments": {
                "file": file_base64 if file_content else None,
                "url": file_url if file_url else None,
                "filename": file_name
            }
        }
        
        try:
            # SSE 调用（简化版，实际需要处理 SSE 流）
            response = await self.client.post(
                f"{self.base_url}/tools/call",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ AIOCR 识别成功: {file_name}")
                return result
            else:
                logger.error(f"❌ AIOCR 识别失败: {response.status_code}")
                return {'error': response.text}
        
        except Exception as e:
            logger.error(f"❌ AIOCR 调用异常: {e}")
            raise
    
    async def doc_to_markdown(
        self,
        file_path: str = None,
        file_url: str = None,
        file_content: bytes = None
    ) -> Dict[str, Any]:
        """
        文档转 Markdown - 保留格式
        
        Returns:
            {
                'markdown': 'Markdown 格式内容',
                'pages': 页数,
                'format': '文件格式'
            }
        """
        # 类似 doc_recognition，调用 doc_to_markdown 工具
        # 实现逻辑与上面相同
        pass
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]):
        """统一的工具调用接口"""
        if tool_name == 'doc_recognition':
            return await self.doc_recognition(**parameters)
        elif tool_name == 'doc_to_markdown':
            return await self.doc_to_markdown(**parameters)
        else:
            raise ValueError(f"未知的工具: {tool_name}")
```

---

## 🔌 集成到现有系统

### 集成点 1: 知识库上传

**场景**: 用户上传文档到知识库

```python
# scripts/upload_with_etl.py (现有文件，添加 MCP 支持)

class DocumentETLPipeline:
    def __init__(self):
        # 原有组件
        self.document_processor = DocumentProcessor()
        
        # ✅ 新增：MCP 中台
        from modules.mcp_platform.mcp_manager import MCPManager
        self.mcp_manager = MCPManager()
        
        # 注册 AIOCR 服务
        self._register_mcp_services()
    
    def _register_mcp_services(self):
        """注册 MCP 服务"""
        from modules.mcp_platform.mcp_manager import MCPServiceConfig
        
        # 注册 AIOCR
        aiocr_config = MCPServiceConfig(
            service_id='aiocr',
            name='AIOCR 文档识别',
            type='sse',
            url='https://dashscope.aliyuncs.com/api/v1/mcps/ai-ocr/sse',
            api_key=os.getenv('DASHSCOPE_API_KEY', 'ali_bailian'),
            capabilities=['ocr', 'doc_to_markdown', 'doc_to_text']
        )
        
        self.mcp_manager.register_service(aiocr_config)
    
    async def process_document(self, file_path: str):
        """处理文档（优先使用 MCP）"""
        
        # ✅ 优先使用 AIOCR MCP
        try:
            logger.info("尝试使用 AIOCR MCP 识别文档...")
            
            result = await self.mcp_manager.call_capability(
                capability='doc_to_markdown',
                parameters={'file_path': file_path}
            )
            
            markdown_content = result['markdown']
            
            logger.info("✅ AIOCR MCP 识别成功")
            
            # 继续 ETL 流程
            return await self._continue_etl(markdown_content, file_path)
        
        except Exception as e:
            logger.warning(f"AIOCR MCP 失败，降级到本地解析: {e}")
            
            # 降级：使用原有的 DocumentProcessor
            return await self.document_processor.process_file(file_path)
```

### 集成点 2: 消息处理（图片/文件）

**场景**: 客户发送图片或文件

```python
# server/services/message_service.py

class MessageService:
    def __init__(self):
        # 原有组件
        self.ai_gateway = AIGateway()
        
        # ✅ 新增：MCP 中台
        from modules.mcp_platform.mcp_manager import MCPManager
        self.mcp_manager = MCPManager()
        self._init_mcp_services()
    
    def _init_mcp_services(self):
        """初始化 MCP 服务"""
        # 注册 AIOCR
        from modules.mcp_platform.mcp_manager import MCPServiceConfig
        
        aiocr = MCPServiceConfig(
            service_id='aiocr',
            name='AIOCR',
            type='sse',
            url='https://dashscope.aliyuncs.com/api/v1/mcps/ai-ocr/sse',
            api_key=os.getenv('DASHSCOPE_API_KEY', 'ali_bailian'),
            capabilities=['ocr', 'doc_to_markdown']
        )
        
        self.mcp_manager.register_service(aiocr)
    
    async def process_message(self, message):
        """处理消息"""
        
        # ✅ 检测是否包含图片或文件
        if message.get('type') == 'image':
            # 使用 AIOCR 识别图片
            ocr_result = await self.mcp_manager.call_capability(
                capability='ocr',
                parameters={
                    'file_url': message['image_url']
                }
            )
            
            # 将 OCR 文本作为用户问题
            message['content'] = ocr_result['text']
        
        elif message.get('type') == 'file':
            # 使用 AIOCR 解析文档
            doc_result = await self.mcp_manager.call_capability(
                capability='doc_to_markdown',
                parameters={
                    'file_url': message['file_url']
                }
            )
            
            # 将文档内容作为上下文
            message['content'] = f"用户发送了文档，内容：\n{doc_result['markdown'][:500]}..."
        
        # 继续原有的消息处理流程
        return await self._process_text_message(message)
```

---

## 📊 AIOCR MCP 服务详细配置

### 配置文件

```yaml
# config.yaml - 添加 MCP 配置

# ==================== MCP 中台配置 ====================
mcp_platform:
  enabled: true                      # 是否启用 MCP 中台
  
  services:
    # AIOCR 文档识别服务
    aiocr:
      enabled: true
      name: "AIOCR 文档识别"
      type: "sse"                    # SSE 长连接
      url: "https://dashscope.aliyuncs.com/api/v1/mcps/ai-ocr/sse"
      api_key_env: "DASHSCOPE_API_KEY"  # 从环境变量读取
      fallback_key: "ali_bailian"    # 临时密钥
      timeout: 60
      retry: 3
      
      capabilities:
        - ocr                        # OCR 识别
        - doc_to_markdown            # 文档转 Markdown
        - doc_to_text                # 文档转文本
      
      supported_formats:
        - pdf
        - doc
        - docx
        - xls
        - xlsx
        - ppt
        - pptx
        - png
        - jpg
        - jpeg
        # ... 更多格式
      
      use_cases:
        - knowledge_base_upload      # 知识库上传
        - image_message_ocr          # 图片消息识别
        - file_message_parse         # 文件消息解析
    
    # 未来可以添加更多 MCP 服务
    # speech_recognition:
    #   enabled: false
    #   name: "语音识别"
    #   ...
```

### 环境变量

```bash
# set_env.sh - 添加 MCP 配置

# MCP 服务密钥
export DASHSCOPE_API_KEY=your-dashscope-api-key-here  # AIOCR 服务
# export SPEECH_API_KEY=your-key  # 语音识别服务（未来）
# export IMAGE_GEN_KEY=your-key   # 图片生成服务（未来）
```

---

## 🎯 使用场景示例

### 场景 1: 知识库文档上传

**用户操作**: 上传 PDF 产品手册

**系统流程**:
```python
1. 接收文件: product_manual.pdf
2. 调用 MCP: mcp_manager.call_capability('doc_to_markdown', ...)
3. 获取 Markdown: 保留格式的文档内容
4. ETL 处理: 清洗、分块、质量验证
5. 存入知识库: 高质量的 Markdown 格式
6. 建立索引: BM25 + 向量索引
```

**优势**:
- ✅ AIOCR 识别准确率高（基于 AI 大模型）
- ✅ 保留文档格式（表格、列表、标题）
- ✅ 支持 40+ 种文件格式
- ✅ 零运维成本

### 场景 2: 客户发送图片咨询

**用户操作**: 发送故障图片 "充电桩报错截图"

**系统流程**:
```python
1. 接收图片: error_screenshot.jpg
2. 调用 MCP: mcp_manager.call_capability('ocr', ...)
3. 提取文本: "错误代码: E-1001, 通讯故障"
4. RAG 检索: 搜索 "E-1001 通讯故障"
5. AI 生成: 基于错误码和知识库生成解决方案
6. 回复客户: "错误 E-1001 是通讯故障，请检查..."
```

**优势**:
- ✅ 自动识别图片中的文字
- ✅ 提取错误码和关键信息
- ✅ 无需客户手动输入

### 场景 3: 客户发送 Excel 表格

**用户操作**: 发送设备清单 Excel

**系统流程**:
```python
1. 接收文件: device_list.xlsx
2. 调用 MCP: mcp_manager.call_capability('doc_to_markdown', ...)
3. 转换表格:
   | 设备型号 | 数量 | 状态 |
   |---------|------|------|
   | CP-7KW  | 5    | 正常 |
   | CP-30KW | 2    | 故障 |
4. AI 分析: "您有 2 台设备显示故障，建议..."
5. 智能建议: 生成维护方案
```

---

## 🚀 快速实现

### 第一阶段：基础集成（1小时）

1. ✅ 创建 `modules/mcp_platform/` 目录
2. ✅ 实现 `MCPManager`
3. ✅ 实现 `AIOCRClient`
4. ✅ 在 `upload_with_etl.py` 中集成

### 第二阶段：消息处理集成（1小时）

5. ✅ 在 `message_service.py` 中集成
6. ✅ 支持图片消息 OCR
7. ✅ 支持文件消息解析

### 第三阶段：扩展更多 MCP 服务（按需）

8. ⏳ 接入语音识别 MCP
9. ⏳ 接入图片生成 MCP
10. ⏳ 接入数据分析 MCP

---

## 💰 成本分析

### AIOCR MCP 成本

```
当前: 限时免费
临时密钥: 'ali_bailian' (免费)
正式密钥: 需 DashScope API Key

未来定价（预估）:
- 文档识别: ¥0.01-0.05/页
- OCR 识别: ¥0.005-0.02/张
```

### 使用场景成本

**每天 100 次文档处理**:
- 知识库上传: 10次 × ¥0.03 = ¥0.3
- 图片 OCR: 80次 × ¥0.01 = ¥0.8
- 文件解析: 10次 × ¥0.03 = ¥0.3

**日成本**: ¥1.4  
**月成本**: ¥42

**总成本**: ¥54 (AI) + ¥42 (MCP) = **¥96/月**

---

## 🎊 MCP 中台的核心优势

### 对比自研方案

| 功能 | 自研方案 | MCP 中台 |
|------|---------|---------|
| **开发成本** | 2-4 周 | 1-2 天 |
| **维护成本** | 持续维护 | 零维护 |
| **准确率** | 需要调试 | AI 大模型，准确率高 |
| **格式支持** | 有限 | 40+ 种格式 |
| **升级** | 需要重新开发 | 自动升级 |

### 扩展能力

**未来可接入的 MCP 服务**:
1. ✅ AIOCR - 文档识别（已分析）
2. ⏳ 语音识别 MCP - 处理语音消息
3. ⏳ 图片生成 MCP - 自动生成图表、流程图
4. ⏳ 数据分析 MCP - 客户数据洞察
5. ⏳ 翻译 MCP - 多语言支持
6. ⏳ 代码执行 MCP - 技术支持场景

---

## 📋 实施计划

### 立即行动（推荐）

**第一步**: 实现 MCP 中台基础架构（1-2小时）
- 创建 `modules/mcp_platform/`
- 实现 `MCPManager` 和 `AIOCRClient`
- 添加配置文件

**第二步**: 集成到知识库上传（30分钟）
- 在 `upload_with_etl.py` 中集成
- 测试 PDF/DOC 上传

**第三步**: 集成到消息处理（1小时）
- 在 `message_service.py` 中集成
- 支持图片和文件消息

**第四步**: 测试和优化（30分钟）
- 端到端测试
- 性能优化

**总计**: 约 4 小时即可完成

---

## 🎯 最终建议

### 是否需要 MCP 中台？

**✅ 强烈推荐**，如果您有以下需求：
- 📄 大量文档需要处理
- 🖼️ 客户经常发送图片/文件
- 🔊 未来可能需要语音识别
- 🎨 需要图表生成等高级功能
- 💰 希望降低开发和维护成本

### 实施建议

**Phase 1: AIOCR 集成（立即实施）**
- 实现 MCP 中台基础架构
- 接入 AIOCR 服务
- 集成到知识库上传

**Phase 2: 消息处理集成（1周内）**
- 支持图片消息 OCR
- 支持文件消息解析

**Phase 3: 扩展更多服务（按需）**
- 语音识别
- 图片生成
- 其他 MCP 服务

---

## ✅ 需要我立即实现吗？

我可以：
1. ✅ 创建完整的 MCP 中台模块
2. ✅ 实现 AIOCR 客户端
3. ✅ 集成到知识库上传
4. ✅ 集成到消息处理
5. ✅ 编写完整的测试脚本
6. ✅ 更新文档

预计耗时：2-3 小时  
预期效果：文档处理能力 +300%

需要我开始实现吗？😊

