#!/usr/bin/env python3
"""
测试不同的合同 API 路径
"""

import json
import requests
import os

def test_contract_paths():
    """测试不同的合同 API 路径"""
    print("\n" + "=" * 70)
    print("🔍 测试不同的合同 API 路径")
    print("=" * 70)
    
    base_url = "http://ls1.jmt.ink:46088"
    username = "admin"
    password = "Abcd@1234"
    
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
        
        login_result = login_response.json()
        
        if login_result.get('header', {}).get('status') == 0:
            session_token = login_result.get('header', {}).get('session')
            print(f"  ✅ 登录成功，获取到 session: {session_token}")
        else:
            print(f"  ❌ 登录失败")
            return
            
    except Exception as e:
        print(f"  ❌ 登录异常: {e}")
        return
    
    # 步骤 2: 测试不同的合同 API 路径
    contract_paths = [
        # 按照文档的路径
        "/sysa/mobilephone/salesmanage/contract/blist.asp",
        
        # 其他可能的合同路径
        "/sysa/mobilephone/salesmanage/contract/list.asp",
        "/sysa/mobilephone/salesmanage/contract.asp",
        "/sysa/mobilephone/salesmanage/contract/list.asp?datatype=contract",
        "/sysa/mobilephone/salesmanage/contract.asp?datatype=contract",
        
        # 尝试其他模块
        "/sysa/mobilephone/salesmanage/ht/list.asp",  # ht可能是合同的缩写
        "/sysa/mobilephone/salesmanage/ht.asp",
        "/sysa/mobilephone/salesmanage/ht/blist.asp",
        
        # 尝试系统管理模块
        "/sysa/mobilephone/systemmanage/contract/blist.asp",
        "/sysa/mobilephone/systemmanage/contract/list.asp",
        
        # 尝试其他可能的命名
        "/sysa/mobilephone/salesmanage/agreement/blist.asp",
        "/sysa/mobilephone/salesmanage/agreement/list.asp",
    ]
    
    # 构建基本参数
    dats = {
        "stype": 0,
        "pagesize": 5,
        "pageindex": 1
    }
    
    datas = [{"id": key, "val": value} for key, value in dats.items()]
    
    json_data = {
        "session": session_token,
        "cmdkey": "refresh",
        "datas": datas
    }
    
    successful_apis = []
    
    for path in contract_paths:
        print(f"\n📝 测试路径: {path}")
        
        try:
            url = f"{base_url}{path}"
            
            response = requests.post(
                url,
                json=json_data,
                headers={"Content-Type": "application/json"},
                timeout=30
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
                        
                        if rows:
                            print(f"  🎉 找到 {len(rows)} 条数据！")
                            successful_apis.append({
                                'path': path,
                                'count': len(rows),
                                'data': rows[:2]
                            })
                        else:
                            print(f"  ⚠️  没有数据，但 API 可用")
                            successful_apis.append({
                                'path': path,
                                'count': 0,
                                'data': []
                            })
                    else:
                        print(f"  ❌ API 调用失败: {result.get('header', {}).get('message')}")
                        
                except json.JSONDecodeError as e:
                    print(f"  ❌ JSON 解析失败: {e}")
                    if "404" in response.text:
                        print(f"  📍 接口不存在")
                    else:
                        print(f"  📍 响应不是 JSON 格式")
            else:
                print(f"  ❌ HTTP 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ API 调用异常: {e}")
    
    # 总结结果
    print(f"\n" + "=" * 70)
    print(f"📊 测试结果总结")
    print(f"=" * 70)
    
    if successful_apis:
        print(f"✅ 找到 {len(successful_apis)} 个可用的 API 接口:")
        
        for api in successful_apis:
            print(f"\n📋 {api['path']}")
            print(f"  数据条数: {api['count']}")
            
            if api['data']:
                print(f"  示例数据:")
                for i, row in enumerate(api['data'], 1):
                    print(f"    数据 {i}: {row}")
    else:
        print(f"❌ 没有找到可用的合同 API 接口")
        print(f"\n💡 可能的原因:")
        print(f"  1. ERP 系统中没有启用合同管理模块")
        print(f"  2. 合同模块的路径与文档不符")
        print(f"  3. 需要特定的权限或配置")
    
    print(f"\n💡 测试完成")


if __name__ == "__main__":
    test_contract_paths()

