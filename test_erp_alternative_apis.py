#!/usr/bin/env python3
"""
测试智邦 ERP 其他可能的 API 接口
包括订单、合同、产品等
"""

import json
import requests
import os

def test_alternative_apis():
    """测试其他可能的 API 接口"""
    print("\n" + "=" * 70)
    print("🔍 测试智邦 ERP 其他可能的 API 接口")
    print("=" * 70)
    
    # 设置凭据
    base_url = "http://ls1.jmt.ink:46088"
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
    
    # 步骤 2: 测试各种可能的 API 接口
    test_apis = [
        # 订单相关
        "/sysa/mobilephone/salesmanage/salesorder/list.asp",
        "/sysa/mobilephone/salesmanage/salesorder.asp",
        "/sysa/mobilephone/salesmanage/order/list.asp",
        "/sysa/mobilephone/salesmanage/order.asp",
        
        # 合同相关
        "/sysa/mobilephone/salesmanage/contract/list.asp",
        "/sysa/mobilephone/salesmanage/contract.asp",
        "/sysa/mobilephone/salesmanage/agreement/list.asp",
        "/sysa/mobilephone/salesmanage/agreement.asp",
        
        # 产品相关
        "/sysa/mobilephone/salesmanage/product/list.asp",
        "/sysa/mobilephone/salesmanage/product.asp",
        "/sysa/mobilephone/salesmanage/goods/list.asp",
        "/sysa/mobilephone/salesmanage/goods.asp",
        
        # 其他可能的模块
        "/sysa/mobilephone/salesmanage/quotation/list.asp",
        "/sysa/mobilephone/salesmanage/quotation.asp",
        "/sysa/mobilephone/salesmanage/invoice/list.asp",
        "/sysa/mobilephone/salesmanage/invoice.asp",
    ]
    
    successful_apis = []
    
    for api_path in test_apis:
        print(f"\n📝 测试 API: {api_path}")
        
        try:
            url = f"{base_url}{api_path}"
            
            # 构建基本查询参数
            dats = {
                "pagesize": 5,
                "pageindex": 1
            }
            
            # 转换为 id-val 键值对数组格式
            datas = [{"id": key, "val": value} for key, value in dats.items()]
            
            json_data = {
                "session": session_token,
                "cmdkey": "refresh",
                "datas": datas
            }
            
            response = requests.post(
                url,
                json=json_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            print(f"  响应状态: {response.status_code}")
            
            # 尝试解析响应
            try:
                result = response.json()
                print(f"  ✅ JSON 解析成功")
                
                # 检查响应状态
                if result.get('header', {}).get('status') == 0:
                    body = result.get('body', {})
                    source = body.get('source', {})
                    table = source.get('table', {})
                    rows = table.get('rows', [])
                    
                    if rows:
                        print(f"  🎉 找到 {len(rows)} 条数据！")
                        successful_apis.append({
                            'path': api_path,
                            'count': len(rows),
                            'data': rows[:2]  # 只保存前2条数据作为示例
                        })
                    else:
                        print(f"  ⚠️  没有数据，但 API 可用")
                        successful_apis.append({
                            'path': api_path,
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
        print(f"❌ 没有找到可用的 API 接口")
        print(f"\n💡 建议:")
        print(f"  1. 检查 ERP 系统的版本和模块")
        print(f"  2. 联系 ERP 供应商获取正确的 API 文档")
        print(f"  3. 或者通过浏览器登录 ERP 系统查看实际的接口路径")
    
    print(f"\n💡 调试完成")


if __name__ == "__main__":
    test_alternative_apis()

