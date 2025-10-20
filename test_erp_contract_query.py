#!/usr/bin/env python3
"""
测试智邦 ERP 合同查询功能
"""

import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent))


async def test_erp_contract_query():
    """测试 ERP 合同查询功能"""
    print("\n" + "=" * 70)
    print("🔍 智邦 ERP - 测试合同查询功能")
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
        
        # 测试 1: 获取合同列表
        print(f"\n📝 测试 1: 获取合同列表（第 1 页，每页 10 条）...")
        
        result = await erp.call("erp_contract_query",
                               page=1,
                               page_size=10,
                               use_cache=False)
        
        print(f"\n📊 合同列表查询结果:")
        print(f"  成功: {result.get('success')}")
        print(f"  合同总数: {result.get('total', 0)}")
        print(f"  当前页: {result.get('page')}")
        print(f"  每页数量: {result.get('page_size')}")
        
        contracts = result.get('contracts', [])
        
        if contracts:
            print(f"\n📋 合同列表 (共 {len(contracts)} 个):")
            print("=" * 70)
            
            for i, contract in enumerate(contracts, 1):
                print(f"\n合同 {i}:")
                # 打印所有字段
                for key, value in contract.items():
                    print(f"  {key}: {value}")
            
            print("\n" + "=" * 70)
            print(f"✅ 成功获取 {len(contracts)} 个合同")
            
            # 测试 2: 查询特定合同
            if contracts:
                first_contract = contracts[0]
                contract_id = first_contract.get('ord') or first_contract.get('name')
                
                if contract_id:
                    print(f"\n📝 测试 2: 查询特定合同 (ID: {contract_id})...")
                    
                    specific_result = await erp.call("erp_contract_query",
                                                   contract_code=str(contract_id),
                                                   use_cache=False)
                    
                    print(f"\n📊 特定合同查询结果:")
                    print(f"  成功: {specific_result.get('success')}")
                    
                    if specific_result.get('success'):
                        contract_detail = specific_result.get('contract', {})
                        print(f"  合同详情:")
                        for key, value in contract_detail.items():
                            print(f"    {key}: {value}")
                    else:
                        print(f"  错误: {specific_result.get('message')}")
            
        else:
            print(f"\n⚠️  没有获取到合同数据")
            print(f"\n可能的原因:")
            print(f"  1. ERP 系统中确实没有合同数据")
            print(f"  2. 需要特定的查询条件或权限")
            print(f"  3. API 接口路径需要调整")
        
        # 测试 3: 按客户ID查询合同
        print(f"\n📝 测试 3: 按客户ID查询合同...")
        
        # 先获取一个客户ID
        customer_result = await erp.call("erp_customer_list",
                                        page=1,
                                        page_size=1,
                                        use_cache=False)
        
        customers = customer_result.get('customers', [])
        if customers:
            customer_id = customers[0].get('ord')
            print(f"  使用客户ID: {customer_id}")
            
            customer_contracts = await erp.call("erp_contract_query",
                                               customer_id=str(customer_id),
                                               page=1,
                                               page_size=5,
                                               use_cache=False)
            
            print(f"\n📊 客户合同查询结果:")
            print(f"  成功: {customer_contracts.get('success')}")
            print(f"  合同数: {customer_contracts.get('total', 0)}")
            
            customer_contracts_list = customer_contracts.get('contracts', [])
            if customer_contracts_list:
                print(f"\n📋 客户合同列表:")
                for i, contract in enumerate(customer_contracts_list, 1):
                    print(f"  合同 {i}: {contract.get('name', 'N/A')} - {contract.get('ord', 'N/A')}")
            else:
                print(f"  该客户暂无合同")
        
        # 显示缓存统计
        print(f"\n📊 缓存统计:")
        stats = manager.get_stats()
        cache_stats = stats['cache_stats']
        print(f"  总请求: {cache_stats['total_requests']}")
        print(f"  缓存命中: {cache_stats['cache_hits']}")
        print(f"  命中率: {cache_stats['hit_rate']}")
        
        print(f"\n💡 提示:")
        print(f"  - 合同查询支持按合同号、客户ID筛选")
        print(f"  - 支持分页查询")
        print(f"  - 可以根据需要开启/关闭缓存")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_erp_contract_query())
