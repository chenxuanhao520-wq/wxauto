#!/usr/bin/env python3
"""
详细搜索 K-0239 客户，检查所有字段
"""

import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent))


async def search_k0239_detailed():
    """详细搜索 K-0239 客户"""
    print("\n" + "=" * 70)
    print("🔍 详细搜索 K-0239 客户（检查所有字段）")
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
        
        # 步骤 1: 获取客户列表
        print(f"\n📝 步骤 1: 获取客户列表...")
        
        customers_result = await erp.call("erp_customer_list",
                                        page=1,
                                        page_size=50,  # 先获取50个客户
                                        use_cache=False)
        
        customers = customers_result.get('customers', [])
        print(f"  获取到 {len(customers)} 个客户")
        
        # 步骤 2: 详细检查每个客户的所有字段
        print(f"\n📝 步骤 2: 详细检查客户字段...")
        
        target_customer = None
        search_patterns = ['K-0239', 'K0239', 'K_0239', '0239']
        
        for i, customer in enumerate(customers, 1):
            print(f"\n检查客户 {i}: {customer.get('name', 'N/A')}")
            
            # 检查所有字段是否包含搜索模式
            found_match = False
            for pattern in search_patterns:
                for key, value in customer.items():
                    if value and pattern in str(value):
                        print(f"  ✅ 找到匹配: '{pattern}' 在字段 '{key}' 中，值为: '{value}'")
                        target_customer = customer
                        found_match = True
                        break
                if found_match:
                    break
            
            # 显示客户的所有字段（用于调试）
            if i <= 5:  # 只显示前5个客户的详细信息
                print(f"  所有字段:")
                for key, value in customer.items():
                    print(f"    {key}: {value}")
        
        if not target_customer:
            print(f"\n❌ 在前 {len(customers)} 个客户中未找到 K-0239")
            
            # 显示所有客户的客户编号字段
            print(f"\n📋 所有客户的客户编号字段:")
            for i, customer in enumerate(customers, 1):
                khid = customer.get('khid', '')
                name = customer.get('name', '')
                print(f"  {i}. {name} - 客户编号: '{khid}'")
            
            # 尝试获取更多客户
            print(f"\n📝 尝试获取更多客户...")
            for page in range(2, 6):  # 获取第2-5页
                print(f"  获取第 {page} 页客户...")
                
                more_customers_result = await erp.call("erp_customer_list",
                                                     page=page,
                                                     page_size=20,
                                                     use_cache=False)
                
                more_customers = more_customers_result.get('customers', [])
                if not more_customers:
                    break
                
                print(f"    获取到 {len(more_customers)} 个客户")
                
                # 检查这一页的客户
                for customer in more_customers:
                    for pattern in search_patterns:
                        for key, value in customer.items():
                            if value and pattern in str(value):
                                print(f"  ✅ 找到匹配: '{pattern}' 在字段 '{key}' 中，值为: '{value}'")
                                target_customer = customer
                                break
                        if target_customer:
                            break
                    if target_customer:
                        break
                if target_customer:
                    break
                
                # 显示这一页的客户编号
                for customer in more_customers:
                    khid = customer.get('khid', '')
                    name = customer.get('name', '')
                    if khid:  # 只显示有客户编号的
                        print(f"    {name} - 客户编号: '{khid}'")
        
        if target_customer:
            print(f"\n🎉 找到 K-0239 客户!")
            print("=" * 70)
            
            print(f"\n📋 客户完整信息:")
            for key, value in target_customer.items():
                print(f"  {key}: {value}")
            
            # 提取联系人信息
            print(f"\n📞 联系人信息:")
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
        else:
            print(f"\n❌ 在所有搜索的客户中未找到 K-0239")
            print(f"\n💡 建议:")
            print(f"  1. 确认 K-0239 是否是实际的客户编号")
            print(f"  2. 检查客户是否已被删除或归档")
            print(f"  3. 尝试使用其他搜索条件")
        
    except Exception as e:
        print(f"\n❌ 搜索失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(search_k0239_detailed())

