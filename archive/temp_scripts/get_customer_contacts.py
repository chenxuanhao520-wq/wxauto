#!/usr/bin/env python3
"""
通过 ERP 接口获取 K-0239 客户的联系人信息
"""

import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent))


async def get_customer_contacts():
    """获取 K-0239 客户的联系人信息"""
    print("\n" + "=" * 70)
    print("🔍 获取 K-0239 客户的联系人信息")
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
        
        # 步骤 1: 搜索 K-0239 客户
        print(f"\n📝 步骤 1: 搜索 K-0239 客户...")
        
        # 先获取客户列表，查找 K-0239
        customers_result = await erp.call("erp_customer_list",
                                        page=1,
                                        page_size=100,  # 获取更多客户以便搜索
                                        use_cache=False)
        
        customers = customers_result.get('customers', [])
        print(f"  获取到 {len(customers)} 个客户")
        
        # 查找 K-0239 客户
        target_customer = None
        for customer in customers:
            if customer.get('khid') == 'K-0239' or customer.get('name') == 'K-0239':
                target_customer = customer
                break
        
        if not target_customer:
            print(f"\n❌ 未找到 K-0239 客户")
            print(f"\n📋 可用的客户列表（前10个）:")
            for i, customer in enumerate(customers[:10], 1):
                print(f"  {i}. {customer.get('name', 'N/A')} (ID: {customer.get('khid', 'N/A')})")
            return
        
        print(f"\n✅ 找到目标客户:")
        print(f"  客户名称: {target_customer.get('name', 'N/A')}")
        print(f"  客户编号: {target_customer.get('khid', 'N/A')}")
        print(f"  客户ID: {target_customer.get('ord', 'N/A')}")
        print(f"  销售人员: {target_customer.get('catename', 'N/A')}")
        print(f"  客户分类: {target_customer.get('sortname', 'N/A')}")
        
        # 步骤 2: 获取客户详情（包含联系人信息）
        print(f"\n📝 步骤 2: 获取客户详情和联系人信息...")
        
        customer_id = target_customer.get('ord')
        if customer_id:
            # 查询客户详情
            customer_detail = await erp.call("erp_customer_query",
                                            customer_code=str(customer_id),
                                            use_cache=False)
            
            print(f"\n📊 客户详情查询结果:")
            print(f"  成功: {customer_detail.get('success')}")
            
            if customer_detail.get('success'):
                detail = customer_detail.get('customer', {})
                print(f"\n📋 客户详细信息:")
                for key, value in detail.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  错误: {customer_detail.get('message')}")
        
        # 步骤 3: 尝试通过联系人 API 获取联系人信息
        print(f"\n📝 步骤 3: 尝试获取联系人列表...")
        
        # 这里我们需要实现联系人查询功能
        # 基于智邦 ERP 的 API 结构，联系人通常在客户详情中
        # 或者有单独的联系人管理接口
        
        # 显示客户基本信息中的联系人信息
        print(f"\n📋 客户联系人信息:")
        print(f"  联系人姓名: {target_customer.get('personname', 'N/A')}")
        print(f"  联系人职务: {target_customer.get('personjob', 'N/A')}")
        print(f"  办公电话: {target_customer.get('phone', 'N/A')}")
        print(f"  手机号码: {target_customer.get('mobile', 'N/A')}")
        print(f"  洽谈进展: {target_customer.get('telintro', 'N/A')}")
        
        # 显示缓存统计
        print(f"\n📊 缓存统计:")
        stats = manager.get_stats()
        cache_stats = stats['cache_stats']
        print(f"  总请求: {cache_stats['total_requests']}")
        print(f"  缓存命中: {cache_stats['cache_hits']}")
        print(f"  命中率: {cache_stats['hit_rate']}")
        
        print(f"\n💡 提示:")
        print(f"  - 联系人信息已从客户列表中获取")
        print(f"  - 如需更详细的联系人信息，可能需要调用专门的联系人 API")
        print(f"  - 可以通过客户ID进一步查询更多详情")
        
    except Exception as e:
        print(f"\n❌ 获取客户联系人信息失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(get_customer_contacts())

