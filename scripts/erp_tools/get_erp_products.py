#!/usr/bin/env python3
"""
ERP产品数据获取脚本
基于智邦国际ERP产品管理接口获取全量产品数据
"""

import requests
import json
import csv
import time
from datetime import datetime
from typing import List, Dict, Any
import os


class ERPProductFetcher:
    """ERP产品数据获取器"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session_token = None
        self.session = requests.Session()  # 使用Session保持Cookie
        
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
                # 检查Cookie中是否有session信息
                cookies = self.session.cookies.get_dict()
                print(f"🍪 获取到的Cookies: {cookies}")
                
                # 使用Cookie中的session信息
                if 'ZBCCSN' in cookies or 'ASP.NET_SessionId' in cookies:
                    self.session_token = "cookie_session"  # 标记为使用Cookie session
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
    
    def get_products_page(self, page: int = 1, page_size: int = 100) -> List[Dict[str, Any]]:
        """获取单页产品数据"""
        if not self.session_token:
            print("❌ 未登录，请先调用login()")
            return []
        
        try:
            url = f"{self.base_url}/sysa/mobilephone/salesmanage/product/billlist.asp"
            
            # 构建请求参数（基于文档）
            datas = [
                {"id": "listadd", "val": ""},
                {"id": "company", "val": ""},
                {"id": "specialCompany", "val": ""},
                {"id": "companyFromType", "val": ""},
                {"id": "htcateid", "val": ""},
                {"id": "IsTools", "val": ""},
                {"id": "bz", "val": ""},
                {"id": "repairOrder", "val": ""},
                {"id": "secpro", "val": ""},
                {"id": "fromtype", "val": ""},
                {"id": "totalNum", "val": ""},
                {"id": "totalCount", "val": ""},
                {"id": "flag", "val": ""},
                {"id": "remind", "val": ""},
                {"id": "ords", "val": ""},
                {"id": "idProductClass", "val": ""},
                {"id": "cpname", "val": ""},
                {"id": "cpbh", "val": ""},
                {"id": "cpxh", "val": ""},
                {"id": "txm", "val": ""},
                {"id": "cateid", "val": ""},
                {"id": "adddate_0", "val": ""},
                {"id": "adddate_1", "val": ""},
                {"id": "searchKey", "val": ""},
                {"id": "pagesize", "val": str(page_size)},
                {"id": "pageindex", "val": str(page)},
                {"id": "_rpt_sort", "val": ""}
            ]
            
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
    
    def get_all_products(self, page_size: int = 100) -> List[Dict[str, Any]]:
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
    
    def save_to_csv(self, products: List[Dict[str, Any]], filename: str = None) -> str:
        """保存产品数据到CSV文件"""
        if not products:
            print("❌ 无产品数据可保存")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"erp_products_{timestamp}.csv"
        
        # 获取所有字段名
        all_fields = set()
        for product in products:
            all_fields.update(product.keys())
        
        all_fields = sorted(list(all_fields))
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_fields)
            writer.writeheader()
            writer.writerows(products)
        
        print(f"💾 产品数据已保存到: {filename}")
        print(f"📊 共保存 {len(products)} 个产品，{len(all_fields)} 个字段")
        
        return filename
    
    def save_to_json(self, products: List[Dict[str, Any]], filename: str = None) -> str:
        """保存产品数据到JSON文件"""
        if not products:
            print("❌ 无产品数据可保存")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"erp_products_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(products, jsonfile, ensure_ascii=False, indent=2)
        
        print(f"💾 产品数据已保存到: {filename}")
        print(f"📊 共保存 {len(products)} 个产品")
        
        return filename
    
    def analyze_products(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析产品数据"""
        if not products:
            return {"error": "无产品数据"}
        
        analysis = {
            "total_count": len(products),
            "fields_count": len(products[0].keys()) if products else 0,
            "field_names": list(products[0].keys()) if products else [],
            "sample_product": products[0] if products else None
        }
        
        # 统计非空字段
        field_stats = {}
        for product in products:
            for field, value in product.items():
                if field not in field_stats:
                    field_stats[field] = {"total": 0, "non_empty": 0}
                field_stats[field]["total"] += 1
                if value and str(value).strip():
                    field_stats[field]["non_empty"] += 1
        
        analysis["field_statistics"] = field_stats
        
        return analysis


def main():
    """主函数"""
    # 从环境变量获取ERP配置
    base_url = os.getenv("ERP_BASE_URL", "http://ls1.jmt.ink:46088")
    username = os.getenv("ERP_USERNAME", "admin")
    password = os.getenv("ERP_PASSWORD", "Abcd@1234")
    
    print("=" * 60)
    print("🏭 ERP产品数据获取工具")
    print("=" * 60)
    print(f"📍 ERP地址: {base_url}")
    print(f"👤 用户名: {username}")
    print(f"🔑 密码: {'*' * len(password)}")
    print("=" * 60)
    
    # 创建获取器
    fetcher = ERPProductFetcher(base_url, username, password)
    
    # 登录
    if not fetcher.login():
        print("❌ 登录失败，程序退出")
        return
    
    # 获取全量产品数据
    products = fetcher.get_all_products(page_size=50)  # 使用较小的页面大小避免超时
    
    if not products:
        print("❌ 未获取到任何产品数据")
        return
    
    # 保存数据
    csv_file = fetcher.save_to_csv(products)
    json_file = fetcher.save_to_json(products)
    
    # 分析数据
    print("\n" + "=" * 60)
    print("📊 产品数据分析")
    print("=" * 60)
    
    analysis = fetcher.analyze_products(products)
    print(f"📦 产品总数: {analysis['total_count']}")
    print(f"🏷️  字段数量: {analysis['fields_count']}")
    print(f"📋 字段列表: {', '.join(analysis['field_names'][:10])}{'...' if len(analysis['field_names']) > 10 else ''}")
    
    # 显示字段统计
    print("\n📈 字段完整性统计:")
    for field, stats in analysis['field_statistics'].items():
        completeness = (stats['non_empty'] / stats['total']) * 100
        print(f"  {field}: {stats['non_empty']}/{stats['total']} ({completeness:.1f}%)")
    
    # 显示示例产品
    if analysis['sample_product']:
        print(f"\n🔍 示例产品数据:")
        for key, value in list(analysis['sample_product'].items())[:5]:
            print(f"  {key}: {value}")
        if len(analysis['sample_product']) > 5:
            print(f"  ... 还有 {len(analysis['sample_product']) - 5} 个字段")
    
    print(f"\n✅ 数据获取完成！")
    print(f"📄 CSV文件: {csv_file}")
    print(f"📄 JSON文件: {json_file}")


if __name__ == "__main__":
    main()
