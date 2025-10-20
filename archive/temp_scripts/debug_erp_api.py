#!/usr/bin/env python3
"""
调试智邦 ERP API 调用
查看完整的请求和响应数据
"""

import json
import requests
import os

def debug_erp_api():
    """调试 ERP API 调用"""
    print("\n" + "=" * 70)
    print("🔍 调试智邦 ERP API 调用")
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
    
    print(f"  登录请求: {login_url}")
    print(f"  登录数据: {json.dumps(login_data, ensure_ascii=False, indent=2)}")
    
    try:
        login_response = requests.post(
            login_url,
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"  登录响应状态: {login_response.status_code}")
        login_result = login_response.json()
        print(f"  登录响应: {json.dumps(login_result, ensure_ascii=False, indent=2)}")
        
        if login_result.get('header', {}).get('status') == 0:
            # session 在 header 中，不在 data 中
            session_token = login_result.get('header', {}).get('session')
            print(f"  ✅ 登录成功，获取到 session: {session_token}")
        else:
            print(f"  ❌ 登录失败")
            return
            
    except Exception as e:
        print(f"  ❌ 登录异常: {e}")
        return
    
    # 步骤 2: 调用客户列表 API
    print(f"\n📝 步骤 2: 调用客户列表 API...")
    
    # 按照您提供的参考代码构建请求
    dats = {
        "datatype": "",      # 列表模式
        "stype": "",         # 数据模式
        "remind": 0,         # 提醒类型
        "tjly": "",          # 统计来源
        "tdate1": "",        # 领用开始日期
        "tdate2": "",        # 领用结束日期
        "checktype": "",     # 关联客户选择模式
        "telsort": "",       # 客户分类
        "Ismode": "",        # 供应商总览标识
        "a_cateid": "",      # 销售人员
        "khjz": "",          # 客户价值评估
        "khhy": "",          # 客户行业
        "khly": "",          # 客户来源
        "a_date_0": "",      # 添加开始日期
        "a_date_1": "",      # 添加结束日期
        "telord": "",        # 客户id
        "name": "",          # 客户名称
        "pym": "",           # 拼音码
        "khid": "",          # 客户编号
        "phone": "",         # 办公电话
        "fax": "",           # 传真
        "url": "",           # 客户网址
        "catetype": 0,       # 人员类型
        "cateid": "",        # 人员选择
        "ly": "",            # 客户来源
        "jz": "",            # 价值评估
        "area": "",          # 客户区域
        "trade": "",         # 客户行业
        "address": "",       # 客户地址
        "zip": "",           # 邮编
        "intro": "",         # 备注
        "date1_0": "",       # 添加时间
        "date1_1": "",       # 添加时间
        "searchKey": "",     # 快速检索条件
        "pagesize": 20,      # 每页记录数
        "pageindex": 1,      # 数据页标
        "_rpt_sort": ""      # 排序字段
    }
    
    # 转换为 id-val 键值对数组格式
    datas = [{"id": key, "val": value} for key, value in dats.items()]
    
    json_data = {
        "session": session_token,
        "cmdkey": "refresh",
        "datas": datas
    }
    
    url = f"{base_url}/sysa/mobilephone/salesmanage/custom/list.asp"
    
    print(f"  客户列表请求: {url}")
    print(f"  请求数据: {json.dumps(json_data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            url,
            json=json_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"  响应状态: {response.status_code}")
        result = response.json()
        print(f"  完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 解析结果
        if result.get('header', {}).get('status') == 0:
            table_data = result.get('data', {}).get('table', {})
            rows = table_data.get('rows', [])
            print(f"\n✅ 成功获取到 {len(rows)} 个客户")
            
            if rows:
                print(f"\n📋 客户数据示例:")
                for i, customer in enumerate(rows[:3], 1):  # 只显示前3个
                    print(f"  客户 {i}:")
                    for key, value in customer.items():
                        print(f"    {key}: {value}")
            else:
                print(f"\n⚠️  没有客户数据，但 API 调用成功")
        else:
            print(f"\n❌ API 调用失败")
            
    except Exception as e:
        print(f"  ❌ API 调用异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_erp_api()
