#!/usr/bin/env python3
"""
调试ERP产品接口，查看正确的请求格式
"""

import requests
import json
import os


def debug_products():
    """调试产品接口"""
    base_url = os.getenv("ERP_BASE_URL", "http://ls1.jmt.ink:46088")
    username = os.getenv("ERP_USERNAME", "admin")
    password = os.getenv("ERP_PASSWORD", "Abcd@1234")
    
    print(f"🔐 先登录获取session...")
    
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
            
            # 现在测试产品接口
            print("\n" + "=" * 60)
            print("📦 测试产品接口...")
            
            products_url = f"{base_url}/sysa/mobilephone/salesmanage/product/billlist.asp"
            
            # 尝试不同的session参数
            test_cases = [
                {"session": "", "desc": "空session"},
                {"session": "cookie_session", "desc": "cookie_session"},
                {"session": session.cookies.get('ZBCCSN', ''), "desc": "ZBCCSN cookie值"},
                {"session": session.cookies.get('ASP.NET_SessionId', ''), "desc": "ASP.NET_SessionId cookie值"},
            ]
            
            for i, test_case in enumerate(test_cases, 1):
                print(f"\n🧪 测试用例 {i}: {test_case['desc']}")
                print(f"   Session值: '{test_case['session']}'")
                
                products_data = {
                    "session": test_case['session'],
                    "cmdkey": "refresh",
                    "datas": [
                        {"id": "pagesize", "val": "5"},
                        {"id": "pageindex", "val": "1"},
                        {"id": "_rpt_sort", "val": ""}
                    ]
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
            print(f"❌ 登录失败: {login_result.get('header', {}).get('message', '未知错误')}")
    else:
        print(f"❌ 登录请求失败: {login_response.status_code}")


if __name__ == "__main__":
    debug_products()
