#!/usr/bin/env python3
"""
测试ERP session格式，参考客户接口的成功模式
"""

import requests
import json
import os


def test_session_formats():
    """测试不同的session格式"""
    base_url = os.getenv("ERP_BASE_URL", "http://ls1.jmt.ink:46088")
    username = os.getenv("ERP_USERNAME", "admin")
    password = os.getenv("ERP_PASSWORD", "Abcd@1234")
    
    print(f"🔐 登录ERP系统...")
    
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
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        if login_result.get('header', {}).get('status') == 0:
            print(f"✅ 登录成功")
            print(f"🍪 Cookies: {session.cookies.get_dict()}")
            
            # 先测试客户接口（已知可工作）
            print("\n" + "=" * 60)
            print("👥 测试客户接口（参考）...")
            
            customer_url = f"{base_url}/webapi/v3/ov1/customer"
            customer_data = {
                "session": "",  # 客户接口使用空session
                "cmdkey": "refresh",
                "datas": [
                    {"id": "pagesize", "val": "5"},
                    {"id": "pageindex", "val": "1"},
                    {"id": "_rpt_sort", "val": ""}
                ]
            }
            
            try:
                customer_response = session.post(customer_url, json=customer_data, timeout=30)
                print(f"📊 客户接口状态码: {customer_response.status_code}")
                
                if customer_response.status_code == 200:
                    customer_result = customer_response.json()
                    print(f"📋 客户接口响应: {json.dumps(customer_result, ensure_ascii=False, indent=2)}")
                    
                    if customer_result.get('header', {}).get('status') == 0:
                        print(f"✅ 客户接口成功！")
                        
                        # 现在测试产品接口，使用相同的session格式
                        print("\n" + "=" * 60)
                        print("📦 测试产品接口...")
                        
                        products_url = f"{base_url}/sysa/mobilephone/salesmanage/product/billlist.asp"
                        
                        # 尝试不同的参数组合
                        test_cases = [
                            {
                                "session": "",
                                "datas": [
                                    {"id": "pagesize", "val": "5"},
                                    {"id": "pageindex", "val": "1"},
                                    {"id": "_rpt_sort", "val": ""}
                                ],
                                "desc": "最小参数集"
                            },
                            {
                                "session": "",
                                "datas": [
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
                                    {"id": "pagesize", "val": "5"},
                                    {"id": "pageindex", "val": "1"},
                                    {"id": "_rpt_sort", "val": ""}
                                ],
                                "desc": "完整参数集"
                            }
                        ]
                        
                        for i, test_case in enumerate(test_cases, 1):
                            print(f"\n🧪 测试用例 {i}: {test_case['desc']}")
                            
                            products_data = {
                                "session": test_case['session'],
                                "cmdkey": "refresh",
                                "datas": test_case['datas']
                            }
                            
                            try:
                                response = session.post(products_url, json=products_data, timeout=30)
                                print(f"   📊 状态码: {response.status_code}")
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    print(f"   📋 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                                    
                                    if result.get('header', {}).get('status') == 0:
                                        print(f"   ✅ 成功！")
                                        break
                                    else:
                                        print(f"   ❌ 失败: {result.get('header', {}).get('message', '未知错误')}")
                                else:
                                    print(f"   ❌ HTTP错误: {response.status_code}")
                                    print(f"   响应内容: {response.text[:200]}...")
                                    
                            except Exception as e:
                                print(f"   ❌ 异常: {e}")
                    else:
                        print(f"❌ 客户接口失败: {customer_result.get('header', {}).get('message', '未知错误')}")
                else:
                    print(f"❌ 客户接口请求失败: {customer_response.status_code}")
            except Exception as e:
                print(f"❌ 客户接口异常: {e}")
        else:
            print(f"❌ 登录失败: {login_result.get('header', {}).get('message', '未知错误')}")
    else:
        print(f"❌ 登录请求失败: {login_response.status_code}")


if __name__ == "__main__":
    test_session_formats()
