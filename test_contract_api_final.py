#!/usr/bin/env python3
"""
根据用户提供的合同API文档进行最终测试
使用正确的URL和参数格式
"""

import json
import requests
import os

def test_contract_api_final():
    """根据文档测试合同 API"""
    print("\n" + "=" * 70)
    print("🔍 根据文档测试智邦 ERP 合同 API")
    print("=" * 70)
    
    # 使用我们实际工作的 URL
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
    
    # 步骤 2: 测试合同 API - 使用文档中的正确路径
    print(f"\n📝 步骤 2: 测试合同 API...")
    
    # 使用文档中的路径：contract/blist.asp
    url = f"{base_url}/sysa/mobilephone/salesmanage/contract/blist.asp"
    
    # 按照文档构建完整的参数
    dats = {
        "stype": 0,          # 列表模式，0=全部，1=待审核，2=即将到期
        "datatype": "",      # 数据模式
        "remind": "",        # 提醒类型，14=合同审核，17=员工合同到期
        "tdate1": "",        # 添加开始日期
        "tdate2": "",        # 添加结束日期
        "a_date_0": "",      # 签约开始日期
        "a_date_1": "",      # 签约结束日期
        "htbh": "",          # 合同编号（模糊查询）
        "khmc": "",          # 客户名称（模糊查询）
        "htmoney_0": 0,      # 合同金额下限
        "htmoney_1": 0,      # 合同金额上限
        "dateQD_0": "",      # 签约日期开始
        "dateQD_1": "",      # 签约日期结束
        "dateKS_0": "",      # 合同开始日期开始
        "dateKS_1": "",      # 合同开始日期结束
        "dateZZ_0": "",      # 合同结束日期开始
        "dateZZ_1": "",      # 合同结束日期结束
        "searchKey": "",     # 快速检索条件
        "pagesize": 20,      # 每页记录数
        "pageindex": 1,      # 页码
        "_rpt_sort": ""      # 排序字段
    }
    
    # 转换为 id-val 键值对数组格式 - 这是关键！
    datas = [{"id": key, "val": value} for key, value in dats.items()]
    
    json_data = {
        "session": session_token,
        "cmdkey": "refresh",
        "datas": datas
    }
    
    print(f"  合同 API 请求: {url}")
    print(f"  请求参数数量: {len(datas)}")
    
    try:
        response = requests.post(
            url,
            json=json_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"  响应状态: {response.status_code}")
        print(f"  响应头 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        # 尝试解析响应
        try:
            result = response.json()
            print(f"  ✅ JSON 解析成功")
            print(f"  响应结构: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 检查响应状态
            if result.get('header', {}).get('status') == 0:
                body = result.get('body', {})
                source = body.get('source', {})
                table = source.get('table', {})
                rows = table.get('rows', [])
                cols = table.get('cols', [])
                page_info = table.get('page', {})
                
                print(f"\n🎉 合同 API 调用成功！")
                print(f"  合同总数: {len(rows)}")
                print(f"  分页信息: {page_info}")
                
                if rows:
                    print(f"\n📋 合同列表 (共 {len(rows)} 个):")
                    print("=" * 70)
                    
                    # 显示列信息
                    print(f"\n📊 列信息:")
                    for col in cols:
                        print(f"  {col['id']}: {col.get('dbtype', 'unknown')}")
                    
                    # 显示合同数据
                    for i, row in enumerate(rows, 1):
                        print(f"\n合同 {i}:")
                        for j, value in enumerate(row):
                            if j < len(cols):
                                col_name = cols[j]['id']
                                print(f"  {col_name}: {value}")
                    
                    print("\n" + "=" * 70)
                    print(f"✅ 成功获取 {len(rows)} 个合同")
                    
                else:
                    print(f"  ⚠️  没有合同数据，但 API 调用成功")
                    
            else:
                print(f"  ❌ API 调用失败: {result.get('header', {}).get('message')}")
                
        except json.JSONDecodeError as e:
            print(f"  ❌ JSON 解析失败: {e}")
            print(f"  原始响应: {response.text[:500]}...")
            
    except Exception as e:
        print(f"  ❌ API 调用异常: {e}")
    
    print(f"\n💡 测试完成")


if __name__ == "__main__":
    test_contract_api_final()

