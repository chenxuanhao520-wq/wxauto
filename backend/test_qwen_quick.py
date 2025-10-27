#!/usr/bin/env python3
import asyncio
from dotenv import load_dotenv
import os
from modules.mcp_platform.qwen_thinking_client import QwenThinkingClient

load_dotenv()

async def test():
    print("🧠 快速测试通义千问深度思考")
    print("=" * 60)
    
    api_key = os.getenv('QWEN_API_KEY')
    print(f"API Key: {api_key[:20]}...")
    
    client = QwenThinkingClient(api_key)
    
    problem = "为什么Supabase pgvector比Pinecone更适合项目？"
    print(f"\n问题: {problem}")
    print("思考中...")
    
    result = await client.sequential_thinking(problem, max_steps=3)
    
    if result.get("success"):
        print(f"\n✅ 成功!")
        print(f"结论: {result.get('conclusion', 'N/A')[:200]}")
    else:
        print(f"\n❌ 失败: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test())
