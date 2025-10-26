#!/usr/bin/env python3
"""
调试客户接口响应，查看原始内容
"""

import requests
import json
import os


def debug_customer_response():
    """调试客户接口响应"""
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
            
            # 测试客户接口
            print("\n" + "=" * 60)
            print("👥 测试客户接口...")
            
            customer_url = f"{base_url}/webapi/v3/ov1/customer"
            customer_data = {
                "session": "",
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
                print(f"📊 响应头: {dict(customer_response.headers)}")
                print(f"📊 响应内容长度: {len(customer_response.text)}")
                print(f"📊 响应内容前500字符: {customer_response.text[:500]}")
                
                # 尝试解析JSON
                try:
                    customer_result = customer_response.json()
                    print(f"📋 客户接口JSON响应: {json.dumps(customer_result, ensure_ascii=False, indent=2)}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON解析失败: {e}")
                    print(f"原始响应: {customer_response.text}")
                
            except Exception as e:
                print(f"❌ 客户接口异常: {e}")
        else:
            print(f"❌ 登录失败: {login_result.get('header', {}).get('message', '未知错误')}")
    else:
        print(f"❌ 登录请求失败: {login_response.status_code}")


if __name__ == "__main__":
    debug_customer_response()
