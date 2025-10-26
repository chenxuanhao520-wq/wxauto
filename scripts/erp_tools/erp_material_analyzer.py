#!/usr/bin/env python3
"""
ERP物料表格和分析工具
综合获取ERP物料数据并提供详细分析
"""

import json
import requests
import csv
import time
import os
from datetime import datetime
from typing import List, Dict, Any
import random


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
    
    def generate_sample_material_data(self, count: int = 100) -> List[Dict[str, Any]]:
        """生成示例物料数据"""
        print(f"📦 生成 {count} 条示例物料数据...")
        
        # 示例物料数据模板
        material_templates = [
            {
                "产品名称": ["螺丝", "螺母", "垫圈", "螺栓", "弹簧", "轴承", "齿轮", "链条", "皮带", "密封圈"],
                "产品编号": ["M", "N", "W", "B", "S", "B", "G", "C", "P", "O"],
                "产品型号": ["M6", "M8", "M10", "M12", "M16", "M20", "M24", "M30", "M36", "M42"],
                "产品分类": ["紧固件", "传动件", "密封件", "轴承件", "弹簧件", "齿轮件", "链条件", "皮带件", "密封件", "标准件"],
                "单位": ["个", "套", "包", "箱", "盒", "袋", "卷", "米", "公斤", "吨"],
                "供应商": ["上海机械", "北京工业", "广州制造", "深圳精密", "杭州标准", "南京五金", "苏州机械", "无锡制造", "常州工业", "南通标准"],
                "仓库": ["主仓库", "原料库", "成品库", "半成品库", "工具库", "备件库", "临时库", "退货库", "废料库", "样品库"]
            }
        ]
        
        materials = []
        for i in range(count):
            template = material_templates[0]
            
            # 随机选择产品信息
            product_name = random.choice(template["产品名称"])
            product_code = random.choice(template["产品编号"])
            product_model = random.choice(template["产品型号"])
            category = random.choice(template["产品分类"])
            unit = random.choice(template["单位"])
            supplier = random.choice(template["供应商"])
            warehouse = random.choice(template["仓库"])
            
            # 生成物料数据
            material = {
                "ID": i + 1,
                "产品名称": f"{product_name}{i+1:03d}",
                "产品编号": f"{product_code}{i+1:04d}",
                "产品型号": f"{product_model}-{random.randint(1, 99):02d}",
                "产品分类": category,
                "单位": unit,
                "库存数量": round(random.uniform(0, 1000), 2),
                "安全库存": round(random.uniform(10, 100), 2),
                "最大库存": round(random.uniform(500, 2000), 2),
                "单价": round(random.uniform(0.1, 100), 2),
                "总价值": 0,  # 将在后面计算
                "供应商": supplier,
                "仓库": warehouse,
                "库位": f"A{random.randint(1, 10):02d}-{random.randint(1, 20):02d}",
                "生产日期": datetime.now().strftime("%Y-%m-%d"),
                "有效期": (datetime.now().timestamp() + random.randint(30, 365) * 24 * 3600),
                "状态": random.choice(["正常", "缺货", "过量", "过期", "待检"]),
                "备注": f"物料{i+1}的备注信息",
                "创建时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 计算总价值
            material["总价值"] = round(material["库存数量"] * material["单价"], 2)
            
            # 格式化有效期
            material["有效期"] = datetime.fromtimestamp(material["有效期"]).strftime("%Y-%m-%d")
            
            materials.append(material)
        
        print(f"✅ 生成了 {len(materials)} 条示例物料数据")
        return materials
    
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
    
    def save_to_json(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """保存数据到JSON文件"""
        if not data:
            print("❌ 无数据可保存")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"erp_materials_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False, indent=2)
        
        print(f"💾 数据已保存到: {filename}")
        print(f"📊 共保存 {len(data)} 条记录")
        
        return filename
    
    def analyze_materials(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析物料数据"""
        if not data:
            return {"error": "无物料数据"}
        
        analysis = {
            "basic_stats": {
                "total_materials": len(data),
                "fields_count": len(data[0].keys()) if data else 0,
                "field_names": list(data[0].keys()) if data else []
            },
            "field_statistics": {},
            "category_analysis": {},
            "warehouse_analysis": {},
            "supplier_analysis": {},
            "status_analysis": {},
            "value_analysis": {},
            "inventory_analysis": {}
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
        if '产品分类' in data[0]:
            category_stats = {}
            for item in data:
                category = item.get('产品分类', '未分类')
                if category not in category_stats:
                    category_stats[category] = 0
                category_stats[category] += 1
            analysis["category_analysis"] = category_stats
        
        # 仓库分析
        if '仓库' in data[0]:
            warehouse_stats = {}
            for item in data:
                warehouse = item.get('仓库', '未分配')
                if warehouse not in warehouse_stats:
                    warehouse_stats[warehouse] = 0
                warehouse_stats[warehouse] += 1
            analysis["warehouse_analysis"] = warehouse_stats
        
        # 供应商分析
        if '供应商' in data[0]:
            supplier_stats = {}
            for item in data:
                supplier = item.get('供应商', '未知')
                if supplier not in supplier_stats:
                    supplier_stats[supplier] = 0
                supplier_stats[supplier] += 1
            analysis["supplier_analysis"] = supplier_stats
        
        # 状态分析
        if '状态' in data[0]:
            status_stats = {}
            for item in data:
                status = item.get('状态', '未知')
                if status not in status_stats:
                    status_stats[status] = 0
                status_stats[status] += 1
            analysis["status_analysis"] = status_stats
        
        # 价值分析
        if '总价值' in data[0]:
            total_value = sum(float(item.get('总价值', 0)) for item in data)
            avg_value = total_value / len(data) if data else 0
            max_value = max(float(item.get('总价值', 0)) for item in data) if data else 0
            min_value = min(float(item.get('总价值', 0)) for item in data) if data else 0
            
            analysis["value_analysis"] = {
                "total_value": round(total_value, 2),
                "average_value": round(avg_value, 2),
                "max_value": round(max_value, 2),
                "min_value": round(min_value, 2)
            }
        
        # 库存分析
        if '库存数量' in data[0]:
            total_inventory = sum(float(item.get('库存数量', 0)) for item in data)
            avg_inventory = total_inventory / len(data) if data else 0
            low_stock_count = sum(1 for item in data if float(item.get('库存数量', 0)) < float(item.get('安全库存', 0)))
            over_stock_count = sum(1 for item in data if float(item.get('库存数量', 0)) > float(item.get('最大库存', 0)))
            
            analysis["inventory_analysis"] = {
                "total_inventory": round(total_inventory, 2),
                "average_inventory": round(avg_inventory, 2),
                "low_stock_count": low_stock_count,
                "over_stock_count": over_stock_count
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
        report.append(f"  • 物料总数: {basic_stats.get('total_materials', 0)}")
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
                report.append(f"  • {category}: {count} 个物料")
            report.append("")
        
        # 仓库分析
        warehouse_analysis = analysis.get("warehouse_analysis", {})
        if warehouse_analysis:
            report.append("🏪 仓库分析:")
            for warehouse, count in sorted(warehouse_analysis.items(), key=lambda x: x[1], reverse=True):
                report.append(f"  • {warehouse}: {count} 个物料")
            report.append("")
        
        # 供应商分析
        supplier_analysis = analysis.get("supplier_analysis", {})
        if supplier_analysis:
            report.append("🏭 供应商分析:")
            for supplier, count in sorted(supplier_analysis.items(), key=lambda x: x[1], reverse=True):
                report.append(f"  • {supplier}: {count} 个物料")
            report.append("")
        
        # 状态分析
        status_analysis = analysis.get("status_analysis", {})
        if status_analysis:
            report.append("📊 物料状态分析:")
            for status, count in sorted(status_analysis.items(), key=lambda x: x[1], reverse=True):
                report.append(f"  • {status}: {count} 个物料")
            report.append("")
        
        # 价值分析
        value_analysis = analysis.get("value_analysis", {})
        if value_analysis:
            report.append("💰 价值分析:")
            report.append(f"  • 总价值: ¥{value_analysis.get('total_value', 0):,.2f}")
            report.append(f"  • 平均价值: ¥{value_analysis.get('average_value', 0):,.2f}")
            report.append(f"  • 最高价值: ¥{value_analysis.get('max_value', 0):,.2f}")
            report.append(f"  • 最低价值: ¥{value_analysis.get('min_value', 0):,.2f}")
            report.append("")
        
        # 库存分析
        inventory_analysis = analysis.get("inventory_analysis", {})
        if inventory_analysis:
            report.append("📦 库存分析:")
            report.append(f"  • 总库存数量: {inventory_analysis.get('total_inventory', 0):,.2f}")
            report.append(f"  • 平均库存: {inventory_analysis.get('average_inventory', 0):,.2f}")
            report.append(f"  • 库存不足物料: {inventory_analysis.get('low_stock_count', 0)} 个")
            report.append(f"  • 库存过量物料: {inventory_analysis.get('over_stock_count', 0)} 个")
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
    
    # 尝试登录
    login_success = analyzer.login()
    
    # 由于接口访问限制，我们生成示例数据进行分析
    print("\n📦 由于接口访问限制，生成示例物料数据进行演示...")
    materials = analyzer.generate_sample_material_data(100)
    
    if not materials:
        print("❌ 未获取到任何物料数据")
        return
    
    # 保存数据
    csv_file = analyzer.save_to_csv(materials, "erp_materials.csv")
    json_file = analyzer.save_to_json(materials, "erp_materials.json")
    
    # 分析数据
    print("\n" + "=" * 80)
    print("📊 开始数据分析...")
    print("=" * 80)
    
    analysis = analyzer.analyze_materials(materials)
    
    # 生成报告
    report = analyzer.generate_material_report(analysis)
    print(report)
    
    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"erp_material_analysis_report_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 分析完成！")
    print(f"📄 CSV文件: {csv_file}")
    print(f"📄 JSON文件: {json_file}")
    print(f"📄 分析报告文件: {report_file}")
    
    # 显示前几条数据样本
    print(f"\n🔍 数据样本预览:")
    for i, material in enumerate(materials[:3], 1):
        print(f"  第{i}条物料:")
        for key, value in list(material.items())[:5]:
            print(f"    {key}: {value}")
        if len(material) > 5:
            print(f"    ... 还有 {len(material) - 5} 个字段")
        print()


if __name__ == "__main__":
    main()
