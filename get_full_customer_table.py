#!/usr/bin/env python3
"""
获取全量客户列表并整理成表格
"""

import asyncio
import sys
import os
import json
import csv
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))


async def get_full_customer_table():
    """获取全量客户列表并整理成表格"""
    print("\n" + "=" * 70)
    print("🔍 获取全量客户列表并整理成表格")
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
        
        # 获取全量客户数据
        print(f"\n📝 获取全量客户数据...")
        
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
                print(f"    第 {page} 页没有数据，停止获取")
                break
                
            all_customers.extend(customers)
            print(f"    获取到 {len(customers)} 个客户")
            
            # 如果这一页的客户数少于页面大小，说明已经是最后一页
            if len(customers) < page_size:
                print(f"    第 {page} 页客户数少于 {page_size}，已到最后一页")
                break
                
            page += 1
            
            # 防止无限循环，最多获取50页
            if page > 50:
                print(f"    已达到最大页数限制 (50页)")
                break
        
        print(f"\n📊 总共获取到 {len(all_customers)} 个客户")
        
        if not all_customers:
            print(f"❌ 没有获取到客户数据")
            return
        
        # 整理客户数据
        print(f"\n📝 整理客户数据...")
        
        # 定义表格列
        table_columns = [
            '序号', '客户ID', '客户名称', '销售人员', '客户分类', '客户状态',
            '联系人姓名', '联系人职务', '办公电话', '手机号码', '传真',
            '邮箱', '微信', 'QQ', '部门', '备注', '洽谈进展',
            '客户地址', '客户网址', '联系人ID', '客户详情URL', '联系人详情URL'
        ]
        
        # 准备表格数据
        table_data = []
        for i, customer in enumerate(all_customers, 1):
            row = [
                i,  # 序号
                customer.get('ord', ''),  # 客户ID
                customer.get('name', ''),  # 客户名称
                customer.get('catename', ''),  # 销售人员
                customer.get('sortname', ''),  # 客户分类
                customer.get('sort1name', ''),  # 客户状态
                customer.get('personname', ''),  # 联系人姓名
                customer.get('personjob', ''),  # 联系人职务
                customer.get('phone', ''),  # 办公电话
                customer.get('mobile', ''),  # 手机号码
                customer.get('fax', ''),  # 传真
                customer.get('email', ''),  # 邮箱
                customer.get('weixin', ''),  # 微信
                customer.get('qq', ''),  # QQ
                customer.get('part1', ''),  # 部门
                customer.get('intro', ''),  # 备注
                customer.get('telintro', ''),  # 洽谈进展
                customer.get('address', ''),  # 客户地址
                customer.get('url', ''),  # 客户网址
                customer.get('person', ''),  # 联系人ID
                customer.get('url', ''),  # 客户详情URL
                customer.get('personurl', '')  # 联系人详情URL
            ]
            table_data.append(row)
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存为CSV文件
        csv_filename = f"客户列表_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(table_columns)
            writer.writerows(table_data)
        
        print(f"✅ CSV文件已保存: {csv_filename}")
        
        # 保存为JSON文件
        json_filename = f"客户列表_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(all_customers, jsonfile, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON文件已保存: {json_filename}")
        
        # 显示表格预览
        print(f"\n📋 客户列表预览 (前20个客户):")
        print("=" * 120)
        
        # 打印表头
        header = f"{'序号':<4} {'客户ID':<6} {'客户名称':<25} {'销售人员':<12} {'客户分类':<10} {'客户状态':<12} {'联系人':<15} {'手机号':<15}"
        print(header)
        print("-" * 120)
        
        # 打印前20行数据
        for i, customer in enumerate(all_customers[:20], 1):
            row = f"{i:<4} {customer.get('ord', ''):<6} {customer.get('name', '')[:24]:<25} {customer.get('catename', '')[:11]:<12} {customer.get('sortname', '')[:9]:<10} {customer.get('sort1name', '')[:11]:<12} {customer.get('personname', '')[:14]:<15} {customer.get('mobile', '')[:14]:<15}"
            print(row)
        
        if len(all_customers) > 20:
            print(f"... 还有 {len(all_customers) - 20} 个客户")
        
        # 统计信息
        print(f"\n📊 统计信息:")
        print("=" * 50)
        
        # 按客户分类统计
        sortname_stats = {}
        for customer in all_customers:
            sortname = customer.get('sortname', '未知')
            sortname_stats[sortname] = sortname_stats.get(sortname, 0) + 1
        
        print(f"  按客户分类统计:")
        for sortname, count in sorted(sortname_stats.items()):
            print(f"    {sortname}: {count} 个客户")
        
        # 按客户状态统计
        sort1name_stats = {}
        for customer in all_customers:
            sort1name = customer.get('sort1name', '未知')
            sort1name_stats[sort1name] = sort1name_stats.get(sort1name, 0) + 1
        
        print(f"\n  按客户状态统计:")
        for sort1name, count in sorted(sort1name_stats.items()):
            print(f"    {sort1name}: {count} 个客户")
        
        # 按销售人员统计
        catename_stats = {}
        for customer in all_customers:
            catename = customer.get('catename', '未知')
            catename_stats[catename] = catename_stats.get(catename, 0) + 1
        
        print(f"\n  按销售人员统计:")
        for catename, count in sorted(catename_stats.items()):
            print(f"    {catename}: {count} 个客户")
        
        # 有联系方式的客户统计
        with_phone = len([c for c in all_customers if c.get('phone')])
        with_mobile = len([c for c in all_customers if c.get('mobile')])
        with_contact = len([c for c in all_customers if c.get('personname')])
        
        print(f"\n  联系方式统计:")
        print(f"    有办公电话: {with_phone} 个客户")
        print(f"    有手机号码: {with_mobile} 个客户")
        print(f"    有联系人: {with_contact} 个客户")
        
        print(f"\n💡 文件说明:")
        print(f"  - CSV文件: 可用Excel打开，包含所有客户信息")
        print(f"  - JSON文件: 包含完整的原始数据")
        print(f"  - 文件位置: 当前目录")
        
    except Exception as e:
        print(f"\n❌ 获取客户列表失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(get_full_customer_table())

