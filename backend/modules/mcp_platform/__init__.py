"""
MCP 中台模块
支持多种 MCP 服务的统一接入和管理
"""

from .mcp_manager import MCPManager
from .aiocr_client import AIOCRClient
from .sequential_thinking_client import SequentialThinkingClient
from .mcp_client import MCPClient

__all__ = [
    'MCPManager',
    'AIOCRClient',
    'SequentialThinkingClient',
    'MCPClient'
]

__version__ = '1.0.0'
