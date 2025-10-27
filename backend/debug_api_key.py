#!/usr/bin/env python3
"""
调试 API Key 传递问题
"""

import asyncio
from dotenv import load_dotenv
from modules.mcp_platform.mcp_manager_v2 import MCPManagerV2

load_dotenv()

async def debug_api_key():
    print("=" * 60)
    print("🔍 调试 API Key 传递")
    print("=" * 60)
    
    # 初始化 Manager
    manager = MCPManagerV2(config_path="config/mcp_config.yaml")
    
    # 获取服务
    service = manager.get_service('sequential_thinking')
    print(f"\n📋 服务配置:")
    print(f"   名称: {service.name}")
    print(f"   端点: {service.endpoint}")
    print(f"   API Key: '{service.api_key}'")
    print(f"   API Key 长度: {len(service.api_key) if service.api_key else 0}")
    print(f"   API Key 是否为空: {not service.api_key or not service.api_key.strip()}")
    
    # 获取客户端
    client = manager.get_client('sequential_thinking')
    print(f"\n🔧 客户端配置:")
    print(f"   API Key: '{client.api_key}'")
    print(f"   API Key 长度: {len(client.api_key) if client.api_key else 0}")
    
    # 模拟构建 headers
    api_key = client.api_key
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    if api_key and api_key.strip():
        headers["Authorization"] = f"Bearer {api_key.strip()}"
    
    print(f"\n📤 构建的 Headers:")
    for k, v in headers.items():
        if k == "Authorization":
            print(f"   {k}: {v[:30]}..." if len(v) > 30 else f"   {k}: {v}")
        else:
            print(f"   {k}: {v}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(debug_api_key())
