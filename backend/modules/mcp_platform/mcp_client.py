"""
MCP 通用客户端
处理 MCP 协议通信
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
import httpx

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP 通用客户端"""
    
    def __init__(self, service, cache_manager=None):
        self.service = service
        self.endpoint = service.endpoint
        self.api_key = service.api_key
        self.timeout = service.timeout
        self.max_retries = service.max_retries
        self.cache_manager = cache_manager  # 缓存管理器
    
    async def _make_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        发送 MCP 请求
        
        Args:
            method: 方法名
            params: 参数
            
        Returns:
            响应结果
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        # 只有当 API Key 存在且非空时才添加 Authorization 头
        if self.api_key and self.api_key.strip():
            headers["Authorization"] = f"Bearer {self.api_key.strip()}"
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method
        }
        
        if params:
            payload["params"] = params
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # 使用 stream 方法处理 SSE 响应
                    async with client.stream(
                        'POST',
                        self.endpoint,
                        headers=headers,
                        json=payload
                    ) as response:
                        
                        if response.status_code != 200:
                            error_text = await response.aread()
                            raise Exception(f"HTTP {response.status_code}: {error_text.decode('utf-8')}")
                        
                        # 处理 SSE 流
                        result_data = None
                        buffer = ""
                        
                        async for chunk in response.aiter_text():
                            buffer += chunk
                            
                            # 按行分割处理
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                line = line.strip()
                                
                                if not line:
                                    continue
                                
                                # 处理 SSE 数据行
                                if line.startswith('data:'):
                                    data_json = line[5:].strip()
                                    
                                    if data_json and data_json != '[DONE]':
                                        try:
                                            data = json.loads(data_json)
                                            result_data = data
                                            
                                            # 如果是错误响应
                                            if "error" in data:
                                                raise Exception(f"MCP 错误: {data['error']}")
                                            
                                            # 如果是结果响应，直接返回
                                            if "result" in data:
                                                return data["result"]
                                                
                                        except json.JSONDecodeError:
                                            logger.debug(f"跳过非 JSON 数据: {data_json[:50]}...")
                                            continue
                        
                        # 如果流结束但有数据，返回最后的数据
                        if result_data:
                            return result_data
                        else:
                            raise Exception("未收到有效响应")
            
            except Exception as e:
                logger.warning(f"MCP 请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))  # 递增延迟
                else:
                    raise e
    
    async def _list_tools(self) -> List[Dict[str, Any]]:
        """获取工具列表"""
        try:
            result = await self._make_request("tools/list")
            return result.get("tools", [])
        except Exception as e:
            logger.error(f"获取工具列表失败: {e}")
            return []
    
    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用工具
        
        Args:
            tool_name: 工具名
            arguments: 参数
            
        Returns:
            工具执行结果
        """
        try:
            result = await self._make_request(
                "tools/call",
                {
                    "name": tool_name,
                    "arguments": arguments
                }
            )
            return result
        except Exception as e:
            logger.error(f"调用工具失败 {tool_name}: {e}")
            raise e
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            tools = await self._list_tools()
            return {
                "status": "healthy",
                "tools_count": len(tools),
                "message": "MCP 服务正常"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "MCP 服务异常"
            }
