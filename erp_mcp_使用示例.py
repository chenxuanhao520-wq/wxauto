#!/usr/bin/env python3
"""
智邦国际 ERP MCP 服务使用示例
展示如何通过 MCP 中台访问 ERP 功能
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))


async def example_customer_management():
    """示例：客户管理"""
    print("\n" + "=" * 70)
    print("📋 示例 1: 客户管理")
    print("=" * 70)
    
    from modules.mcp_platform.mcp_manager_v2 import MCPManagerV2
    
    # 初始化 MCP 管理器
    manager = MCPManagerV2()
    erp = manager.get_client("erp_zhibang")
    
    # 1. 创建客户
    print("\n🔹 创建新客户:")
    result = await erp.call("erp_customer_create", customer_data={
        "name": "科技有限公司",
        "contact_name": "李经理",
        "phone": "13912345678",
        "wechat_id": "wxid_abc123",
        "remark": "通过微信客服咨询充电桩产品"
    })
    print(f"  结果: {result}")
    
    # 2. 查询客户（第一次，调用 API）
    print("\n🔹 查询客户信息（第一次）:")
    customer = await erp.call("erp_customer_query", 
                             customer_code="C001",
                             use_cache=True)
    print(f"  结果: {customer}")
    
    # 3. 再次查询客户（第二次，使用缓存）
    print("\n🔹 查询客户信息（第二次，缓存命中）:")
    customer = await erp.call("erp_customer_query",
                             customer_code="C001",
                             use_cache=True)
    print(f"  结果: {customer}")
    print(f"  💡 第二次查询会从缓存返回，响应速度提升 99%+")
    
    # 4. 获取客户列表
    print("\n🔹 获取客户列表:")
    customers = await erp.call("erp_customer_list",
                              page=1,
                              page_size=10,
                              use_cache=True)
    print(f"  结果: 获取到 {customers.get('total', 0)} 个客户")
    print(f"  前3个客户:")
    for i, cust in enumerate(customers.get('customers', [])[:3], 1):
        print(f"    {i}. {cust.get('name')} - {cust.get('phone')}")


async def example_product_query():
    """示例：产品查询"""
    print("\n" + "=" * 70)
    print("📦 示例 2: 产品查询（高频缓存）")
    print("=" * 70)
    
    from modules.mcp_platform.mcp_manager_v2 import MCPManagerV2
    
    manager = MCPManagerV2()
    erp = manager.get_client("erp_zhibang")
    
    # 查询产品（自动缓存 1 小时）
    print("\n🔹 查询产品信息:")
    product = await erp.call("erp_product_query",
                            product_code="P001",
                            use_cache=True)
    print(f"  结果: {product.get('product', {})}")
    print(f"  💡 产品信息变化不频繁，缓存 1 小时")
    print(f"  💡 大幅减少 ERP API 调用，降低成本")


async def example_order_management():
    """示例：订单管理"""
    print("\n" + "=" * 70)
    print("📑 示例 3: 订单管理（不缓存）")
    print("=" * 70)
    
    from modules.mcp_platform.mcp_manager_v2 import MCPManagerV2
    
    manager = MCPManagerV2()
    erp = manager.get_client("erp_zhibang")
    
    # 1. 创建订单
    print("\n🔹 创建订单:")
    order = await erp.call("erp_order_create", order_data={
        "customer_code": "C001",
        "products": [
            {"code": "P001", "quantity": 10, "price": 1000},
            {"code": "P002", "quantity": 5, "price": 2000}
        ],
        "remark": "客户下单购买充电桩"
    })
    print(f"  结果: {order}")
    
    # 2. 查询订单（不缓存，保证实时性）
    print("\n🔹 查询订单状态:")
    order_info = await erp.call("erp_order_query",
                                order_code="O001",
                                use_cache=False)
    print(f"  结果: {order_info}")
    print(f"  💡 订单查询不缓存，保证实时性")


async def example_cache_management():
    """示例：缓存管理"""
    print("\n" + "=" * 70)
    print("📊 示例 4: 缓存统计和管理")
    print("=" * 70)
    
    from modules.mcp_platform.mcp_manager_v2 import MCPManagerV2
    
    manager = MCPManagerV2()
    
    # 查看整体统计
    print("\n🔹 MCP 中台统计:")
    stats = manager.get_stats()
    
    print(f"  服务统计:")
    print(f"    - 总服务数: {stats['total_services']}")
    print(f"    - 启用服务: {stats['enabled_services']}")
    
    print(f"\n  缓存统计:")
    cache = stats['cache_stats']
    print(f"    - 总请求数: {cache['total_requests']}")
    print(f"    - 缓存命中: {cache['cache_hits']}")
    print(f"    - 缓存未命中: {cache['cache_misses']}")
    print(f"    - 命中率: {cache['hit_rate']}")
    print(f"    - 缓存大小: {cache['cache_size']}")
    
    # 清空缓存
    print("\n🔹 清空缓存:")
    manager.clear_cache()
    print(f"  ✅ 缓存已清空")


async def example_unified_interface():
    """示例：统一接口管理"""
    print("\n" + "=" * 70)
    print("🎯 示例 5: 统一 MCP 接口（核心优势）")
    print("=" * 70)
    
    from modules.mcp_platform.mcp_manager_v2 import MCPManagerV2
    
    manager = MCPManagerV2()
    
    print("\n🔹 通过统一的 MCP 中台访问所有服务:")
    
    # 1. AIOCR 服务
    print("\n  1️⃣ AIOCR 文档识别:")
    print("     aiocr = manager.get_client('aiocr')")
    print("     result = await aiocr.call('doc_recognition', file='doc.pdf')")
    
    # 2. Sequential Thinking 服务
    print("\n  2️⃣ Sequential Thinking 结构化思考:")
    print("     thinking = manager.get_client('sequential_thinking')")
    print("     result = await thinking.call('problem_decomposition', problem='...')")
    
    # 3. ERP 服务
    print("\n  3️⃣ 智邦 ERP 管理:")
    print("     erp = manager.get_client('erp_zhibang')")
    print("     result = await erp.call('erp_customer_list', page=1)")
    
    print("\n  💡 优势:")
    print("     ✅ 统一的调用方式")
    print("     ✅ 统一的缓存管理")
    print("     ✅ 统一的监控体系")
    print("     ✅ 统一的配置管理")
    
    # 查看所有服务
    print("\n🔹 已注册的 MCP 服务:")
    services = manager.list_services()
    for i, svc in enumerate(services, 1):
        print(f"  {i}. {svc['name']}: {svc['description']}")
        print(f"     工具数: {len(svc['tools'])}, 缓存: {'启用' if svc['cache_enabled'] else '禁用'}")


async def main():
    """运行所有示例"""
    print("\n🚀 智邦国际 ERP MCP 服务使用示例")
    print("=" * 70)
    
    # 运行所有示例
    await example_customer_management()
    await example_product_query()
    await example_order_management()
    await example_cache_management()
    await example_unified_interface()
    
    print("\n" + "=" * 70)
    print("✅ 所有示例运行完成")
    print("=" * 70)
    print("\n💡 提示:")
    print("  - 所有 MCP 服务通过统一接口访问")
    print("  - 查询操作自动缓存，提升性能")
    print("  - 写操作不缓存，保证数据一致性")
    print("  - 可通过 manager.get_stats() 查看统计")
    print("\n📚 更多信息:")
    print("  - 配置文件: config/mcp_config.yaml")
    print("  - 测试脚本: test_erp_customer_list.py")
    print("  - 文档: 🎉智邦ERP_MCP集成完成报告.md")


if __name__ == "__main__":
    asyncio.run(main())

