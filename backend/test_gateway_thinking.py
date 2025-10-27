#!/usr/bin/env python3
"""
测试 AI 网关的深度思考功能
"""

import asyncio
import json
from dotenv import load_dotenv
from modules.ai_gateway.gateway import AIGateway

load_dotenv()


async def test_deep_thinking():
    """测试深度思考"""
    print("=" * 70)
    print("🧠 测试 AI 网关 - 深度思考功能")
    print("=" * 70)
    
    # 初始化 AI 网关
    gateway = AIGateway(
        primary_provider="qwen",
        primary_model="qwen-turbo",
        enable_smart_routing=True
    )
    
    print("\n📋 网关状态:")
    health = gateway.health_check()
    print(json.dumps(health, indent=2, ensure_ascii=False))
    
    # 测试深度思考
    problem = "为什么 Supabase pgvector 比 Pinecone 更适合我们的智能客服项目？请给出3个关键理由。"
    
    print(f"\n📝 问题: {problem}")
    print("\n⏳ 深度思考中...")
    
    result = await gateway.deep_thinking(
        problem=problem,
        max_steps=5,
        thinking_style="analytical"
    )
    
    print("\n" + "=" * 70)
    if result.get("success"):
        print("✅ 思考完成!")
        print(f"\n🎯 结论:\n{result.get('conclusion', 'N/A')}")
        
        steps = result.get('thinking_steps', [])
        print(f"\n🧩 思考步骤 ({len(steps)} 步):")
        for i, step in enumerate(steps[:3], 1):  # 只显示前3步
            print(f"\n【步骤{i}】")
            content = step.get('content', '')
            print(content[:150] + "..." if len(content) > 150 else content)
        
        if len(steps) > 3:
            print(f"\n... 还有 {len(steps) - 3} 个步骤")
        
        usage = result.get('usage', {})
        print(f"\n📊 Token 使用: 输入 {usage.get('input_tokens', 0)}, 输出 {usage.get('output_tokens', 0)}")
    else:
        print(f"❌ 失败: {result.get('error', 'Unknown')}")


async def test_decision_analysis():
    """测试决策分析"""
    print("\n" + "=" * 70)
    print("⚖️ 测试 AI 网关 - 决策分析功能")
    print("=" * 70)
    
    gateway = AIGateway()
    
    decision_context = "我们的微信客服系统需要选择向量数据库方案"
    options = [
        "Pinecone（云服务，按量付费）",
        "Supabase pgvector（开源，零成本）",
        "Milvus（自建，需维护）"
    ]
    criteria = ["成本", "性能", "可维护性", "扩展性"]
    
    print(f"\n📋 决策背景: {decision_context}")
    print(f"📌 方案选项: {', '.join(options)}")
    print(f"📏 评估标准: {', '.join(criteria)}")
    print("\n⏳ 分析中...")
    
    result = await gateway.decision_analysis(
        decision_context=decision_context,
        options=options,
        criteria=criteria
    )
    
    print("\n" + "=" * 70)
    if result.get("success"):
        print("✅ 决策分析完成!")
        print(f"\n💡 推荐方案: {result.get('recommendation', 'N/A')}")
        
        analysis = result.get('analysis', '')
        print(f"\n📄 分析摘要:\n{analysis[:300]}..." if len(analysis) > 300 else f"\n📄 分析:\n{analysis}")
    else:
        print(f"❌ 失败: {result.get('error', 'Unknown')}")


if __name__ == "__main__":
    asyncio.run(test_deep_thinking())
    asyncio.run(test_decision_analysis())
