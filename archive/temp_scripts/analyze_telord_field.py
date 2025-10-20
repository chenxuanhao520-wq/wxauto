#!/usr/bin/env python3
"""
分析 telord 字段（客户ID）的信息
"""

import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent))


async def analyze_telord_field():
    """分析 telord 字段信息"""
    print("\n" + "=" * 70)
    print("🔍 分析 telord 字段（客户ID）信息")
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
        
        # 获取更多客户数据进行分析
        print(f"\n📝 获取客户数据进行分析...")
        
        all_customers = []
        for page in range(1, 6):  # 获取前5页
            print(f"  获取第 {page} 页客户...")
            
            customers_result = await erp.call("erp_customer_list",
                                            page=page,
                                            page_size=20,
                                            use_cache=False)
            
            customers = customers_result.get('customers', [])
            if not customers:
                break
                
            all_customers.extend(customers)
            print(f"    获取到 {len(customers)} 个客户")
        
        print(f"\n📊 总共获取到 {len(all_customers)} 个客户")
        
        # 分析 telord 字段（对应 ord 字段）
        print(f"\n🔍 telord 字段分析:")
        print("=" * 50)
        
        ord_values = []
        for customer in all_customers:
            ord_value = customer.get('ord', '')
            if ord_value:
                ord_values.append(int(ord_value))
        
        if ord_values:
            ord_values.sort()
            
            print(f"  客户ID范围: {min(ord_values)} - {max(ord_values)}")
            print(f"  客户ID总数: {len(ord_values)}")
            print(f"  客户ID示例: {ord_values[:10]}")
            print(f"  客户ID分布:")
            
            # 分析ID分布
            ranges = [
                (1, 100, "1-100"),
                (101, 200, "101-200"),
                (201, 300, "201-300"),
                (301, 400, "301-400"),
                (401, 500, "401-500"),
                (501, 600, "501-600"),
                (601, 700, "601-700"),
                (701, 800, "701-800"),
                (801, 900, "801-900"),
                (901, 1000, "901-1000")
            ]
            
            for min_val, max_val, label in ranges:
                count = len([x for x in ord_values if min_val <= x <= max_val])
                if count > 0:
                    print(f"    {label}: {count} 个客户")
            
            # 查找可能的 K-0239 对应关系
            print(f"\n🔍 查找可能的 K-0239 对应关系:")
            print("-" * 50)
            
            # 尝试不同的映射关系
            possible_mappings = []
            
            # 1. 直接搜索包含 0239 的ID
            for ord_val in ord_values:
                if '0239' in str(ord_val):
                    possible_mappings.append(('包含0239', ord_val))
            
            # 2. 搜索以 239 结尾的ID
            for ord_val in ord_values:
                if str(ord_val).endswith('239'):
                    possible_mappings.append(('以239结尾', ord_val))
            
            # 3. 搜索以 39 结尾的ID
            for ord_val in ord_values:
                if str(ord_val).endswith('39'):
                    possible_mappings.append(('以39结尾', ord_val))
            
            # 4. 搜索包含 23 的ID
            for ord_val in ord_values:
                if '23' in str(ord_val):
                    possible_mappings.append(('包含23', ord_val))
            
            if possible_mappings:
                print(f"  找到可能的映射关系:")
                for pattern, ord_val in possible_mappings:
                    # 找到对应的客户信息
                    customer = next((c for c in all_customers if c.get('ord') == str(ord_val)), None)
                    if customer:
                        print(f"    {pattern}: ID {ord_val} -> {customer.get('name', 'N/A')}")
            else:
                print(f"  未找到明显的 K-0239 映射关系")
            
            # 显示所有客户ID和对应的客户名称
            print(f"\n📋 所有客户ID和名称:")
            print("-" * 50)
            
            for customer in all_customers[:20]:  # 显示前20个
                ord_val = customer.get('ord', '')
                name = customer.get('name', '')
                personname = customer.get('personname', '')
                mobile = customer.get('mobile', '')
                
                print(f"  ID {ord_val}: {name}")
                if personname:
                    print(f"    联系人: {personname}")
                if mobile:
                    print(f"    手机: {mobile}")
                print()
            
            if len(all_customers) > 20:
                print(f"  ... 还有 {len(all_customers) - 20} 个客户")
        
        # 分析字段对应关系
        print(f"\n📊 字段对应关系分析:")
        print("=" * 50)
        
        print(f"  API 文档中的字段 -> 实际返回的字段:")
        print(f"    telord (客户ID) -> ord")
        print(f"    name (客户名称) -> name")
        print(f"    personname (联系人) -> personname")
        print(f"    phone (电话) -> phone")
        print(f"    mobile (手机) -> mobile")
        
        print(f"\n💡 关于 K-0239 的搜索建议:")
        print("-" * 50)
        print(f"  1. K-0239 可能是客户编号，但系统中没有客户编号字段")
        print(f"  2. 客户ID是数字格式，如 574, 572, 561 等")
        print(f"  3. 建议通过以下方式搜索:")
        print(f"     - 客户名称搜索")
        print(f"     - 联系人姓名搜索")
        print(f"     - 电话号码搜索")
        print(f"     - 如果知道对应的数字ID，直接搜索")
        
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(analyze_telord_field())

