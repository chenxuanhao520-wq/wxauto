#!/usr/bin/env python3
"""
测试 MCP 服务
"""

import asyncio
import json
import websockets
import requests


async def test_websocket_mcp():
    """测试 WebSocket MCP 连接"""
    print("🔌 测试 1: WebSocket MCP 连接")
    print("-" * 50)
    
    uri = "ws://localhost:8888/api/v1/mcp/ws/mcp/test-client-001"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ WebSocket 连接成功: {uri}")
            
            # 1. 初始化连接
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize"
            }
            await websocket.send(json.dumps(init_msg))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"\n📨 初始化响应:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 2. 获取工具列表
            tools_msg = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            await websocket.send(json.dumps(tools_msg))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"\n🛠️  可用工具:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 3. 调用工具 - 向量搜索
            call_msg = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "search_vectors",
                    "arguments": {
                        "query": "充电桩故障排查",
                        "top_k": 5
                    }
                }
            }
            await websocket.send(json.dumps(call_msg))
            response = await websocket.recv()
            data = json.loads(response)
            print(f"\n🔍 向量搜索结果:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            print("\n✅ WebSocket MCP 测试通过！")
            
    except Exception as e:
        print(f"\n❌ WebSocket 连接失败: {e}")


def test_http_mcp_info():
    """测试 HTTP MCP 信息端点"""
    print("\n" + "=" * 50)
    print("🌐 测试 2: HTTP MCP 信息端点")
    print("-" * 50)
    
    url = "http://localhost:8888/api/v1/mcp/mcp/info"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ HTTP 请求成功")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"❌ HTTP 请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ HTTP 请求异常: {e}")


async def test_mcp_manager():
    """测试 MCP Manager (AIOCR & Sequential Thinking)"""
    print("\n" + "=" * 50)
    print("🧠 测试 3: MCP Manager 服务")
    print("-" * 50)
    
    try:
        from modules.mcp_platform import MCPManager
        
        # 初始化 MCP Manager
        manager = MCPManager(config_path="config/mcp_config.yaml")
        await manager.initialize()
        
        print(f"✅ MCP Manager 初始化成功")
        print(f"📋 已加载服务: {list(manager.clients.keys())}")
        
        # 测试 AIOCR 服务
        if 'aiocr' in manager.clients:
            print("\n📄 测试 AIOCR 服务...")
            aiocr_client = manager.clients['aiocr']
            health = await aiocr_client.health_check()
            print(f"   状态: {health}")
        
        # 测试 Sequential Thinking 服务
        if 'sequential_thinking' in manager.clients:
            print("\n🤔 测试 Sequential Thinking 服务...")
            st_client = manager.clients['sequential_thinking']
            health = await st_client.health_check()
            print(f"   状态: {health}")
        
        print("\n✅ MCP Manager 测试完成！")
        
    except Exception as e:
        print(f"\n❌ MCP Manager 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试函数"""
    print("=" * 50)
    print("🚀 开始测试 MCP 服务")
    print("=" * 50)
    
    # 测试 1: HTTP 端点
    test_http_mcp_info()
    
    # 测试 2: WebSocket 连接
    await test_websocket_mcp()
    
    # 测试 3: MCP Manager
    await test_mcp_manager()
    
    print("\n" + "=" * 50)
    print("🎉 所有测试完成！")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
