#!/usr/bin/env python3
"""
钉钉多维表格集成
实现客户信息与钉钉表格的自动同步
"""

# 强制 UTF-8 编码
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

class DingtalkBitableClient:
    """钉钉多维表格客户端"""
    
    def __init__(self, app_key: str = None, app_secret: str = None):
        """
        初始化钉钉客户端
        
        Args:
            app_key: 钉钉应用 Key
            app_secret: 钉钉应用密钥
        """
        self.app_key = app_key or os.getenv('DINGTALK_APP_KEY')
        self.app_secret = app_secret or os.getenv('DINGTALK_APP_SECRET')
        self.base_url = "https://oapi.dingtalk.com"
        
        self.access_token = None
        self.token_expires_at = 0
        
        if not self.app_key or not self.app_secret:
            print("警告: 钉钉 App Key 或 App Secret 未配置")
    
    def _get_access_token(self) -> str:
        """获取访问令牌"""
        # 检查令牌是否过期
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        # 获取新令牌
        url = f"{self.base_url}/gettoken"
        params = {
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('errcode') == 0:
                self.access_token = data['access_token']
                # 提前5分钟刷新令牌
                self.token_expires_at = time.time() + data.get('expires_in', 7200) - 300
                return self.access_token
            else:
                print(f"获取钉钉访问令牌失败: {data.get('errmsg')}")
                return None
                
        except Exception as e:
            print(f"获取钉钉访问令牌异常: {e}")
            return None
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """发送API请求"""
        token = self._get_access_token()
        if not token:
            return None
        
        url = f"{self.base_url}{endpoint}"
        params = kwargs.get('params', {})
        params['access_token'] = token
        kwargs['params'] = params
        
        try:
            response = requests.request(method, url, **kwargs)
            data = response.json()
            
            if data.get('errcode') == 0:
                return data
            else:
                print(f"钉钉API请求失败: {data.get('errmsg')}")
                return None
                
        except Exception as e:
            print(f"钉钉API请求异常: {e}")
            return None
    
    def get_records(self, base_id: str, table_id: str, 
                   page_size: int = 100) -> List[Dict]:
        """
        获取表格记录
        
        Args:
            base_id: Base ID
            table_id: 表格 ID
            page_size: 每页记录数
            
        Returns:
            记录列表
        """
        endpoint = "/topapi/aitable/record/list"
        
        all_records = []
        page_num = 1
        has_more = True
        
        while has_more:
            payload = {
                "base_id": base_id,
                "table_id": table_id,
                "page_size": page_size,
                "page_num": page_num
            }
            
            data = self._make_request('POST', endpoint, json=payload)
            if not data:
                break
            
            result = data.get('result', {})
            records = result.get('records', [])
            all_records.extend(records)
            
            total = result.get('total', 0)
            has_more = len(all_records) < total
            page_num += 1
        
        return all_records
    
    def add_record(self, base_id: str, table_id: str, fields: Dict) -> Optional[Dict]:
        """
        添加记录
        
        Args:
            base_id: Base ID
            table_id: 表格 ID
            fields: 字段数据
            
        Returns:
            新记录信息
        """
        endpoint = "/topapi/aitable/record/create"
        payload = {
            "base_id": base_id,
            "table_id": table_id,
            "fields": fields
        }
        
        return self._make_request('POST', endpoint, json=payload)
    
    def update_record(self, base_id: str, table_id: str, 
                     record_id: str, fields: Dict) -> Optional[Dict]:
        """
        更新记录
        
        Args:
            base_id: Base ID
            table_id: 表格 ID
            record_id: 记录 ID
            fields: 字段数据
            
        Returns:
            更新后的记录信息
        """
        endpoint = "/topapi/aitable/record/update"
        payload = {
            "base_id": base_id,
            "table_id": table_id,
            "record_id": record_id,
            "fields": fields
        }
        
        return self._make_request('POST', endpoint, json=payload)
    
    def search_records(self, base_id: str, table_id: str, 
                      field_name: str, field_value: str) -> List[Dict]:
        """
        搜索记录
        
        Args:
            base_id: Base ID
            table_id: 表格 ID
            field_name: 字段名
            field_value: 字段值
            
        Returns:
            匹配的记录列表
        """
        all_records = self.get_records(base_id, table_id)
        
        matching_records = []
        for record in all_records:
            fields = record.get('fields', {})
            if fields.get(field_name) == field_value:
                matching_records.append(record)
        
        return matching_records

class CustomerDingtalkSync:
    """客户信息与钉钉表格同步"""
    
    def __init__(self, client: DingtalkBitableClient):
        self.client = client
        self.base_id = os.getenv('DINGTALK_BASE_ID')
        self.table_id = os.getenv('DINGTALK_TABLE_ID')
        
        if not self.base_id or not self.table_id:
            print("警告: 钉钉 Base ID 或 Table ID 未配置")
    
    def sync_customers_from_dingtalk(self) -> List[Dict]:
        """
        从钉钉同步客户信息
        
        Returns:
            客户信息列表
        """
        if not self.base_id or not self.table_id:
            print("钉钉表格未配置，跳过同步")
            return []
        
        try:
            records = self.client.get_records(self.base_id, self.table_id)
            
            customers = []
            for record in records:
                fields = record.get('fields', {})
                
                # 提取客户信息（根据实际表格字段调整）
                customer = {
                    'record_id': record.get('record_id'),
                    'customer_id': fields.get('客户编号') or fields.get('编号'),
                    'name': fields.get('姓名') or fields.get('客户名称'),
                    'group_name': fields.get('群聊名称') or fields.get('所属群聊'),
                    'wechat_remark': fields.get('微信备注'),
                    'priority': fields.get('优先级', 3),
                    'notes': fields.get('备注', ''),
                    'phone': fields.get('电话'),
                    'email': fields.get('邮箱'),
                    'tags': fields.get('标签', [])
                }
                
                # 过滤掉必填字段为空的记录
                if customer['customer_id'] and customer['name']:
                    customers.append(customer)
            
            print(f"从钉钉同步了 {len(customers)} 个客户")
            return customers
            
        except Exception as e:
            print(f"从钉钉同步客户失败: {e}")
            return []
    
    def sync_customer_to_dingtalk(self, customer_data: Dict) -> bool:
        """
        同步客户信息到钉钉
        
        Args:
            customer_data: 客户数据
            
        Returns:
            是否成功
        """
        if not self.base_id or not self.table_id:
            return False
        
        try:
            # 检查客户是否已存在
            existing_records = self.client.search_records(
                self.base_id, self.table_id,
                '客户编号', customer_data.get('customer_id')
            )
            
            # 构建字段数据
            fields = {
                '客户编号': customer_data.get('customer_id'),
                '姓名': customer_data.get('name'),
                '群聊名称': customer_data.get('group_name'),
                '微信备注': customer_data.get('wechat_remark', customer_data.get('name')),
                '优先级': customer_data.get('priority', 3),
                '备注': customer_data.get('notes', ''),
                '总问题数': customer_data.get('total_questions', 0),
                '已解决': customer_data.get('solved_questions', 0),
                '转人工次数': customer_data.get('handoff_count', 0),
                '最后活跃': customer_data.get('last_active'),
                '同步时间': datetime.now().isoformat()
            }
            
            if existing_records:
                # 更新现有记录
                record_id = existing_records[0]['record_id']
                result = self.client.update_record(
                    self.base_id, self.table_id, record_id, fields
                )
                print(f"更新钉钉记录: {customer_data.get('customer_id')}")
            else:
                # 添加新记录
                result = self.client.add_record(
                    self.base_id, self.table_id, fields
                )
                print(f"添加钉钉记录: {customer_data.get('customer_id')}")
            
            return result is not None
            
        except Exception as e:
            print(f"同步客户到钉钉失败: {e}")
            return False
    
    def batch_sync_to_dingtalk(self, customers: List[Dict]) -> Dict[str, int]:
        """
        批量同步客户到钉钉
        
        Args:
            customers: 客户列表
            
        Returns:
            同步统计信息
        """
        stats = {'success': 0, 'failed': 0}
        
        for customer in customers:
            if self.sync_customer_to_dingtalk(customer):
                stats['success'] += 1
            else:
                stats['failed'] += 1
            
            # 避免API频率限制
            time.sleep(0.1)
        
        return stats

# 全局实例
dingtalk_client = DingtalkBitableClient()
dingtalk_sync = CustomerDingtalkSync(dingtalk_client)

if __name__ == "__main__":
    # 测试钉钉集成
    print("🧪 测试钉钉多维表格集成...")
    
    # 测试连接
    token = dingtalk_client._get_access_token()
    if token:
        print(f"✅ 钉钉访问令牌获取成功: {token[:20]}...")
        
        # 测试同步
        customers = dingtalk_sync.sync_customers_from_dingtalk()
        print(f"📊 同步了 {len(customers)} 个客户")
        
        for customer in customers[:3]:  # 显示前3个
            print(f"   {customer.get('customer_id')}: {customer.get('name')}")
    else:
        print("❌ 钉钉访问令牌获取失败")