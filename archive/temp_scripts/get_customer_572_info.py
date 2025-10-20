#!/usr/bin/env python3
"""
查询客户ID 572的详细信息和订单情况
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))


async def get_customer_572_info():
    """查询客户ID 572的详细信息和订单情况"""
    print("\n" + "=" * 70)
    print("🔍 查询客户ID 572的详细信息和订单情况")
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
        
        # 第一步：从客户列表中查找客户ID 572
        print(f"\n📝 步骤1: 查找客户ID 572的信息...")
        
        customer_found = None
        page = 1
        
        while True:
            customers_result = await erp.call("erp_customer_list",
                                            page=page,
                                            page_size=20,
                                            use_cache=False)
            
            customers = customers_result.get('customers', [])
            if not customers:
                break
            
            # 查找客户ID 572
            for customer in customers:
                if customer.get('ord') == '572':
                    customer_found = customer
                    break
            
            if customer_found:
                break
                
            page += 1
            if page > 50:  # 防止无限循环
                break
        
        if not customer_found:
            print(f"❌ 未找到客户ID 572")
            return
        
        print(f"✅ 找到客户ID 572")
        
        # 显示客户详细信息
        print(f"\n📋 客户详细信息:")
        print("=" * 70)
        print(f"  客户ID: {customer_found.get('ord', 'N/A')}")
        print(f"  客户名称: {customer_found.get('name', 'N/A')}")
        print(f"  客户分类: {customer_found.get('sortname', 'N/A')}")
        print(f"  客户状态: {customer_found.get('sort1name', 'N/A')}")
        print(f"  销售人员: {customer_found.get('catename', 'N/A')}")
        print(f"\n  联系人信息:")
        print(f"    姓名: {customer_found.get('personname', 'N/A')}")
        print(f"    职务: {customer_found.get('personjob', 'N/A')}")
        print(f"    办公电话: {customer_found.get('phone', 'N/A')}")
        print(f"    手机号码: {customer_found.get('mobile', 'N/A')}")
        print(f"    传真: {customer_found.get('fax', 'N/A')}")
        print(f"    邮箱: {customer_found.get('email', 'N/A')}")
        print(f"    微信: {customer_found.get('weixin', 'N/A')}")
        print(f"    QQ: {customer_found.get('qq', 'N/A')}")
        print(f"\n  其他信息:")
        print(f"    客户地址: {customer_found.get('address', 'N/A')}")
        print(f"    客户网址: {customer_found.get('url', 'N/A')}")
        print(f"    洽谈进展: {customer_found.get('telintro', 'N/A')}")
        print(f"    备注: {customer_found.get('intro', 'N/A')}")
        
        # 显示完整的字段信息
        print(f"\n📊 所有字段信息:")
        print("=" * 70)
        for key, value in customer_found.items():
            if value and value != '' and value != '0' and value != '_url':
                print(f"  {key}: {value}")
        
        # 第二步：查询订单信息
        print(f"\n📝 步骤2: 查询客户订单...")
        print("=" * 70)
        
        # 使用客户名称查询订单（因为ERP API可能需要客户名称而不是ID）
        customer_name = customer_found.get('name', '')
        
        try:
            # 尝试通过ERP MCP查询订单
            orders_result = await erp.call("erp_order_query",
                                         customer_id=customer_name,
                                         page=1,
                                         page_size=50,
                                         use_cache=False)
            
            if orders_result.get('success'):
                orders = orders_result.get('orders', [])
                if orders:
                    print(f"✅ 找到 {len(orders)} 个订单")
                    print(f"\n📋 订单列表:")
                    print("-" * 70)
                    
                    for i, order in enumerate(orders, 1):
                        print(f"\n  订单 {i}:")
                        for key, value in order.items():
                            if value and value != '' and value != '0' and value != '_url':
                                print(f"    {key}: {value}")
                else:
                    print(f"⚠️  该客户暂无订单记录")
            else:
                print(f"⚠️  查询订单失败: {orders_result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"⚠️  查询订单异常: {e}")
            print(f"  提示: 订单API可能暂时不可用")
        
        # 第三步：尝试查询合同信息
        print(f"\n📝 步骤3: 查询客户合同...")
        print("=" * 70)
        
        try:
            # 尝试通过ERP MCP查询合同
            contracts_result = await erp.call("erp_contract_query",
                                            customer_id=customer_name,
                                            page=1,
                                            page_size=50,
                                            use_cache=False)
            
            if contracts_result.get('success'):
                contracts = contracts_result.get('contracts', [])
                if contracts:
                    print(f"✅ 找到 {len(contracts)} 个合同")
                    print(f"\n📋 合同列表:")
                    print("-" * 70)
                    
                    for i, contract in enumerate(contracts, 1):
                        print(f"\n  合同 {i}:")
                        for key, value in contract.items():
                            if value and value != '' and value != '0' and value != '_url':
                                print(f"    {key}: {value}")
                else:
                    print(f"⚠️  该客户暂无合同记录")
            else:
                print(f"⚠️  查询合同失败: {contracts_result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"⚠️  查询合同异常: {e}")
            print(f"  提示: 合同API可能暂时不可用")
        
        # 保存客户信息到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"客户572详细信息_{timestamp}.json"
        
        output_data = {
            "customer_info": customer_found,
            "orders": orders_result if 'orders_result' in locals() else None,
            "contracts": contracts_result if 'contracts_result' in locals() else None,
            "query_time": timestamp
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 详细信息已保存到: {filename}")
        
    except Exception as e:
        print(f"\n❌ 查询失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(get_customer_572_info())

