#!/usr/bin/env python3
"""
ERP库存物料数据获取工具
使用库存接口获取物料信息
"""

import json
import requests
import csv
import time
import os
from datetime import datetime
from typing import List, Dict, Any


class ERPInventoryFetcher:
    """ERP库存数据获取器"""
    
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
    
    def get_inventory_summary(self, page_size: int = 100, page_index: int = 1) -> List[Dict[str, Any]]:
        """获取库存汇总数据"""
        if not self.session_token:
            print("❌ 未登录，请先调用login()")
            return []
        
        try:
            url = f"{self.base_url}/webapi/v3/store/inventory/InventorySummary"
            
            # 构建请求参数
            params = {
                "page_size": page_size,
                "page_index": page_index
            }
            
            print(f"📦 正在获取库存汇总数据 (第{page_index}页，每页{page_size}条)...")
            
            # 添加认证头
            headers = {
                "ZBAPI-Token": self.session_token
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            print(f"📋 响应状态: {result.get('Code', '未知')}")
            
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
    
    def get_inventory_details(self, page_size: int = 100, page_index: int = 1) -> List[Dict[str, Any]]:
        """获取库存详情数据"""
        if not self.session_token:
            print("❌ 未登录，请先调用login()")
            return []
        
        try:
            url = f"{self.base_url}/webapi/v3/store/inventory/InventoryDetails"
            
            # 构建请求参数
            params = {
                "page_size": page_size,
                "page_index": page_index
            }
            
            print(f"📦 正在获取库存详情数据 (第{page_index}页，每页{page_size}条)...")
            
            # 添加认证头
            headers = {
                "ZBAPI-Token": self.session_token
            }
            
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            print(f"📋 响应状态: {result.get('Code', '未知')}")
            
            if result.get('Code') == 200:
                rows = result.get('Rows', [])
                print(f"✅ 获取到 {len(rows)} 条库存详情数据")
                return rows
            else:
                print(f"❌ 获取库存详情数据失败: {result.get('Msg', '未知错误')}")
                return []
                
        except Exception as e:
            print(f"❌ 获取库存详情数据异常: {e}")
            return []
    
    def get_all_inventory_data(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """获取全量库存数据"""
        all_data = []
        page = 1
        
        print(f"🚀 开始获取全量库存数据 (每页{page_size}条)...")
        
        while True:
            # 获取汇总数据
            summary_data = self.get_inventory_summary(page_size, page)
            if not summary_data:
                break
            
            all_data.extend(summary_data)
            page += 1
            
            # 避免请求过于频繁
            time.sleep(0.5)
            
            # 限制最大页数，避免无限循环
            if page > 50:  # 最多获取50页
                print("⚠️  达到最大页数限制，停止获取")
                break
        
        print(f"📊 库存汇总数据获取完成，共 {len(all_data)} 条记录")
        return all_data
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """保存数据到CSV文件"""
        if not data:
            print("❌ 无数据可保存")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"erp_inventory_{timestamp}.csv"
        
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
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """保存数据到JSON文件"""
        if not data:
            print("❌ 无数据可保存")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"erp_inventory_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2)
        
        print(f"💾 数据已保存到: {filename}")
        print(f"📊 共保存 {len(data)} 条记录")
        
        return filename
    
    def analyze_inventory(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析库存数据"""
        if not data:
            return {"error": "无库存数据"}
        
        analysis = {
            "basic_stats": {
                "total_items": len(data),
                "fields_count": len(data[0].keys()) if data else 0,
                "field_names": list(data[0].keys()) if data else []
            },
            "field_statistics": {},
            "category_analysis": {},
            "warehouse_analysis": {}
        }
        
        # 统计字段完整性
        field_stats = {}
        for item in data:
            for field, value in item.items():
                if field not in field_stats:
                    field_stats[field] = {"total": 0, "non_empty": 0}
                field_stats[field]["total"] += 1
                if value and str(value).strip():
                    field_stats[field]["non_empty"] += 1
        
        analysis["field_statistics"] = field_stats
        
        # 产品分类分析
        if 'ProductSort' in data[0]:  # 产品分类字段
            category_stats = {}
            for item in data:
                category = item.get('ProductSort', '未分类')
                if category not in category_stats:
                    category_stats[category] = 0
                category_stats[category] += 1
            analysis["category_analysis"] = category_stats
        
        # 仓库分析
        if 'Ku' in data[0]:  # 仓库字段
            warehouse_stats = {}
            for item in data:
                warehouse = item.get('Ku', '未分配')
                if warehouse not in warehouse_stats:
                    warehouse_stats[warehouse] = 0
                warehouse_stats[warehouse] += 1
            analysis["warehouse_analysis"] = warehouse_stats
        
        return analysis
    
    def generate_inventory_report(self, analysis: Dict[str, Any]) -> str:
        """生成库存分析报告"""
        report = []
        report.append("=" * 80)
        report.append("📊 ERP库存物料数据分析报告")
        report.append("=" * 80)
        report.append(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 基础统计
        basic_stats = analysis.get("basic_stats", {})
        report.append("📈 基础统计信息:")
        report.append(f"  • 库存项目数: {basic_stats.get('total_items', 0)}")
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
        
        # 仓库分析
        warehouse_analysis = analysis.get("warehouse_analysis", {})
        if warehouse_analysis:
            report.append("🏪 仓库分析:")
            for warehouse, count in sorted(warehouse_analysis.items(), key=lambda x: x[1], reverse=True):
                report.append(f"  • {warehouse}: {count} 个产品")
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
    print("🏭 ERP库存物料数据获取工具")
    print("=" * 80)
    print(f"📍 ERP地址: {base_url}")
    print(f"👤 用户名: {username}")
    print(f"🔑 密码: {'*' * len(password)}")
    print("=" * 80)
    
    # 创建获取器
    fetcher = ERPInventoryFetcher(base_url, username, password)
    
    # 登录
    if not fetcher.login():
        print("❌ 登录失败，程序退出")
        return
    
    # 获取库存数据
    print("\n📦 开始获取库存数据...")
    inventory_data = fetcher.get_all_inventory_data(page_size=50)
    
    if not inventory_data:
        print("❌ 未获取到任何库存数据")
        return
    
    # 保存数据
    csv_file = fetcher.save_to_csv(inventory_data, "erp_inventory.csv")
    json_file = fetcher.save_to_json(inventory_data, "erp_inventory.json")
    
    # 分析数据
    print("\n" + "=" * 80)
    print("📊 开始数据分析...")
    print("=" * 80)
    
    analysis = fetcher.analyze_inventory(inventory_data)
    
    # 生成报告
    report = fetcher.generate_inventory_report(analysis)
    print(report)
    
    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"erp_inventory_analysis_report_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 分析完成！")
    print(f"📄 CSV文件: {csv_file}")
    print(f"📄 JSON文件: {json_file}")
    print(f"📄 分析报告文件: {report_file}")


if __name__ == "__main__":
    main()
