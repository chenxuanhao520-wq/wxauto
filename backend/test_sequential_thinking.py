#!/usr/bin/env python3
"""
测试 Sequential Thinking MCP 服务
深度思考推理能力测试
"""

import asyncio
import json
import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.mcp_platform.mcp_manager_v2 import MCPManagerV2


async def test_sequential_thinking():
    """测试 Sequential Thinking 服务"""
    print("=" * 60)
    print("🧠 Sequential Thinking MCP 深度思考测试")
    print("=" * 60)
    
    try:
        # 初始化 MCP Manager V2（自动加载服务）
        print("\n📋 初始化 MCP Manager V2...")
        manager = MCPManagerV2(config_path="config/mcp_config.yaml")
        
        print(f"✅ MCP Manager 初始化成功")
        print(f"📦 已加载服务: {list(manager.services.keys())}")
        
        # 检查 Sequential Thinking 服务
        if 'sequential_thinking' not in manager.services:
            print("❌ Sequential Thinking 服务未加载")
            return
        
        # 获取客户端
        st_client = manager.get_client('sequential_thinking')
        print(f"\n✅ Sequential Thinking 客户端已就绪")
        
        # 健康检查
        print("\n🏥 执行健康检查...")
        health = await st_client.health_check()
        print(f"健康状态: {json.dumps(health, indent=2, ensure_ascii=False)}")
        
        # 测试 1: 基础推理测试
        print("\n" + "=" * 60)
        print("🧪 测试 1: 基础逻辑推理")
        print("-" * 60)
        
        test_query_1 = """
        问题：如何提升智能客服系统的响应速度？
        
        请从以下角度分析：
        1. 技术架构优化
        2. 算法优化
        3. 缓存策略
        4. 数据库优化
        """
        
        print(f"📝 问题:\n{test_query_1}")
        print("\n⏳ 正在推理...")
        
        result_1 = await st_client._call_tool(
            "sequential_thinking",
            {"query": test_query_1}
        )
        
        print("\n📊 推理结果:")
        print(json.dumps(result_1, indent=2, ensure_ascii=False))
        
        # 测试 2: 复杂决策分析
        print("\n" + "=" * 60)
        print("🧪 测试 2: 复杂决策分析")
        print("-" * 60)
        
        test_query_2 = """
        场景：我们的微信客服系统需要选择向量数据库方案
        
        候选方案：
        A. Pinecone（云服务，按量付费）
        B. Supabase pgvector（开源，零成本）
        C. Milvus（自建，需维护）
        
        决策维度：
        - 成本
        - 性能
        - 可维护性
        - 扩展性
        
        请进行全面分析并给出推荐。
        """
        
        print(f"📝 问题:\n{test_query_2}")
        print("\n⏳ 正在推理...")
        
        result_2 = await st_client._call_tool(
            "decision_analysis",
            {"query": test_query_2}
        )
        
        print("\n📊 决策分析结果:")
        print(json.dumps(result_2, indent=2, ensure_ascii=False))
        
        # 测试 3: 问题分解
        print("\n" + "=" * 60)
        print("🧪 测试 3: 问题分解")
        print("-" * 60)
        
        test_query_3 = """
        大问题：如何构建一个完整的智能客服中台系统？
        
        请将这个问题分解为可执行的子任务，并给出实施顺序。
        """
        
        print(f"📝 问题:\n{test_query_3}")
        print("\n⏳ 正在推理...")
        
        result_3 = await st_client._call_tool(
            "problem_decomposition",
            {"query": test_query_3}
        )
        
        print("\n📊 问题分解结果:")
        print(json.dumps(result_3, indent=2, ensure_ascii=False))
        
        # 测试 4: 创意头脑风暴
        print("\n" + "=" * 60)
        print("🧪 测试 4: 创意头脑风暴")
        print("-" * 60)
        
        test_query_4 = """
        主题：微信智能客服的创新功能点
        
        目标用户：B2B企业客户
        场景：售前咨询、售后支持、订单查询
        
        请给出5个创新功能点的想法。
        """
        
        print(f"📝 问题:\n{test_query_4}")
        print("\n⏳ 正在推理...")
        
        result_4 = await st_client._call_tool(
            "creative_brainstorming",
            {"query": test_query_4}
        )
        
        print("\n📊 头脑风暴结果:")
        print(json.dumps(result_4, indent=2, ensure_ascii=False))
        
        print("\n" + "=" * 60)
        print("✅ Sequential Thinking 测试全部完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def quick_test():
    """快速测试单个问题"""
    print("=" * 60)
    print("⚡ Sequential Thinking 快速测试")
    print("=" * 60)
    
    try:
        manager = MCPManagerV2(config_path="config/mcp_config.yaml")
        
        st_client = manager.get_client('sequential_thinking')
        if not st_client:
            print("❌ Sequential Thinking 服务不可用")
            return
        
        # 简单问题测试
        query = "为什么 Supabase pgvector 比 Pinecone 更适合我们的项目？请给出3个关键理由。"
        
        print(f"\n📝 问题: {query}")
        print("\n⏳ 思考中...")
        
        result = await st_client._call_tool(
            "sequential_thinking",
            {"query": query}
        )
        
        print("\n💡 思考结果:")
        # 提取文本内容
        if isinstance(result, dict) and 'content' in result:
            for item in result['content']:
                if item.get('type') == 'text':
                    print(item.get('text', ''))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ 快速测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # 快速测试模式
        asyncio.run(quick_test())
    else:
        # 完整测试模式
        asyncio.run(test_sequential_thinking())
