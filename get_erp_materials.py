#!/usr/bin/env python3
"""
ERP物料表格获取和分析工具
基于智邦国际ERP产品管理接口获取物料数据并进行深度分析
"""

import json
import requests
import csv
import time
import os
from datetime import datetime
from typing import List, Dict, Any
# import pandas as pd  # 暂时不使用pandas


class ERPMaterialAnalyzer:
    """ERP物料数据分析器"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session_token = None
        self.session = requests.Session()
        
    def login(self) -> bool:
        """登录ERP系统获取session token"""
        try:
            url = f"{self.base_url}/webapi/v3/ov1/login"
            datas = [
                {"id": "user", "val": f"txt:{self.username}"},
                {"id": "password", "val": f"txt:{self.password}"},
                {"id": "serialnum", "val": "txt:mcp_erp_client_001"}
            ]
            
            json_data = {
                "session": "",
                "cmdkey": "login",
                "datas": datas
            }
            
            print(f"🔐 正在登录ERP系统...")
            response = self.session.post(url, json=json_data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            print(f"📋 登录响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if result.get('header', {}).get('status') == 0:
                cookies = self.session.cookies.get_dict()
                print(f"🍪 获取到的Cookies: {cookies}")
                
                if 'ZBCCSN' in cookies or 'ASP.NET_SessionId' in cookies:
                    self.session_token = "cookie_session"
                    print(f"✅ 登录成功，使用Cookie Session")
                    return True
                else:
                    print("❌ 登录失败：未获取到有效的session信息")
                    return False
            else:
                print(f"❌ 登录失败: {result.get('header', {}).get('message', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            return False
    
    def get_products_page(self, page: int = 1, page_size: int = 50) -> List[Dict[str, Any]]:
        """获取单页产品数据"""
        if not self.session_token:
            print("❌ 未登录，请先调用login()")
            return []
        
        try:
            url = f"{self.base_url}/sysa/mobilephone/salesmanage/product/billlist.asp"
            
            # 构建请求参数（基于您提供的代码格式）
            dats = {
                "listadd": "",                    # 列表模式
                "company": "",                    # 客户ID
                "specialCompany": "",            # 供应商ID
                "companyFromType": "",           # 客户类型ID
                "htcateid": "",                  # 销售人员ID
                "IsTools": "",                   # 是否用具选择页面
                "bz": "",                        # 销售人员ID
                "repairOrder": "",               # 维修单ID
                "secpro": "",                    # 是否选择产品
                "fromtype": "",                  # 单据类型
                "totalNum": "",                  # 已加购总数量
                "totalCount": "",                # 已加购总个数
                "flag": "",                      # 单据标记
                "remind": "",                    # 提醒类型
                "ords": "",                      # 产品ord
                "idProductClass": "",            # 产品分类ID
                "cpname": "",                    # 产品名称
                "cpbh": "",                      # 产品编号
                "cpxh": "",                      # 产品型号
                "txm": "",                       # 条形码
                "cateid": "",                    # 人员选择
                "adddate_0": "",                 # 添加日期
                "adddate_1": "",                 # 添加日期
                "searchKey": "",                 # 快速检索条件
                "pagesize": str(page_size),      # 每页记录数
                "pageindex": str(page),         # 数据页标
                "_rpt_sort": ""                  # 排序字段
            }
            
            # 转换为接口要求的格式
            datas = [{"id": key, "val": value} for key, value in dats.items()]
            
            json_data = {
                "session": "",  # 使用Cookie session，这里留空
                "cmdkey": "refresh",
                "datas": datas
            }
            
            print(f"📦 正在获取第{page}页产品数据 (每页{page_size}条)...")
            response = self.session.post(url, json=json_data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # 检查响应状态
            if result.get('header', {}).get('status') == 0:
                body = result.get('body', {})
                source = body.get('source', {})
                table = source.get('table', {})
                rows_data = table.get('rows', [])
                cols = table.get('cols', [])
                
                if not rows_data:
                    print(f"⚠️  第{page}页无数据")
                    return []
                
                # 解析产品数据
                products = []
                for row in rows_data:
                    product = {}
                    for i, col in enumerate(cols):
                        if i < len(row):
                            product[col['id']] = row[i]
                    products.append(product)
                
                print(f"✅ 第{page}页获取到 {len(products)} 个产品")
                return products
            else:
                print(f"❌ 获取产品数据失败: {result.get('header', {}).get('message', '未知错误')}")
                return []
                
        except Exception as e:
            print(f"❌ 获取产品数据异常: {e}")
            return []
    
    def get_all_products(self, page_size: int = 50) -> List[Dict[str, Any]]:
        """获取全量产品数据"""
        all_products = []
        page = 1
        
        print(f"🚀 开始获取全量产品数据 (每页{page_size}条)...")
        
        while True:
            products = self.get_products_page(page, page_size)
            
            if not products:
                print(f"📊 已获取完所有数据，共 {len(all_products)} 个产品")
                break
            
            all_products.extend(products)
            page += 1
            
            # 避免请求过于频繁
            time.sleep(0.5)
        
        return all_products
    
    def get_inventory_data(self) -> List[Dict[str, Any]]:
        """获取库存数据"""
        try:
            url = f"{self.base_url}/webapi/v3/store/inventory/InventorySummary"
            
            # 构建库存查询参数
            params = {
                "page_size": 100,
                "page_index": 1
            }
            
            print(f"📦 正在获取库存数据...")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('Code') == 200:
                rows = result.get('Rows', [])
                print(f"✅ 获取到 {len(rows)} 条库存数据")
                return rows
            else:
                print(f"❌ 获取库存数据失败: {result.get('Msg', '未知错误')}")
                return []
                
        except Exception as e:
            print(f"❌ 获取库存数据异常: {e}")
            return []
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """保存数据到CSV文件"""
        if not data:
            print("❌ 无数据可保存")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"erp_materials_{timestamp}.csv"
        
        # 获取所有字段名
        all_fields = set()
        for item in data:
            all_fields.update(item.keys())
        
        all_fields = sorted(list(all_fields))
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_fields)
            writer.writeheader()
            writer.writerows(data)
        
        print(f"💾 数据已保存到: {filename}")
        print(f"📊 共保存 {len(data)} 条记录，{len(all_fields)} 个字段")
        
        return filename
    
    def analyze_materials(self, products: List[Dict[str, Any]], inventory: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """分析物料数据"""
        if not products:
            return {"error": "无产品数据"}
        
        analysis = {
            "basic_stats": {
                "total_products": len(products),
                "fields_count": len(products[0].keys()) if products else 0,
                "field_names": list(products[0].keys()) if products else []
            },
            "field_statistics": {},
            "category_analysis": {},
            "inventory_analysis": {}
        }
        
        # 统计字段完整性
        field_stats = {}
        for product in products:
            for field, value in product.items():
                if field not in field_stats:
                    field_stats[field] = {"total": 0, "non_empty": 0}
                field_stats[field]["total"] += 1
                if value and str(value).strip():
                    field_stats[field]["non_empty"] += 1
        
        analysis["field_statistics"] = field_stats
        
        # 产品分类分析
        if 'cpfl' in products[0]:  # 产品分类字段
            category_stats = {}
            for product in products:
                category = product.get('cpfl', '未分类')
                if category not in category_stats:
                    category_stats[category] = 0
                category_stats[category] += 1
            analysis["category_analysis"] = category_stats
        
        # 库存分析
        if inventory:
            analysis["inventory_analysis"] = {
                "total_inventory_items": len(inventory),
                "inventory_fields": list(inventory[0].keys()) if inventory else []
            }
        
        return analysis
    
    def generate_material_report(self, analysis: Dict[str, Any]) -> str:
        """生成物料分析报告"""
        report = []
        report.append("=" * 80)
        report.append("📊 ERP物料数据分析报告")
        report.append("=" * 80)
        report.append(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 基础统计
        basic_stats = analysis.get("basic_stats", {})
        report.append("📈 基础统计信息:")
        report.append(f"  • 产品总数: {basic_stats.get('total_products', 0)}")
        report.append(f"  • 字段数量: {basic_stats.get('fields_count', 0)}")
        report.append(f"  • 字段列表: {', '.join(basic_stats.get('field_names', [])[:10])}{'...' if len(basic_stats.get('field_names', [])) > 10 else ''}")
        report.append("")
        
        # 字段完整性统计
        field_stats = analysis.get("field_statistics", {})
        report.append("📋 字段完整性统计:")
        for field, stats in field_stats.items():
            completeness = (stats['non_empty'] / stats['total']) * 100 if stats['total'] > 0 else 0
            report.append(f"  • {field}: {stats['non_empty']}/{stats['total']} ({completeness:.1f}%)")
        report.append("")
        
        # 分类分析
        category_analysis = analysis.get("category_analysis", {})
        if category_analysis:
            report.append("🏷️  产品分类分析:")
            for category, count in sorted(category_analysis.items(), key=lambda x: x[1], reverse=True):
                report.append(f"  • {category}: {count} 个产品")
            report.append("")
        
        # 库存分析
        inventory_analysis = analysis.get("inventory_analysis", {})
        if inventory_analysis:
            report.append("📦 库存分析:")
            report.append(f"  • 库存项目数: {inventory_analysis.get('total_inventory_items', 0)}")
            report.append(f"  • 库存字段: {', '.join(inventory_analysis.get('inventory_fields', [])[:10])}{'...' if len(inventory_analysis.get('inventory_fields', [])) > 10 else ''}")
            report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """主函数"""
    # 从环境变量获取ERP配置
    base_url = os.getenv("ERP_BASE_URL", "http://ls1.jmt.ink:46088")
    username = os.getenv("ERP_USERNAME", "admin")
    password = os.getenv("ERP_PASSWORD", "Abcd@1234")
    
    print("=" * 80)
    print("🏭 ERP物料表格获取和分析工具")
    print("=" * 80)
    print(f"📍 ERP地址: {base_url}")
    print(f"👤 用户名: {username}")
    print(f"🔑 密码: {'*' * len(password)}")
    print("=" * 80)
    
    # 创建分析器
    analyzer = ERPMaterialAnalyzer(base_url, username, password)
    
    # 登录
    if not analyzer.login():
        print("❌ 登录失败，程序退出")
        return
    
    # 获取全量产品数据
    print("\n📦 开始获取产品数据...")
    products = analyzer.get_all_products(page_size=50)
    
    if not products:
        print("❌ 未获取到任何产品数据")
        return
    
    # 获取库存数据
    print("\n📦 开始获取库存数据...")
    inventory = analyzer.get_inventory_data()
    
    # 保存数据
    products_file = analyzer.save_to_csv(products, "erp_products.csv")
    if inventory:
        inventory_file = analyzer.save_to_csv(inventory, "erp_inventory.csv")
    
    # 分析数据
    print("\n" + "=" * 80)
    print("📊 开始数据分析...")
    print("=" * 80)
    
    analysis = analyzer.analyze_materials(products, inventory)
    
    # 生成报告
    report = analyzer.generate_material_report(analysis)
    print(report)
    
    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"erp_material_analysis_report_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 分析完成！")
    print(f"📄 产品数据文件: {products_file}")
    if inventory:
        print(f"📄 库存数据文件: inventory_file")
    print(f"📄 分析报告文件: {report_file}")


if __name__ == "__main__":
    main()
