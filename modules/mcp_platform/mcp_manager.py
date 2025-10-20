"""
MCP 中台管理器
统一管理所有 MCP 服务
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MCPService:
    """MCP 服务配置"""
    name: str
    endpoint: str
    api_key: str
    enabled: bool = True
    timeout: int = 30
    max_retries: int = 3
    metadata: Dict[str, Any] = None


class MCPManager:
    """MCP 中台管理器"""
    
    def __init__(self):
        self.services: Dict[str, MCPService] = {}
        self.clients: Dict[str, Any] = {}
        self._init_services()
    
    def _init_services(self):
        """初始化 MCP 服务"""
        # AIOCR 服务
        aiocr_service = MCPService(
            name="aiocr",
            endpoint="https://dashscope.aliyuncs.com/api/v1/mcps/ai-ocr/sse",
            api_key=os.getenv("QWEN_API_KEY", ""),
            enabled=bool(os.getenv("QWEN_API_KEY")),
            timeout=60,
            max_retries=3,
            metadata={
                "provider": "阿里云百炼",
                "description": "AI 文档识别服务",
                "supported_formats": [
                    "pdf", "doc", "docx", "txt", "csv", "xls", "xlsx", 
                    "ppt", "pptx", "md", "jpeg", "png", "bmp", "gif", 
                    "svg", "webp", "ico", "tiff", "html", "json", "mobi",
                    "log", "go", "h", "c", "cpp", "cs", "java", "js", 
                    "css", "php", "py", "asp", "yaml", "yml", "ini", "ts", "tsx"
                ],
                "tools": ["doc_recognition", "doc_to_markdown"]
            }
        )
        
        self.services["aiocr"] = aiocr_service
        
        # Sequential Thinking 服务
        sequential_thinking_service = MCPService(
            name="sequential_thinking",
            endpoint="https://dashscope.aliyuncs.com/api/v1/mcps/sequential-thinking/sse",
            api_key=os.getenv("QWEN_API_KEY", ""),
            enabled=bool(os.getenv("QWEN_API_KEY")),
            timeout=60,
            max_retries=3,
            metadata={
                "provider": "阿里云百炼",
                "description": "Sequential Thinking 结构化思考服务",
                "tools": [
                    "sequential_thinking",
                    "problem_decomposition", 
                    "decision_analysis",
                    "creative_brainstorming"
                ],
                "capabilities": [
                    "结构化问题分析",
                    "问题分解",
                    "决策分析", 
                    "创意头脑风暴",
                    "逻辑推理",
                    "风险评估"
                ]
            }
        )
        
        self.services["sequential_thinking"] = sequential_thinking_service
        
        logger.info(f"✅ MCP 中台初始化完成，注册 {len(self.services)} 个服务")
    
    def get_service(self, name: str) -> Optional[MCPService]:
        """获取 MCP 服务配置"""
        return self.services.get(name)
    
    def get_client(self, name: str):
        """获取 MCP 客户端"""
        if name not in self.clients:
            service = self.get_service(name)
            if not service:
                raise ValueError(f"MCP 服务不存在: {name}")
            
            if not service.enabled:
                raise ValueError(f"MCP 服务已禁用: {name}")
            
            # 根据服务类型创建客户端
            if name == "aiocr":
                from .aiocr_client import AIOCRClient
                self.clients[name] = AIOCRClient(service)
            elif name == "sequential_thinking":
                from .sequential_thinking_client import SequentialThinkingClient
                self.clients[name] = SequentialThinkingClient(service)
            else:
                from .mcp_client import MCPClient
                self.clients[name] = MCPClient(service)
        
        return self.clients[name]
    
    def list_services(self) -> List[Dict[str, Any]]:
        """列出所有服务"""
        return [
            {
                "name": name,
                "enabled": service.enabled,
                "endpoint": service.endpoint,
                "description": service.metadata.get("description", ""),
                "supported_formats": service.metadata.get("supported_formats", []),
                "tools": service.metadata.get("tools", [])
            }
            for name, service in self.services.items()
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        results = {}
        
        for name, service in self.services.items():
            if not service.enabled:
                results[name] = {"status": "disabled", "message": "服务已禁用"}
                continue
            
            try:
                # 简单的健康检查：验证服务配置和API密钥
                if service.api_key:
                    results[name] = {
                        "status": "healthy", 
                        "message": "服务配置正常",
                        "endpoint": service.endpoint,
                        "api_key_configured": True
                    }
                else:
                    results[name] = {
                        "status": "error", 
                        "message": "API密钥未配置"
                    }
            except Exception as e:
                results[name] = {"status": "error", "message": str(e)}
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_services = len(self.services)
        enabled_services = sum(1 for s in self.services.values() if s.enabled)
        
        return {
            "total_services": total_services,
            "enabled_services": enabled_services,
            "disabled_services": total_services - enabled_services,
            "services": self.list_services()
        }
