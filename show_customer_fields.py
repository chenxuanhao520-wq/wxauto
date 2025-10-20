#!/usr/bin/env python3
"""
显示客户列表的所有字段信息
"""

import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent))


async def show_customer_fields():
    """显示客户列表的所有字段"""
    print("\n" + "=" * 70)
    print("🔍 客户列表字段信息分析")
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
        
        # 获取客户列表
        print(f"\n📝 获取客户列表...")
        
        customers_result = await erp.call("erp_customer_list",
                                        page=1,
                                        page_size=10,  # 只获取10个客户用于分析
                                        use_cache=False)
        
        customers = customers_result.get('customers', [])
        print(f"  获取到 {len(customers)} 个客户")
        
        if not customers:
            print(f"❌ 没有获取到客户数据")
            return
        
        # 分析第一个客户的所有字段
        first_customer = customers[0]
        print(f"\n📊 客户字段分析（以第一个客户为例）:")
        print("=" * 70)
        
        print(f"\n客户名称: {first_customer.get('name', 'N/A')}")
        print(f"\n所有字段及其值:")
        print("-" * 50)
        
        all_fields = {}
        for key, value in first_customer.items():
            all_fields[key] = value
            print(f"  {key}: {value}")
        
        # 统计字段信息
        print(f"\n📈 字段统计:")
        print("-" * 50)
        print(f"  总字段数: {len(all_fields)}")
        
        # 分析字段类型
        text_fields = []
        number_fields = []
        empty_fields = []
        url_fields = []
        
        for key, value in all_fields.items():
            if isinstance(value, str):
                if value == '':
                    empty_fields.append(key)
                elif value == '_url':
                    url_fields.append(key)
                else:
                    text_fields.append(key)
            elif isinstance(value, (int, float)):
                number_fields.append(key)
        
        print(f"\n📋 字段分类:")
        print(f"  文本字段 ({len(text_fields)}): {', '.join(text_fields)}")
        print(f"  数字字段 ({len(number_fields)}): {', '.join(number_fields)}")
        print(f"  空字段 ({len(empty_fields)}): {', '.join(empty_fields)}")
        print(f"  URL字段 ({len(url_fields)}): {', '.join(url_fields)}")
        
        # 分析所有客户的字段一致性
        print(f"\n📊 字段一致性分析:")
        print("-" * 50)
        
        all_customer_fields = set()
        for customer in customers:
            all_customer_fields.update(customer.keys())
        
        print(f"  所有客户共有的字段数: {len(all_customer_fields)}")
        print(f"  字段列表: {', '.join(sorted(all_customer_fields))}")
        
        # 检查每个字段在所有客户中的情况
        print(f"\n📋 字段使用情况:")
        print("-" * 50)
        
        for field in sorted(all_customer_fields):
            non_empty_count = 0
            values = []
            
            for customer in customers:
                value = customer.get(field, '')
                if value and value != '':
                    non_empty_count += 1
                    if len(values) < 3:  # 只收集前3个非空值作为示例
                        values.append(str(value))
            
            usage_rate = (non_empty_count / len(customers)) * 100
            print(f"  {field}: {non_empty_count}/{len(customers)} ({usage_rate:.1f}%) - 示例值: {', '.join(values)}")
        
        # 特别关注客户编号字段
        print(f"\n🔍 客户编号字段分析:")
        print("-" * 50)
        
        khid_values = []
        for customer in customers:
            khid = customer.get('khid', '')
            khid_values.append(khid)
        
        non_empty_khid = [k for k in khid_values if k and k != '']
        print(f"  客户编号字段 (khid):")
        print(f"    总客户数: {len(customers)}")
        print(f"    有客户编号的客户数: {len(non_empty_khid)}")
        print(f"    客户编号使用率: {(len(non_empty_khid)/len(customers))*100:.1f}%")
        
        if non_empty_khid:
            print(f"    客户编号示例: {', '.join(non_empty_khid[:5])}")
        else:
            print(f"    ⚠️  所有客户的客户编号字段都为空")
        
        # 显示完整的字段映射表
        print(f"\n📋 完整字段映射表:")
        print("=" * 70)
        
        field_descriptions = {
            'name': '客户名称',
            'catename': '销售人员',
            'sortname': '客户分类',
            'sort1name': '客户状态',
            'personname': '联系人姓名',
            'personjob': '联系人职务',
            'phone': '办公电话',
            'mobile': '手机号码',
            'fax': '传真',
            'email': '邮箱',
            'weixin': '微信',
            'qq': 'QQ',
            'part1': '部门',
            'intro': '备注',
            'telintro': '洽谈进展',
            'ord': '客户ID（数字）',
            'person': '联系人ID',
            'khid': '客户编号',
            'url': '客户详情URL',
            'personurl': '联系人详情URL'
        }
        
        for field in sorted(all_customer_fields):
            description = field_descriptions.get(field, '未知字段')
            print(f"  {field}: {description}")
        
        print(f"\n💡 总结:")
        print(f"  - 客户列表包含 {len(all_customer_fields)} 个字段")
        print(f"  - 客户编号字段 (khid) 在所有客户中都为空")
        print(f"  - 主要标识字段是客户ID (ord) 和客户名称 (name)")
        print(f"  - 联系人信息包含在客户记录中")
        
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(show_customer_fields())

