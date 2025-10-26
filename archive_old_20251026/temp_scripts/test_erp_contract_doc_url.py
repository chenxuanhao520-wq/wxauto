#!/usr/bin/env python3
"""
测试使用文档中的完整 URL
"""

import json
import requests
import os

def test_with_doc_url():
    """使用文档中的 URL 测试"""
    print("\n" + "=" * 70)
    print("🔍 使用文档中的完整 URL 测试合同 API")
    print("=" * 70)
    
    # 使用文档中的 URL
    base_url = "http://s1.jmt.inic46388"  # 文档中的 URL
    username = "admin"
    password = "Abcd@1234"
    
    print(f"\n📋 连接信息:")
    print(f"  URL: {base_url}")
    print(f"  用户: {username}")
    
    # 步骤 1: 登录获取 session
    print(f"\n📝 步骤 1: 登录获取 session...")
    
    login_url = f"{base_url}/webapi/v3/ov1/login"
    login_data = {
        "datas": [
            {"id": "user", "val": f"txt:{username}"},
            {"id": "password", "val": f"txt:{password}"},
            {"id": "serialnum", "val": "txt:mcp_erp_client_001"}
        ]
    }
    
    try:
        login_response = requests.post(
            login_url,
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"  登录响应状态: {login_response.status_code}")
        
        if login_response.status_code == 200:
            try:
                login_result = login_response.json()
                if login_result.get('header', {}).get('status') == 0:
                    session_token = login_result.get('header', {}).get('session')
                    print(f"  ✅ 登录成功，获取到 session: {session_token}")
                else:
                    print(f"  ❌ 登录失败: {login_result}")
                    return
            except:
                print(f"  ❌ 登录响应不是 JSON 格式: {login_response.text[:200]}")
                return
        else:
            print(f"  ❌ 登录请求失败: {login_response.status_code}")
            print(f"  响应内容: {login_response.text[:200]}")
            return
            
    except Exception as e:
        print(f"  ❌ 登录异常: {e}")
        return
    
    # 步骤 2: 测试合同 API
    print(f"\n📝 步骤 2: 测试合同 API...")
    
    # 使用文档中的完整 URL
    url = f"{base_url}/sysa/mobilephone/salesmanage/contract/blist.asp"
    
    # 按照文档构建参数
    dats = {
        "stype": 0,
        "datatype": "",
        "remind": "",
        "tdate1": "",
        "tdate2": "",
        "a_date_0": "",
        "a_date_1": "",
        "htbh": "",
        "khmc": "",
        "htmoney_0": 0,
        "htmoney_1": 0,
        "dateQD_0": "",
        "dateQD_1": "",
        "dateKS_0": "",
        "dateKS_1": "",
        "dateZZ_0": "",
        "dateZZ_1": "",
        "searchKey": "",
        "pagesize": 10,
        "pageindex": 1,
        "_rpt_sort": ""
    }
    
    datas = [{"id": key, "val": value} for key, value in dats.items()]
    
    json_data = {
        "session": session_token,
        "cmdkey": "refresh",
        "datas": datas
    }
    
    print(f"  合同 API 请求: {url}")
    
    try:
        response = requests.post(
            url,
            json=json_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"  响应状态: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"  ✅ JSON 解析成功")
                
                if result.get('header', {}).get('status') == 0:
                    body = result.get('body', {})
                    source = body.get('source', {})
                    table = source.get('table', {})
                    rows = table.get('rows', [])
                    
                    print(f"\n🎉 合同 API 调用成功！")
                    print(f"  合同总数: {len(rows)}")
                    
                    if rows:
                        print(f"\n📋 前3个合同数据:")
                        for i, row in enumerate(rows[:3], 1):
                            print(f"  合同 {i}: {row}")
                    else:
                        print(f"  ⚠️  没有合同数据")
                else:
                    print(f"  ❌ API 调用失败: {result.get('header', {}).get('message')}")
                    
            except json.JSONDecodeError as e:
                print(f"  ❌ JSON 解析失败: {e}")
                print(f"  原始响应: {response.text[:500]}...")
        else:
            print(f"  ❌ HTTP 请求失败: {response.status_code}")
            print(f"  响应内容: {response.text[:200]}")
            
    except Exception as e:
        print(f"  ❌ API 调用异常: {e}")
    
    print(f"\n💡 测试完成")


if __name__ == "__main__":
    test_with_doc_url()

