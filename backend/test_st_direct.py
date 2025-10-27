#!/usr/bin/env python3
"""
直接测试通义千问 MCP Sequential Thinking API
"""

import asyncio
import httpx
import json
from dotenv import load_dotenv
import os

load_dotenv()

async def test_sequential_thinking_direct():
    """直接调用 Sequential Thinking API"""
    
    api_key = os.getenv('QWEN_API_KEY')
    endpoint = "https://dashscope.aliyuncs.com/api/v1/mcps/Sequential_Thinking/sse"
    
    print("=" * 60)
    print("🧠 直接测试 Sequential Thinking MCP API")
    print("=" * 60)
    print(f"\n📍 端点: {endpoint}")
    print(f"🔑 API Key: {api_key[:20]}...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list"
    }
    
    print(f"\n📤 请求: {json.dumps(payload, ensure_ascii=False)}")
    print(f"\n⏳ 发送请求...")
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                endpoint,
                headers=headers,
                json=payload
            )
            
            print(f"\n📥 响应状态: {response.status_code}")
            print(f"📋 响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                content = response.text
                print(f"\n📄 响应内容 (前500字符):")
                print(content[:500])
                print("\n" + "=" * 60)
                print("✅ API 调用成功!")
            else:
                print(f"\n❌ API 调用失败: {response.status_code}")
                print(f"错误信息: {response.text}")
    
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sequential_thinking_direct())
