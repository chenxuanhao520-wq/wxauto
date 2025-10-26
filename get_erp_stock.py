#!/usr/bin/env python3
"""
ERP库存查看数据获取工具
使用库存查看接口获取物料信息
"""

import json
import requests
import csv
import time
import os
from datetime import datetime
from typing import List, Dict, Any


class ERPStockFetcher:
    """ERP库存查看数据获取器"""
    
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
    
    def get_stock_list(self, page_size: int = 50, page_index: int = 1) -> List[Dict[str, Any]]:
        """获取库存列表数据"""
        if not self.session_token:
            print("❌ 未登录，请先调用login()")
            return []
        
        try:
            url = f"{self.base_url}/sysa/mobilephone/storemanage/store/list.asp"
            
            # 构建请求参数
            datas = [
                {"id": "dataType", "val": ""},      # 列表模式
                {"id": "ord", "val": ""},           # 列表数据检索条件
                {"id": "searchKey", "val": ""},    # 快速检索条件
                {"id": "pagesize", "val": str(page_size)},  # 每页记录数
                {"id": "pageindex", "val": str(page_index)}, # 数据页标
                {"id": "_rpt_sort", "val": ""}      # 排序字段
            ]
            
            json_data = {
                "session": "",  # 使用Cookie session
                "cmdkey": "refresh",
                "datas": datas
            }
            
            print(f"📦 正在获取库存列表数据 (第{page_index}页，每页{page_size}条)...")
            response = self.session.post(url, json=json_data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            print(f"📋 响应状态: {result.get('header', {}).get('status', '未知')}")
            
            if result.get('header', {}).get('status') == 0:
                body = result.get('body', {})
                source = body.get('source', {})
                table = source.get('table', {})
                rows_data = table.get('rows', [])
                cols = table.get('cols', [])
                
                if not rows_data:
                    print(f"⚠️  第{page_index}页无数据")
                    return []
                
                # 解析库存数据
                stock_items = []
                for row in rows_data:
                    item = {}
                    for i, col in enumerate(cols):
                        if i < len(row):
                            item[col['id']] = row[i]
                    stock_items.append(item)
                
                print(f"✅ 第{page_index}页获取到 {len(stock_items)} 个库存项目")
                return stock_items
            else:
                print(f"❌ 获取库存数据失败: {result.get('header', {}).get('message', '未知错误')}")
                return []
                
        except Exception as e:
            print(f"❌ 获取库存数据异常: {e}")
            return []
    
    def get_all_stock_data(self, page_size: int = 50) -> List[Dict[str, Any]]:
        """获取全量库存数据"""
        all_data = []
        page = 1
        
        print(f"🚀 开始获取全量库存数据 (每页{page_size}条)...")
        
        while True:
            stock_data = self.get_stock_list(page_size, page)
            
            if not stock_data:
                print(f"📊 已获取完所有数据，共 {len(all_data)} 个库存项目")
                break
            
            all_data.extend(stock_data)
            page += 1
            
            # 避免请求过于频繁
            time.sleep(0.5)
            
            # 限制最大页数，避免无限循环
            if page > 20:  # 最多获取20页
                print("⚠️  达到最大页数限制，停止获取")
                break
        
        return all_data
    
    def save_to_csv(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """保存数据到CSV文件"""
        if not data:
            print("❌ 无数据可保存")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"erp_stock_{timestamp}.csv"
        
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
            filename = f"erp_stock_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2)
        
        print(f"💾 数据已保存到: {filename}")
        print(f"📊 共保存 {len(data)} 条记录")
        
        return filename
    
    def analyze_stock(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
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
            "sample_data": data[:3] if data else []  # 前3条数据作为样本
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
        
        return analysis
    
    def generate_stock_report(self, analysis: Dict[str, Any]) -> str:
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
        
        # 样本数据
        sample_data = analysis.get("sample_data", [])
        if sample_data:
            report.append("🔍 样本数据预览:")
            for i, item in enumerate(sample_data, 1):
                report.append(f"  第{i}条数据:")
                for key, value in list(item.items())[:5]:  # 只显示前5个字段
                    report.append(f"    {key}: {value}")
                if len(item) > 5:
                    report.append(f"    ... 还有 {len(item) - 5} 个字段")
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
    fetcher = ERPStockFetcher(base_url, username, password)
    
    # 登录
    if not fetcher.login():
        print("❌ 登录失败，程序退出")
        return
    
    # 获取库存数据
    print("\n📦 开始获取库存数据...")
    stock_data = fetcher.get_all_stock_data(page_size=50)
    
    if not stock_data:
        print("❌ 未获取到任何库存数据")
        return
    
    # 保存数据
    csv_file = fetcher.save_to_csv(stock_data, "erp_stock.csv")
    json_file = fetcher.save_to_json(stock_data, "erp_stock.json")
    
    # 分析数据
    print("\n" + "=" * 80)
    print("📊 开始数据分析...")
    print("=" * 80)
    
    analysis = fetcher.analyze_stock(stock_data)
    
    # 生成报告
    report = fetcher.generate_stock_report(analysis)
    print(report)
    
    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"erp_stock_analysis_report_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 分析完成！")
    print(f"📄 CSV文件: {csv_file}")
    print(f"📄 JSON文件: {json_file}")
    print(f"📄 分析报告文件: {report_file}")


if __name__ == "__main__":
    main()
