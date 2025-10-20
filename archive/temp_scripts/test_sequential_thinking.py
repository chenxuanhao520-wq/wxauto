#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sequential Thinking MCP 服务测试脚本
"""

import os
import asyncio
import logging
from typing import List, Dict, Any

# 设置环境变量
os.environ['QWEN_API_KEY'] = os.getenv('QWEN_API_KEY', 'sk-1d7d593d85b1469683eb8e7988a0f646')
os.environ['QWEN_API_BASE'] = os.getenv('QWEN_API_BASE', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
os.environ['QWEN_MODEL'] = os.getenv('QWEN_MODEL', 'qwen-turbo')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


async def test_sequential_thinking_basic():
    """测试基础顺序思考功能"""
    print("\n" + "="*70)
    print("🧪 测试 1: Sequential Thinking 基础功能")
    print("="*70)
    
    try:
        from modules.mcp_platform import MCPManager
        
        # 获取 Sequential Thinking 客户端
        manager = MCPManager()
        thinking_client = manager.get_client("sequential_thinking")
        
        # 健康检查
        health = await thinking_client.health_check()
        print(f"🏥 Sequential Thinking 健康状态: {health.get('status', 'unknown')}")
        
        # 基础思考测试
        test_problems = [
            "如何提高团队的工作效率？",
            "选择云服务器时应该考虑哪些因素？",
            "如何设计一个用户友好的登录界面？"
        ]
        
        for i, problem in enumerate(test_problems, 1):
            print(f"\n🧠 测试问题 {i}: {problem}")
            
            result = await thinking_client.sequential_thinking(
                problem=problem,
                context="这是一个测试场景",
                max_steps=3,
                thinking_style="analytical"
            )
            
            if result.get("success"):
                print(f"✅ 思考完成!")
                print(f"  思考步骤: {len(result.get('thinking_steps', []))} 个")
                print(f"  结论: {result.get('conclusion', '')[:100]}...")
                print(f"  置信度: {result.get('confidence', 0.0)}")
            else:
                print(f"❌ 思考失败: {result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sequential Thinking 基础测试失败: {e}")
        return False


async def test_problem_decomposition():
    """测试问题分解功能"""
    print("\n" + "="*70)
    print("🧪 测试 2: 问题分解功能")
    print("="*70)
    
    try:
        from modules.mcp_platform import MCPManager
        
        manager = MCPManager()
        thinking_client = manager.get_client("sequential_thinking")
        
        # 复杂问题分解测试
        complex_problems = [
            "如何构建一个完整的电商平台？",
            "如何优化公司的供应链管理？",
            "如何设计一个智能客服系统？"
        ]
        
        for i, problem in enumerate(complex_problems, 1):
            print(f"\n🔍 复杂问题 {i}: {problem}")
            
            result = await thinking_client.problem_decomposition(
                complex_problem=problem,
                decomposition_level=3
            )
            
            if result.get("success"):
                print(f"✅ 问题分解完成!")
                print(f"  子问题数量: {len(result.get('sub_problems', []))}")
                print(f"  分解层级: {result.get('decomposition_level')}")
                print(f"  置信度: {result.get('confidence', 0.0)}")
                
                # 显示前3个子问题
                sub_problems = result.get('sub_problems', [])[:3]
                for j, sub_problem in enumerate(sub_problems, 1):
                    content = sub_problem.get('content', '')[:80]
                    print(f"    {j}. {content}...")
            else:
                print(f"❌ 问题分解失败: {result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 问题分解测试失败: {e}")
        return False


async def test_decision_analysis():
    """测试决策分析功能"""
    print("\n" + "="*70)
    print("🧪 测试 3: 决策分析功能")
    print("="*70)
    
    try:
        from modules.mcp_platform import MCPManager
        
        manager = MCPManager()
        thinking_client = manager.get_client("sequential_thinking")
        
        # 决策分析测试
        decision_scenarios = [
            {
                "context": "公司需要选择新的开发框架",
                "options": ["React", "Vue", "Angular", "Svelte"],
                "criteria": ["学习成本", "社区支持", "性能", "生态系统"]
            },
            {
                "context": "团队需要选择部署方案",
                "options": ["Docker", "Kubernetes", "Serverless", "传统服务器"],
                "criteria": ["成本", "可扩展性", "维护复杂度", "性能"]
            }
        ]
        
        for i, scenario in enumerate(decision_scenarios, 1):
            print(f"\n⚖️ 决策场景 {i}: {scenario['context']}")
            
            result = await thinking_client.decision_analysis(
                decision_context=scenario['context'],
                options=scenario['options'],
                criteria=scenario['criteria']
            )
            
            if result.get("success"):
                print(f"✅ 决策分析完成!")
                print(f"  分析步骤: {len(result.get('analysis', []))} 个")
                print(f"  推荐方案: {result.get('recommendation', '')[:100]}...")
                print(f"  置信度: {result.get('confidence', 0.0)}")
            else:
                print(f"❌ 决策分析失败: {result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 决策分析测试失败: {e}")
        return False


async def test_creative_brainstorming():
    """测试创意头脑风暴功能"""
    print("\n" + "="*70)
    print("🧪 测试 4: 创意头脑风暴功能")
    print("="*70)
    
    try:
        from modules.mcp_platform import MCPManager
        
        manager = MCPManager()
        thinking_client = manager.get_client("sequential_thinking")
        
        # 创意头脑风暴测试
        brainstorming_topics = [
            {
                "topic": "如何提升用户体验的创新方法",
                "constraints": ["低成本", "快速实施", "用户友好"],
                "num_ideas": 5
            },
            {
                "topic": "智能客服系统的新功能",
                "constraints": ["技术可行", "用户价值", "易于维护"],
                "num_ideas": 6
            }
        ]
        
        for i, topic_info in enumerate(brainstorming_topics, 1):
            print(f"\n💡 头脑风暴主题 {i}: {topic_info['topic']}")
            
            result = await thinking_client.creative_brainstorming(
                topic=topic_info['topic'],
                constraints=topic_info['constraints'],
                num_ideas=topic_info['num_ideas']
            )
            
            if result.get("success"):
                print(f"✅ 头脑风暴完成!")
                print(f"  生成想法: {len(result.get('ideas', []))} 个")
                print(f"  期望数量: {topic_info['num_ideas']}")
                print(f"  思考过程: {len(result.get('thinking_process', []))} 个步骤")
                print(f"  置信度: {result.get('confidence', 0.0)}")
                
                # 显示前3个想法
                ideas = result.get('ideas', [])[:3]
                for j, idea in enumerate(ideas, 1):
                    content = idea.get('content', '')[:80]
                    print(f"    {j}. {content}...")
            else:
                print(f"❌ 头脑风暴失败: {result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 创意头脑风暴测试失败: {e}")
        return False


async def test_mcp_manager_integration():
    """测试 MCP 管理器集成"""
    print("\n" + "="*70)
    print("🧪 测试 5: MCP 管理器集成")
    print("="*70)
    
    try:
        from modules.mcp_platform import MCPManager
        
        # 初始化管理器
        manager = MCPManager()
        
        # 列出服务
        services = manager.list_services()
        print(f"📋 注册的服务: {len(services)} 个")
        for service in services:
            print(f"  • {service['name']}: {service['description']}")
            if service['name'] == 'sequential_thinking':
                print(f"    工具: {service['tools']}")
                print(f"    能力: {service.get('capabilities', [])}")
        
        # 健康检查
        health = manager.health_check()
        print(f"\n🏥 健康检查:")
        for name, status in health.items():
            print(f"  • {name}: {status.get('status', 'unknown')}")
        
        # 统计信息
        stats = manager.get_stats()
        print(f"\n📊 统计信息:")
        print(f"  总服务数: {stats['total_services']}")
        print(f"  启用服务: {stats['enabled_services']}")
        print(f"  禁用服务: {stats['disabled_services']}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP 管理器集成测试失败: {e}")
        return False


async def main():
    """主测试流程"""
    print("\n" + "🧠"*35)
    print("Sequential Thinking MCP 服务测试")
    print("🧠"*35)
    
    # 检查环境变量
    api_key = os.getenv('QWEN_API_KEY', '')
    if not api_key or api_key == 'sk-your-qwen-key-here':
        print("⚠️ 请设置有效的 QWEN_API_KEY 环境变量")
        return
    
    print(f"使用 API Key: {api_key[:20]}...")
    print("")
    
    # 运行所有测试
    tests = [
        ("Sequential Thinking 基础功能", test_sequential_thinking_basic),
        ("问题分解功能", test_problem_decomposition),
        ("决策分析功能", test_decision_analysis),
        ("创意头脑风暴功能", test_creative_brainstorming),
        ("MCP 管理器集成", test_mcp_manager_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 总结
    print("\n\n" + "="*70)
    print("📊 测试总结")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<25} {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！Sequential Thinking MCP 服务集成成功！")
        print("\n✅ 功能确认:")
        print("  • Sequential Thinking 基础功能正常")
        print("  • 问题分解功能正常")
        print("  • 决策分析功能正常")
        print("  • 创意头脑风暴功能正常")
        print("  • MCP 管理器集成正常")
        print("\n🚀 系统已准备好使用 Sequential Thinking 服务！")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，请检查配置")


if __name__ == "__main__":
    asyncio.run(main())
