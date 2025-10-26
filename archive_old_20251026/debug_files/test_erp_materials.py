#!/usr/bin/env python3
"""
测试ERP物料接口
"""

import json
import requests
import os

def test_erp_materials():
    """测试ERP物料接口"""
    base_url = "http://ls1.jmt.ink:46088"
    username = "admin"
    password = "Abcd@1234"
    
    print("🔐 先登录获取session...")
    
    # 创建session
    session = requests.Session()
    
    # 登录
    login_url = f"{base_url}/webapi/v3/ov1/login"
    login_data = {
        "session": "",
        "cmdkey": "login",
        "datas": [
            {"id": "user", "val": f"txt:{username}"},
            {"id": "password", "val": f"txt:{password}"},
            {"id": "serialnum", "val": "txt:mcp_erp_client_001"}
        ]
    }
    
    login_response = session.post(login_url, json=login_data, timeout=30)
    print(f"📊 登录状态码: {login_response.status_code}")
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        print(f"📋 登录结果: {json.dumps(login_result, ensure_ascii=False, indent=2)}")
        
        if login_result.get('header', {}).get('status') == 0:
            print(f"✅ 登录成功")
            print(f"🍪 Cookies: {session.cookies.get_dict()}")
            
            # 测试产品接口
            print("\n" + "=" * 60)
            print("📦 测试产品接口...")
            
            products_url = f"{base_url}/sysa/mobilephone/salesmanage/product/billlist.asp"
            
            # 使用您提供的代码格式
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
                "pagesize": "10",                # 每页记录数
                "pageindex": "1",                # 数据页标
                "_rpt_sort": ""                  # 排序字段
            }
            
            # 转换为接口要求的格式
            datas = [{"id": key, "val": value} for key, value in dats.items()]
            
            json_data = {
                "session": "",  # 尝试空session
                "cmdkey": "refresh",
                "datas": datas
            }
            
            print(f"📤 请求数据: {json.dumps(json_data, ensure_ascii=False, indent=2)}")
            
            try:
                response = session.post(products_url, json=json_data, timeout=30)
                print(f"📊 状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"📋 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    
                    if result.get('header', {}).get('status') == 0:
                        print(f"✅ 成功获取产品数据！")
                        
                        # 解析数据
                        body = result.get('body', {})
                        source = body.get('source', {})
                        table = source.get('table', {})
                        rows_data = table.get('rows', [])
                        cols = table.get('cols', [])
                        
                        print(f"📊 获取到 {len(rows_data)} 行数据，{len(cols)} 个字段")
                        
                        if rows_data and cols:
                            print(f"📋 字段列表: {[col['id'] for col in cols]}")
                            print(f"📋 第一行数据: {rows_data[0] if rows_data else '无数据'}")
                            
                            # 保存数据到文件
                            with open('erp_materials_test.json', 'w', encoding='utf-8') as f:
                                json.dump(result, f, ensure_ascii=False, indent=2)
                            print(f"💾 数据已保存到 erp_materials_test.json")
                    else:
                        print(f"❌ 失败: {result.get('header', {}).get('message', '未知错误')}")
                else:
                    print(f"❌ HTTP错误: {response.status_code}")
                    print(f"响应内容: {response.text[:500]}...")
                    
            except Exception as e:
                print(f"❌ 异常: {e}")
        else:
            print(f"❌ 登录失败: {login_result.get('header', {}).get('message', '未知错误')}")
    else:
        print(f"❌ 登录请求失败: {login_response.status_code}")

if __name__ == "__main__":
    test_erp_materials()
