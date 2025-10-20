#!/usr/bin/env python3
"""
调试智邦 ERP 订单 API 调用
查看完整的请求和响应数据
"""

import json
import requests
import os

def debug_erp_order_api():
    """调试 ERP 订单 API 调用"""
    print("\n" + "=" * 70)
    print("🔍 调试智邦 ERP 订单 API 调用")
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
    
    # 步骤 2: 尝试不同的订单 API 接口
    order_apis = [
        "/sysa/mobilephone/salesmanage/order/list.asp",
        "/sysa/mobilephone/salesmanage/order.asp",
        "/sysa/mobilephone/systemmanage/order.asp?datatype=tel",
        "/sysa/mobilephone/salesmanage/order/list.asp?datatype=tel"
    ]
    
    for api_path in order_apis:
        print(f"\n📝 测试订单 API: {api_path}")
        
        try:
            url = f"{base_url}{api_path}"
            
            # 构建订单查询参数
            dats = {
                "datatype": "",      # 数据类型
                "stype": "",         # 状态类型
                "remind": 0,         # 提醒类型
                "tjly": "",          # 统计来源
                "tdate1": "",        # 开始日期
                "tdate2": "",        # 结束日期
                "checktype": "",     # 选择模式
                "telsort": "",       # 订单分类
                "Ismode": "",        # 模式标识
                "a_cateid": "",      # 销售人员
                "telord": "",        # 客户ID
                "name": "",          # 订单名称
                "pym": "",           # 拼音码
                "khid": "",          # 客户编号
                "phone": "",         # 电话
                "fax": "",           # 传真
                "url": "",           # 网址
                "catetype": 0,       # 人员类型
                "cateid": "",        # 人员选择
                "ly": "",            # 来源
                "jz": "",            # 价值评估
                "area": "",          # 区域
                "trade": "",         # 行业
                "address": "",       # 地址
                "zip": "",           # 邮编
                "intro": "",         # 备注
                "date1_0": "",       # 开始时间
                "date1_1": "",       # 结束时间
                "searchKey": "",     # 搜索关键字
                "pagesize": 10,      # 每页记录数
                "pageindex": 1,      # 页码
                "_rpt_sort": ""      # 排序字段
            }
            
            # 转换为 id-val 键值对数组格式
            datas = [{"id": key, "val": value} for key, value in dats.items()]
            
            json_data = {
                "session": session_token,
                "cmdkey": "refresh",
                "datas": datas
            }
            
            print(f"  请求数据: {json.dumps(json_data, ensure_ascii=False, indent=2)[:500]}...")
            
            response = requests.post(
                url,
                json=json_data,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            print(f"  响应状态: {response.status_code}")
            print(f"  响应头: {dict(response.headers)}")
            
            # 尝试解析响应
            try:
                result = response.json()
                print(f"  ✅ JSON 解析成功")
                print(f"  响应内容: {json.dumps(result, ensure_ascii=False, indent=2)[:1000]}...")
                
                # 检查是否有订单数据
                if result.get('header', {}).get('status') == 0:
                    body = result.get('body', {})
                    source = body.get('source', {})
                    table = source.get('table', {})
                    rows = table.get('rows', [])
                    
                    if rows:
                        print(f"  🎉 找到 {len(rows)} 个订单！")
                        break
                    else:
                        print(f"  ⚠️  没有订单数据")
                else:
                    print(f"  ❌ API 调用失败: {result.get('header', {}).get('message')}")
                    
            except json.JSONDecodeError as e:
                print(f"  ❌ JSON 解析失败: {e}")
                print(f"  原始响应: {response.text[:500]}...")
                
        except Exception as e:
            print(f"  ❌ API 调用异常: {e}")
    
    print(f"\n💡 调试完成")


if __name__ == "__main__":
    debug_erp_order_api()
