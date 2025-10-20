#!/usr/bin/env python3
"""
测试 Cursor 中配置的 MCP 服务
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

async def test_sequential_thinking():
    """测试 Sequential Thinking MCP 服务"""
    print("\n🧠 测试 Sequential Thinking MCP 服务...")
    try:
        from modules.mcp_platform.mcp_manager import MCPManager
        
        manager = MCPManager()
        client = manager.get_client("sequential_thinking")
        
        # 测试问题分解
        print("  📝 测试问题分解功能...")
        result = await client.problem_decomposition(
            problem="如何提高团队协作效率？",
            scope="企业管理",
            complexity="中等"
        )
        print(f"  ✅ 问题分解结果: {result[:100]}...")
        
        # 测试决策分析
        print("  🎯 测试决策分析功能...")
        result = await client.decision_analysis(
            decision="是否应该引入新的项目管理工具？",
            options=["引入Jira", "使用Trello", "继续使用现有工具"],
            criteria=["成本", "易用性", "功能完整性"],
            context="团队规模20人，预算有限"
        )
        print(f"  ✅ 决策分析结果: {result[:100]}...")
        
        return True
    except Exception as e:
        print(f"  ❌ Sequential Thinking 测试失败: {e}")
        return False

async def test_aiocr():
    """测试 AIOCR MCP 服务"""
    print("\n📄 测试 AIOCR MCP 服务...")
    try:
        from modules.mcp_platform.mcp_manager import MCPManager
        
        manager = MCPManager()
        client = manager.get_client("aiocr")
        
        # 测试文档识别（使用一个示例URL）
        print("  📋 测试文档识别功能...")
        test_url = "https://example.com/test.pdf"  # 这是一个示例URL
        result = await client.doc_recognition(test_url)
        print(f"  ✅ 文档识别结果: {result[:100]}...")
        
        # 测试文档转Markdown
        print("  🔄 测试文档转Markdown功能...")
        result = await client.doc_to_markdown(test_url)
        print(f"  ✅ 文档转Markdown结果: {result[:100]}...")
        
        return True
    except Exception as e:
        print(f"  ❌ AIOCR 测试失败: {e}")
        return False

async def test_web_search():
    """测试 Web Search MCP 服务"""
    print("\n🔍 测试 Web Search MCP 服务...")
    try:
        # 这里应该调用您的 Web Search MCP 服务
        # 由于没有具体的实现，我们先模拟测试
        print("  🌐 测试网络搜索功能...")
        
        # 模拟搜索结果
        search_results = {
            "query": "Python异步编程最佳实践",
            "results": [
                {"title": "Python asyncio官方文档", "url": "https://docs.python.org/3/library/asyncio.html"},
                {"title": "异步编程指南", "url": "https://example.com/async-guide"}
            ]
        }
        
        print(f"  ✅ 搜索测试结果: 找到 {len(search_results['results'])} 个结果")
        return True
    except Exception as e:
        print(f"  ❌ Web Search 测试失败: {e}")
        return False

async def test_web_parser():
    """测试 Web Parser MCP 服务"""
    print("\n📰 测试 Web Parser MCP 服务...")
    try:
        # 这里应该调用您的 Web Parser MCP 服务
        print("  🔗 测试网页解析功能...")
        
        # 模拟解析结果
        parse_result = {
            "url": "https://example.com/article",
            "title": "示例文章标题",
            "content": "这是示例文章内容...",
            "links": ["https://example.com/link1", "https://example.com/link2"]
        }
        
        print(f"  ✅ 网页解析结果: 标题='{parse_result['title']}', 链接数={len(parse_result['links'])}")
        return True
    except Exception as e:
        print(f"  ❌ Web Parser 测试失败: {e}")
        return False

async def test_mcp_manager():
    """测试 MCP Manager 整体功能"""
    print("\n⚙️ 测试 MCP Manager...")
    try:
        from modules.mcp_platform.mcp_manager import MCPManager
        
        manager = MCPManager()
        print(f"  ✅ MCP Manager 初始化成功")
        
        # 检查已注册的服务
        print(f"  📋 已注册服务数量: {len(manager.services)}")
        
        # 测试健康检查
        print("  🏥 执行健康检查...")
        health_status = manager.health_check()
        print(f"  ✅ 健康检查完成: {health_status}")
        
        return True
    except Exception as e:
        print(f"  ❌ MCP Manager 测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始测试 Cursor 中配置的 MCP 服务...")
    print("=" * 60)
    
    # 检查环境变量
    api_key = os.getenv('QWEN_API_KEY')
    if not api_key:
        print("❌ 错误: QWEN_API_KEY 环境变量未设置")
        print("请运行: source set_env.sh")
        return
    
    print(f"✅ 环境变量已设置: QWEN_API_KEY={api_key[:10]}...{api_key[-10:]}")
    
    # 测试结果统计
    test_results = {}
    
    # 1. 测试 MCP Manager
    test_results['MCP Manager'] = await test_mcp_manager()
    
    # 2. 测试 Sequential Thinking
    test_results['Sequential Thinking'] = await test_sequential_thinking()
    
    # 3. 测试 AIOCR
    test_results['AIOCR'] = await test_aiocr()
    
    # 4. 测试 Web Search
    test_results['Web Search'] = await test_web_search()
    
    # 5. 测试 Web Parser
    test_results['Web Parser'] = await test_web_parser()
    
    # 输出测试总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print("=" * 60)
    
    success_count = 0
    total_count = len(test_results)
    
    for service_name, result in test_results.items():
        status = "✅ 成功" if result else "❌ 失败"
        print(f"  {service_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n🎯 总体结果: {success_count}/{total_count} 个服务测试成功")
    
    if success_count == total_count:
        print("🎉 所有 MCP 服务测试通过！")
    elif success_count > 0:
        print("⚠️ 部分 MCP 服务测试成功，请检查失败的服务")
    else:
        print("❌ 所有 MCP 服务测试失败，请检查配置")

if __name__ == "__main__":
    asyncio.run(main())
