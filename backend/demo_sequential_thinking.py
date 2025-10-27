#!/usr/bin/env python3
"""
Sequential Thinking 工具使用示例
演示如何使用结构化思考能力解决实际问题

使用前提：
1. 确保已配置 QWEN_API_KEY 环境变量
2. 或在 config/mcp_config.yaml 中配置 API Key
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量（如果未设置）
if not os.getenv('QWEN_API_KEY'):
    print("⚠️ 检测到 QWEN_API_KEY 未设置")
    print("请输入您的通义千问 API Key（或按回车跳过使用配置文件）：")
    api_key = input().strip()
    if api_key:
        os.environ['QWEN_API_KEY'] = api_key
        print("✅ API Key 已设置")
    else:
        print("❌ 未设置 API Key，将尝试从配置文件读取")
        print("如果配置文件中也未配置，调用将失败")
        print("")

from modules.mcp_platform.mcp_manager_v2 import MCPManagerV2


async def demo_basic_thinking():
    """示例 1: 基础结构化思考"""
    print("\n" + "=" * 70)
    print("📌 示例 1: 基础结构化思考")
    print("=" * 70)
    
    manager = MCPManagerV2(config_path="config/mcp_config.yaml")
    st_client = manager.get_client('sequential_thinking')
    
    # 问题：如何优化微信客服系统的响应时间
    problem = """
    问题：我们的微信智能客服系统平均响应时间是3秒，用户反馈较慢。
    如何将响应时间优化到1秒以内？
    
    当前架构：
    - 后端：FastAPI + Python
    - 数据库：Supabase PostgreSQL
    - AI模型：通义千问（平均耗时2秒）
    - 缓存：内存缓存
    """
    
    print(f"🎯 待解决问题:\n{problem}\n")
    print("⏳ 开始结构化思考分析...\n")
    
    result = await st_client.sequential_thinking(
        problem=problem,
        max_steps=5,
        thinking_style="analytical"
    )
    
    # 输出结果
    if result.get("success"):
        print("✅ 思考分析完成！\n")
        print(f"📊 结论: {result.get('conclusion', '暂无结论')}\n")
        print(f"🎯 置信度: {result.get('confidence', 0):.2%}\n")
        
        print("🧠 思考步骤:")
        for i, step in enumerate(result.get('thinking_steps', []), 1):
            print(f"\n步骤 {i}:")
            print(f"  {step}")
    else:
        print(f"❌ 分析失败: {result.get('error', '未知错误')}")


async def demo_decision_analysis():
    """示例 2: 决策分析"""
    print("\n" + "=" * 70)
    print("📌 示例 2: 决策分析 - 选择向量数据库方案")
    print("=" * 70)
    
    manager = MCPManagerV2(config_path="config/mcp_config.yaml")
    st_client = manager.get_client('sequential_thinking')
    
    # 决策背景
    decision_context = """
    我们需要为智能客服系统选择向量数据库存储方案，
    用于RAG知识检索，预计数据量100万条对话记录。
    """
    
    # 可选方案
    options = [
        "Pinecone: 云服务，按量付费，月成本约$70，免运维",
        "Supabase pgvector: 开源免费，与现有PostgreSQL集成，需要自己优化",
        "Milvus: 高性能开源方案，需要独立部署和运维"
    ]
    
    # 评估标准
    criteria = [
        "成本（一次性+运维）",
        "查询性能（延迟要求<50ms）",
        "可维护性",
        "扩展性（未来可能达到1000万条）"
    ]
    
    print(f"🎯 决策背景:\n{decision_context}\n")
    print("📋 可选方案:")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    
    print(f"\n📊 评估标准: {', '.join(criteria)}\n")
    print("⏳ 开始决策分析...\n")
    
    result = await st_client.decision_analysis(
        decision_context=decision_context,
        options=options,
        criteria=criteria
    )
    
    # 输出结果
    if result.get("success"):
        print("✅ 决策分析完成！\n")
        print(f"💡 推荐方案:\n{result.get('recommendation', '暂无推荐')}\n")
        print(f"🎯 置信度: {result.get('confidence', 0):.2%}\n")
        
        print("📊 分析过程:")
        for i, step in enumerate(result.get('analysis', []), 1):
            print(f"\n分析 {i}:")
            print(f"  {step}")
    else:
        print(f"❌ 分析失败: {result.get('error', '未知错误')}")


async def demo_problem_decomposition():
    """示例 3: 问题分解"""
    print("\n" + "=" * 70)
    print("📌 示例 3: 问题分解 - 构建智能客服中台")
    print("=" * 70)
    
    manager = MCPManagerV2(config_path="config/mcp_config.yaml")
    st_client = manager.get_client('sequential_thinking')
    
    # 复杂问题
    complex_problem = """
    构建一个支持多租户的微信智能客服中台系统，
    需要具备：AI智能回复、客户管理、知识库检索、ERP集成、数据统计功能。
    """
    
    print(f"🎯 复杂问题:\n{complex_problem}\n")
    print("⏳ 开始问题分解...\n")
    
    result = await st_client.problem_decomposition(
        complex_problem=complex_problem,
        decomposition_level=5
    )
    
    # 输出结果
    if result.get("success"):
        print("✅ 问题分解完成！\n")
        print(f"📊 共分解为 {len(result.get('sub_problems', []))} 个子问题\n")
        print(f"🎯 置信度: {result.get('confidence', 0):.2%}\n")
        
        print("📋 子问题清单:")
        for i, sub in enumerate(result.get('sub_problems', []), 1):
            print(f"\n子问题 {i}:")
            print(f"  {sub}")
    else:
        print(f"❌ 分解失败: {result.get('error', '未知错误')}")


async def demo_creative_brainstorming():
    """示例 4: 创意头脑风暴"""
    print("\n" + "=" * 70)
    print("📌 示例 4: 创意头脑风暴 - 提升客户满意度")
    print("=" * 70)
    
    manager = MCPManagerV2(config_path="config/mcp_config.yaml")
    st_client = manager.get_client('sequential_thinking')
    
    # 头脑风暴主题
    topic = "如何通过AI技术提升B2B客户的服务满意度"
    
    # 约束条件
    constraints = [
        "技术实现难度中等以下",
        "3个月内可以落地",
        "成本增加不超过20%",
        "不改变现有核心架构"
    ]
    
    print(f"🎯 头脑风暴主题:\n{topic}\n")
    print("⚠️ 约束条件:")
    for c in constraints:
        print(f"  - {c}")
    
    print("\n⏳ 开始创意头脑风暴...\n")
    
    result = await st_client.creative_brainstorming(
        topic=topic,
        constraints=constraints,
        num_ideas=5
    )
    
    # 输出结果
    if result.get("success"):
        print("✅ 头脑风暴完成！\n")
        print(f"💡 生成了 {result.get('total_generated', 0)} 个创意想法\n")
        print(f"🎯 置信度: {result.get('confidence', 0):.2%}\n")
        
        print("🌟 创意想法:")
        for i, idea in enumerate(result.get('ideas', []), 1):
            print(f"\n想法 {i}:")
            print(f"  {idea}")
    else:
        print(f"❌ 头脑风暴失败: {result.get('error', '未知错误')}")


async def demo_real_scenario():
    """示例 5: 真实业务场景 - 客户流失预警"""
    print("\n" + "=" * 70)
    print("📌 示例 5: 真实业务场景 - 设计客户流失预警系统")
    print("=" * 70)
    
    manager = MCPManagerV2(config_path="config/mcp_config.yaml")
    st_client = manager.get_client('sequential_thinking')
    
    # 业务问题
    business_problem = """
    业务背景：
    我们的智能客服系统服务了200家B2B客户，但最近3个月流失率达到15%。
    分析发现流失客户有以下共同特征：
    1. 响应时间 > 5秒
    2. 问题解决率 < 60%
    3. 连续7天无客服互动
    4. 客户满意度评分 < 3分
    
    需求：
    设计一个客户流失预警系统，能够提前识别高风险客户并触发挽留措施。
    
    技术栈：
    - 后端: Python + FastAPI
    - 数据库: Supabase PostgreSQL
    - AI: 通义千问 + pgvector
    
    请给出完整的技术方案，包括：
    1. 数据指标体系设计
    2. 预警规则引擎
    3. 自动化挽留策略
    4. 实施步骤
    """
    
    print(f"🎯 业务问题:\n{business_problem}\n")
    print("⏳ 开始深度思考分析...\n")
    
    result = await st_client.sequential_thinking(
        problem=business_problem,
        max_steps=8,
        thinking_style="analytical"
    )
    
    # 输出详细结果
    if result.get("success"):
        print("✅ 深度分析完成！\n")
        
        print("=" * 70)
        print("📊 完整分析报告")
        print("=" * 70)
        
        print(f"\n🎯 问题: {result.get('problem', '')[:100]}...\n")
        
        print("🧠 思考过程:")
        for i, step in enumerate(result.get('thinking_steps', []), 1):
            print(f"\n【步骤 {i}】")
            print(f"{step}")
        
        print(f"\n" + "=" * 70)
        print("💡 最终结论:")
        print("=" * 70)
        print(f"\n{result.get('conclusion', '暂无结论')}\n")
        
        print(f"🎯 置信度: {result.get('confidence', 0):.2%}\n")
        
        if result.get('alternatives'):
            print("🔄 替代方案:")
            for alt in result.get('alternatives', []):
                print(f"  - {alt}")
        
        print("\n" + "=" * 70)
        
    else:
        print(f"❌ 分析失败: {result.get('error', '未知错误')}")


async def main():
    """主函数 - 运行所有示例"""
    print("\n" + "🌟" * 35)
    print("  Sequential Thinking 工具完整使用示例")
    print("  演示时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🌟" * 35)
    
    try:
        # 运行所有示例
        await demo_basic_thinking()          # 示例1: 基础思考
        await demo_decision_analysis()       # 示例2: 决策分析
        await demo_problem_decomposition()   # 示例3: 问题分解
        await demo_creative_brainstorming()  # 示例4: 创意头脑风暴
        await demo_real_scenario()           # 示例5: 真实业务场景
        
        print("\n" + "=" * 70)
        print("🎉 所有示例运行完成！")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行完整示例
    asyncio.run(main())
