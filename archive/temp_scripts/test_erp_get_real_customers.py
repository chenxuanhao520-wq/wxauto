#!/usr/bin/env python3
"""
获取真实的智邦 ERP 客户列表
详细输出所有响应数据
"""

import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent))


async def get_real_customer_list():
    """获取真实的客户列表"""
    print("\n" + "=" * 70)
    print("🔍 智邦 ERP - 获取真实客户列表")
    print("=" * 70)
    
    # 设置凭据
    os.environ['ERP_BASE_URL'] = 'http://ls1.jmt.ink:46088'
    os.environ['ERP_USERNAME'] = 'admin'
    os.environ['ERP_PASSWORD'] = 'Abcd@1234'
    
    print(f"\n📋 连接信息:")
    print(f"  URL: {os.environ['ERP_BASE_URL']}")
    print(f"  用户: {os.environ['ERP_USERNAME']}")
    
    try:
        # 初始化 MCP Manager
        from modules.mcp_platform.mcp_manager_v2 import MCPManagerV2
        
        manager = MCPManagerV2()
        erp = manager.get_client("erp_zhibang")
        
        print(f"\n✅ ERP 客户端初始化成功")
        
        # 测试健康检查
        print(f"\n📝 执行健康检查...")
        health = await erp.health_check()
        print(f"  状态: {health['status']}")
        print(f"  消息: {health['message']}")
        
        if health['status'] != 'healthy':
            print(f"\n⚠️  ERP 连接异常，可能无法获取数据")
            return
        
        # 获取客户列表
        print(f"\n📝 查询客户列表（第 1 页，每页 20 条）...")
        
        result = await erp.call("erp_customer_list",
                               page=1,
                               page_size=20,
                               use_cache=False)  # 不使用缓存，确保获取最新数据
        
        print(f"\n📊 查询结果:")
        print(f"  成功: {result.get('success')}")
        print(f"  客户总数: {result.get('total', 0)}")
        print(f"  当前页: {result.get('page')}")
        print(f"  每页数量: {result.get('page_size')}")
        
        customers = result.get('customers', [])
        
        if customers:
            print(f"\n📋 客户列表 (共 {len(customers)} 个):")
            print("=" * 70)
            
            for i, customer in enumerate(customers, 1):
                print(f"\n客户 {i}:")
                # 打印所有字段
                for key, value in customer.items():
                    print(f"  {key}: {value}")
            
            print("\n" + "=" * 70)
            print(f"✅ 成功获取 {len(customers)} 个客户")
            
        else:
            print(f"\n⚠️  没有获取到客户数据")
            print(f"\n可能的原因:")
            print(f"  1. ERP 系统中确实没有客户数据")
            print(f"  2. 需要特定的查询条件或权限")
            print(f"  3. API 返回格式需要调整")
            
            # 尝试不同的页码
            print(f"\n📝 尝试查询不同页码...")
            for page in [1, 2]:
                result = await erp.call("erp_customer_list",
                                       page=page,
                                       page_size=50,
                                       use_cache=False)
                print(f"  第 {page} 页: {result.get('total', 0)} 个客户")
        
        # 显示缓存统计
        print(f"\n📊 缓存统计:")
        stats = manager.get_stats()
        cache_stats = stats['cache_stats']
        print(f"  总请求: {cache_stats['total_requests']}")
        print(f"  缓存命中: {cache_stats['cache_hits']}")
        print(f"  命中率: {cache_stats['hit_rate']}")
        
        print(f"\n💡 提示:")
        print(f"  - 客户列表会自动缓存 10 分钟")
        print(f"  - 第二次查询会从缓存返回，速度提升 99%+")
        print(f"  - 可以通过 use_cache=False 强制刷新")
        
    except Exception as e:
        print(f"\n❌ 获取客户列表失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(get_real_customer_list())

