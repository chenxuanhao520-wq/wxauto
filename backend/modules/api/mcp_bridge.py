"""
MCP 浏览器桥接端点
允许 Chrome 扩展通过 WebSocket 与 MCP 通信
"""

import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()


class MCPBridge:
    """MCP 浏览器桥接器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """连接客户端"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"✅ MCP 客户端已连接: {client_id}")
    
    def disconnect(self, client_id: str):
        """断开客户端"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"❌ MCP 客户端已断开: {client_id}")
    
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        """发送消息给客户端"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
    
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息给所有客户端"""
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"广播失败 {client_id}: {e}")


# 全局桥接器实例
mcp_bridge = MCPBridge()


@router.websocket("/ws/mcp/{client_id}")
async def mcp_websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    MCP WebSocket 端点
    Chrome 扩展通过此端点连接
    """
    await mcp_bridge.connect(websocket, client_id)
    
    try:
        while True:
            # 接收来自浏览器的消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            logger.info(f"收到 MCP 消息 from {client_id}: {message.get('method')}")
            
            # 处理不同的 MCP 方法
            response = await handle_mcp_request(message)
            
            # 发送响应
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        mcp_bridge.disconnect(client_id)
    except Exception as e:
        logger.error(f"MCP WebSocket 错误: {e}")
        mcp_bridge.disconnect(client_id)


async def handle_mcp_request(message: Dict[str, Any]) -> Dict[str, Any]:
    """处理 MCP 请求"""
    method = message.get("method")
    params = message.get("params", {})
    msg_id = message.get("id", 1)
    
    try:
        if method == "initialize":
            # 初始化连接
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "0.1.0",
                    "serverInfo": {
                        "name": "wxauto-smart-service",
                        "version": "2.0.0"
                    },
                    "capabilities": {
                        "tools": True,
                        "resources": True,
                        "prompts": True
                    }
                }
            }
        
        elif method == "tools/list":
            # 返回可用工具列表
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "search_vectors",
                            "description": "搜索向量数据库（pgvector）",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string"},
                                    "top_k": {"type": "number", "default": 10}
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "query_database",
                            "description": "查询 Supabase 数据库",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "table": {"type": "string"},
                                    "filters": {"type": "object"}
                                },
                                "required": ["table"]
                            }
                        },
                        {
                            "name": "call_ai",
                            "description": "调用 AI 模型（智谱AI/Qwen等）",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "prompt": {"type": "string"},
                                    "model": {"type": "string"}
                                },
                                "required": ["prompt"]
                            }
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            # 调用工具
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # 这里调用实际的工具函数
            result = await execute_tool(tool_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False)
                        }
                    ]
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"未知方法: {method}"
                }
            }
    
    except Exception as e:
        logger.error(f"处理 MCP 请求失败: {e}")
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """执行工具"""
    # TODO: 集成实际的工具实现
    if tool_name == "search_vectors":
        return {
            "results": [],
            "message": "向量搜索功能待集成"
        }
    elif tool_name == "query_database":
        return {
            "data": [],
            "message": "数据库查询功能待集成"
        }
    elif tool_name == "call_ai":
        return {
            "response": "AI 调用功能待集成",
            "model": arguments.get("model", "unknown")
        }
    else:
        raise ValueError(f"未知工具: {tool_name}")


@router.get("/mcp/info")
async def mcp_info():
    """MCP 服务信息"""
    return JSONResponse({
        "service": "wxauto-smart-service MCP Bridge",
        "version": "2.0.0",
        "protocol": "0.1.0",
        "websocket_endpoint": "ws://localhost:8888/api/v1/mcp/ws/mcp/{client_id}",
        "active_connections": len(mcp_bridge.active_connections),
        "capabilities": ["tools", "resources", "prompts"]
    })
