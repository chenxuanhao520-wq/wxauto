#!/usr/bin/env python3
"""
搜索 K-0239 客户并获取联系人信息
"""

import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent))


async def search_customer_k0239():
    """搜索 K-0239 客户"""
    print("\n" + "=" * 70)
    print("🔍 搜索 K-0239 客户并获取联系人信息")
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
        
        # 步骤 1: 获取所有客户列表
        print(f"\n📝 步骤 1: 获取所有客户列表...")
        
        all_customers = []
        page = 1
        page_size = 20
        
        while True:
            print(f"  正在获取第 {page} 页客户...")
            
            customers_result = await erp.call("erp_customer_list",
                                            page=page,
                                            page_size=page_size,
                                            use_cache=False)
            
            customers = customers_result.get('customers', [])
            if not customers:
                break
                
            all_customers.extend(customers)
            print(f"    获取到 {len(customers)} 个客户")
            
            # 如果这一页的客户数少于页面大小，说明已经是最后一页
            if len(customers) < page_size:
                break
                
            page += 1
            
            # 防止无限循环，最多获取10页
            if page > 10:
                break
        
        print(f"\n📊 总共获取到 {len(all_customers)} 个客户")
        
        # 步骤 2: 搜索 K-0239 客户
        print(f"\n📝 步骤 2: 搜索 K-0239 客户...")
        
        target_customer = None
        search_patterns = ['K-0239', 'K0239', 'K_0239', '0239']
        
        for customer in all_customers:
            # 检查所有可能的字段
            customer_info = {
                'name': customer.get('name', ''),
                'khid': customer.get('khid', ''),
                'ord': customer.get('ord', ''),
                'personname': customer.get('personname', ''),
                'phone': customer.get('phone', ''),
                'mobile': customer.get('mobile', '')
            }
            
            # 检查是否匹配搜索模式
            for pattern in search_patterns:
                for key, value in customer_info.items():
                    if pattern in str(value):
                        target_customer = customer
                        print(f"  ✅ 找到匹配客户: {pattern} 在 {key} 字段中")
                        break
                if target_customer:
                    break
            if target_customer:
                break
        
        if not target_customer:
            print(f"\n❌ 未找到 K-0239 客户")
            print(f"\n📋 显示所有客户的详细信息（前20个）:")
            for i, customer in enumerate(all_customers[:20], 1):
                print(f"\n客户 {i}:")
                for key, value in customer.items():
                    print(f"  {key}: {value}")
            return
        
        # 步骤 3: 显示 K-0239 客户的详细信息
        print(f"\n✅ 找到 K-0239 客户:")
        print("=" * 70)
        
        print(f"\n📋 客户基本信息:")
        for key, value in target_customer.items():
            print(f"  {key}: {value}")
        
        # 步骤 4: 提取联系人信息
        print(f"\n📋 联系人信息:")
        print("=" * 50)
        
        contact_info = {
            "联系人姓名": target_customer.get('personname', 'N/A'),
            "联系人职务": target_customer.get('personjob', 'N/A'),
            "办公电话": target_customer.get('phone', 'N/A'),
            "手机号码": target_customer.get('mobile', 'N/A'),
            "传真": target_customer.get('fax', 'N/A'),
            "邮箱": target_customer.get('email', 'N/A'),
            "微信": target_customer.get('weixin', 'N/A'),
            "QQ": target_customer.get('qq', 'N/A'),
            "部门": target_customer.get('part1', 'N/A'),
            "备注": target_customer.get('intro', 'N/A'),
            "洽谈进展": target_customer.get('telintro', 'N/A')
        }
        
        for key, value in contact_info.items():
            if value != 'N/A' and value:
                print(f"  {key}: {value}")
        
        # 步骤 5: 显示客户其他信息
        print(f"\n📋 客户其他信息:")
        print("=" * 50)
        
        customer_other_info = {
            "客户名称": target_customer.get('name', 'N/A'),
            "客户编号": target_customer.get('khid', 'N/A'),
            "客户ID": target_customer.get('ord', 'N/A'),
            "销售人员": target_customer.get('catename', 'N/A'),
            "客户分类": target_customer.get('sortname', 'N/A'),
            "客户状态": target_customer.get('sort1name', 'N/A'),
            "客户地址": target_customer.get('address', 'N/A'),
            "客户网址": target_customer.get('url', 'N/A')
        }
        
        for key, value in customer_other_info.items():
            if value != 'N/A' and value:
                print(f"  {key}: {value}")
        
        # 显示缓存统计
        print(f"\n📊 缓存统计:")
        stats = manager.get_stats()
        cache_stats = stats['cache_stats']
        print(f"  总请求: {cache_stats['total_requests']}")
        print(f"  缓存命中: {cache_stats['cache_hits']}")
        print(f"  命中率: {cache_stats['hit_rate']}")
        
        print(f"\n💡 提示:")
        print(f"  - 已成功获取 K-0239 客户的完整信息")
        print(f"  - 联系人信息已从客户记录中提取")
        print(f"  - 如需更多联系人，可能需要查看客户详情页面")
        
    except Exception as e:
        print(f"\n❌ 搜索客户失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(search_customer_k0239())

