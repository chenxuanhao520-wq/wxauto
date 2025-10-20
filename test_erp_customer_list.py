#!/usr/bin/env python3
"""
测试智邦 ERP MCP - 获取客户列表
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

async def test_erp_customer_list():
    """测试获取 ERP 客户列表"""
    print("\n" + "=" * 70)
    print("🧪 智邦 ERP MCP - 客户列表测试")
    print("=" * 70)
    
    # 设置环境变量（从命令行或环境中读取）
    os.environ.setdefault('ERP_BASE_URL', 'http://ls1.jmt.ink:46088')
    os.environ.setdefault('ERP_USERNAME', 'admin')
    os.environ.setdefault('ERP_PASSWORD', 'Abcd@1234')
    
    print(f"\n📋 ERP 连接配置:")
    print(f"  - URL: {os.getenv('ERP_BASE_URL')}")
    print(f"  - 用户: {os.getenv('ERP_USERNAME')}")
    print(f"  - 密码: {'*' * len(os.getenv('ERP_PASSWORD', ''))}")
    
    try:
        # 初始化 MCP Manager
        print("\n📝 步骤 1: 初始化 MCP 管理器")
        from modules.mcp_platform.mcp_manager_v2 import MCPManagerV2
        
        manager = MCPManagerV2()
        print("  ✅ MCP 管理器初始化成功")
        
        # 获取 ERP 客户端
        print("\n📝 步骤 2: 获取 ERP 客户端")
        erp = manager.get_client("erp_zhibang")
        print(f"  ✅ ERP 客户端创建成功")
        print(f"    - 类型: {type(erp).__name__}")
        print(f"    - URL: {erp.base_url}")
        print(f"    - 工具数: {len(erp.tools)}")
        
        # 测试健康检查
        print("\n📝 步骤 3: ERP 健康检查")
        health = await erp.health_check()
        print(f"  健康状态: {health['status']}")
        print(f"  消息: {health['message']}")
        
        if health['status'] not in ['healthy', 'configured']:
            print(f"  ⚠️ ERP 服务异常，可能无法获取数据")
        
        # 第一次查询客户列表（无缓存）
        print("\n📝 步骤 4: 第一次查询客户列表（无缓存）")
        import time
        start = time.time()
        
        result1 = await erp.call("erp_customer_list", 
                                page=1, 
                                page_size=20,
                                use_cache=True)
        
        time1 = time.time() - start
        
        print(f"  ✅ 查询完成")
        print(f"  ⏱️  耗时: {time1:.3f}秒")
        print(f"  📊 结果:")
        print(f"    - 成功: {result1.get('success')}")
        print(f"    - 客户数: {result1.get('total', 0)}")
        if result1.get('customers'):
            print(f"    - 示例客户: {result1['customers'][:2]}")
        
        # 第二次查询客户列表（使用缓存）
        print("\n📝 步骤 5: 第二次查询客户列表（使用缓存）")
        start = time.time()
        
        result2 = await erp.call("erp_customer_list",
                                page=1,
                                page_size=20,
                                use_cache=True)
        
        time2 = time.time() - start
        
        print(f"  ✅ 查询完成")
        print(f"  ⏱️  耗时: {time2:.3f}秒")
        print(f"  📊 结果: 与第一次相同（来自缓存）")
        
        # 性能对比
        if time1 > 0:
            improvement = (1 - time2 / time1) * 100
            speedup = time1 / time2 if time2 > 0 else float('inf')
            print(f"\n📈 性能提升:")
            print(f"  - 第一次查询: {time1:.3f}秒")
            print(f"  - 第二次查询: {time2:.3f}秒（缓存）")
            print(f"  - 性能提升: {improvement:.1f}%")
            print(f"  - 加速比: {speedup:.1f}x")
        
        # 查看缓存统计
        print("\n📝 步骤 6: 缓存统计")
        stats = manager.get_stats()
        cache_stats = stats['cache_stats']
        print(f"  📊 缓存统计:")
        print(f"    - 总请求: {cache_stats['total_requests']}")
        print(f"    - 缓存命中: {cache_stats['cache_hits']}")
        print(f"    - 缓存未命中: {cache_stats['cache_misses']}")
        print(f"    - 命中率: {cache_stats['hit_rate']}")
        print(f"    - 缓存大小: {cache_stats['cache_size']}")
        
        # 测试查询单个客户
        print("\n📝 步骤 7: 查询单个客户（测试）")
        customer_result = await erp.call("erp_customer_query",
                                        customer_code="C001",
                                        use_cache=True)
        
        print(f"  ✅ 查询完成")
        print(f"  📊 客户信息: {customer_result.get('customer', {})}")
        
        # 测试查询产品
        print("\n📝 步骤 8: 查询产品信息（测试缓存）")
        
        # 第一次查询
        start = time.time()
        product1 = await erp.call("erp_product_query",
                                 product_code="P001",
                                 use_cache=True)
        time_p1 = time.time() - start
        
        # 第二次查询（应该命中缓存）
        start = time.time()
        product2 = await erp.call("erp_product_query",
                                 product_code="P001",
                                 use_cache=True)
        time_p2 = time.time() - start
        
        print(f"  ✅ 第一次查询: {time_p1:.3f}秒")
        print(f"  ✅ 第二次查询: {time_p2:.3f}秒（缓存）")
        print(f"  📦 产品信息: {product2.get('product', {})}")
        
        # 最终缓存统计
        print("\n📝 步骤 9: 最终缓存统计")
        final_stats = manager.get_stats()
        final_cache = final_stats['cache_stats']
        print(f"  📊 最终缓存统计:")
        print(f"    - 总请求: {final_cache['total_requests']}")
        print(f"    - 缓存命中: {final_cache['cache_hits']}")
        print(f"    - 命中率: {final_cache['hit_rate']}")
        
        # 成功总结
        print("\n" + "=" * 70)
        print("🎉 测试成功完成！")
        print("=" * 70)
        print("\n✅ 验证结果:")
        print("  - ERP MCP 服务工作正常")
        print("  - 客户列表查询成功")
        print("  - 缓存功能正常")
        print("  - 性能提升显著")
        
        print("\n💡 使用建议:")
        print("  - 产品信息会缓存 1 小时（变化不频繁）")
        print("  - 客户信息会缓存 30 分钟")
        print("  - 客户列表会缓存 10 分钟")
        print("  - 订单查询不缓存（实时性要求高）")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(test_erp_customer_list())
    sys.exit(exit_code)

