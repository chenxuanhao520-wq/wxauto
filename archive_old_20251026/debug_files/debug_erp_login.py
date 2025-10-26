#!/usr/bin/env python3
"""
调试ERP登录接口，查看完整响应结构
"""

import requests
import json
import os


def debug_login():
    """调试登录接口"""
    base_url = os.getenv("ERP_BASE_URL", "http://ls1.jmt.ink:46088")
    username = os.getenv("ERP_USERNAME", "admin")
    password = os.getenv("ERP_PASSWORD", "Abcd@1234")
    
    print(f"🔐 调试ERP登录接口")
    print(f"📍 URL: {base_url}/webapi/v3/ov1/login")
    print(f"👤 用户: {username}")
    print("=" * 60)
    
    try:
        url = f"{base_url}/webapi/v3/ov1/login"
        datas = [
            {"id": "user", "val": f"txt:{username}"},
            {"id": "password", "val": f"txt:{password}"},
            {"id": "serialnum", "val": "txt:mcp_erp_client_001"}
        ]
        
        json_data = {
            "session": "",
            "cmdkey": "login",
            "datas": datas
        }
        
        print(f"📤 请求数据:")
        print(json.dumps(json_data, ensure_ascii=False, indent=2))
        print("=" * 60)
        
        response = requests.post(url, json=json_data, timeout=30)
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📊 响应头: {dict(response.headers)}")
        print("=" * 60)
        
        if response.status_code == 200:
            result = response.json()
            print(f"📋 完整响应:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            # 分析响应结构
            print("=" * 60)
            print("🔍 响应结构分析:")
            print(f"  header: {result.get('header', {})}")
            print(f"  body: {result.get('body', {})}")
            
            # 查找session
            session_locations = []
            def find_session(obj, path=""):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if k == "session":
                            session_locations.append(f"{path}.{k}" if path else k)
                        find_session(v, f"{path}.{k}" if path else k)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        find_session(item, f"{path}[{i}]")
            
            find_session(result)
            if session_locations:
                print(f"  🎯 找到session字段位置: {session_locations}")
            else:
                print(f"  ❌ 未找到session字段")
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 异常: {e}")


if __name__ == "__main__":
    debug_login()
