#!/usr/bin/env python3
"""
真实测试 Sequential Thinking 工具调用
"""

import asyncio
from dotenv import load_dotenv
from modules.mcp_platform.mcp_manager_v2 import MCPManagerV2

load_dotenv()

async def test_real_thinking():
    print("=" * 60)
    print("🧠 真实测试 Sequential Thinking")
    print("=" * 60)
    
    try:
        # 初始化管理器
        manager = MCPManagerV2(config_path="config/mcp_config.yaml")
        
        # 获取客户端
        st_client = manager.get_client('sequential_thinking')
        
        # 测试问题
        problem = "为什么 Supabase pgvector 比 Pinecone 更适合我们的项目？请给出3个关键理由。"
        
        print(f"\n📝 测试问题:")
        print(f"   {problem}")
        print("\n⏳ 正在思考...")
        
        # 调用 sequential_thinking 方法
        result = await st_client.sequential_thinking(
            problem=problem,
            max_steps=5,
            thinking_style="analytical"
        )
        
        print("\n" + "=" * 60)
        print("📊 思考结果:")
        print("=" * 60)
        
        if result.get("success"):
            print(f"\n✅ 成功")
            print(f"\n🎯 结论: {result.get('conclusion', 'N/A')}")
            print(f"\n📈 置信度: {result.get('confidence', 0.0)}")
            
            thinking_steps = result.get('thinking_steps', [])
            print(f"\n🧩 思考步骤 ({len(thinking_steps)} 步):")
            for i, step in enumerate(thinking_steps, 1):
                print(f"   {i}. {step}")
                
        else:
            print(f"\n❌ 失败")
            print(f"错误: {result.get('error', 'Unknown')}")
            if 'raw_result' in result:
                print(f"\n原始结果: {result['raw_result']}")
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_thinking())
