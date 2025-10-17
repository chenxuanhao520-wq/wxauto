#!/usr/bin/env python3
"""
飞书多维表格集成
实现客户信息与飞书表格的自动同步
"""

# 强制 UTF-8 编码
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

class FeishuBitableClient:
    """飞书多维表格客户端"""
    
    def __init__(self, app_id: str = None, app_secret: str = None):
        """
        初始化飞书客户端
        
        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
        """
        self.app_id = app_id or os.getenv('FEISHU_APP_ID')
        self.app_secret = app_secret or os.getenv('FEISHU_APP_SECRET')
        self.base_url = "https://open.feishu.cn/open-apis"
        
        self.access_token = None
        self.token_expires_at = 0
        
        if not self.app_id or not self.app_secret:
            print("警告: 飞书 App ID 或 App Secret 未配置")
    
    def _get_access_token(self) -> str:
        """获取访问令牌"""
        # 检查令牌是否过期
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        # 获取新令牌
        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, json=payload)
            data = response.json()
            
            if data.get('code') == 0:
                self.access_token = data['tenant_access_token']
                # 提前5分钟刷新令牌
                self.token_expires_at = time.time() + data['expire'] - 300
                return self.access_token
            else:
                print(f"获取飞书访问令牌失败: {data.get('msg')}")
                return None
                
        except Exception as e:
            print(f"获取飞书访问令牌异常: {e}")
            return None
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """发送API请求"""
        token = self._get_access_token()
        if not token:
            return None
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.request(method, url, headers=headers, **kwargs)
            data = response.json()
            
            if data.get('code') == 0:
                return data.get('data')
            else:
                print(f"飞书API请求失败: {data.get('msg')}")
                return None
                
        except Exception as e:
            print(f"飞书API请求异常: {e}")
            return None
    
    def get_records(self, app_token: str, table_id: str, 
                   view_id: str = None, page_size: int = 100) -> List[Dict]:
        """
        获取表格记录
        
        Args:
            app_token: 多维表格 Token
            table_id: 表格 ID
            view_id: 视图 ID（可选）
            page_size: 每页记录数
            
        Returns:
            记录列表
        """
        endpoint = f"/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        params = {"page_size": page_size}
        
        if view_id:
            params['view_id'] = view_id
        
        all_records = []
        has_more = True
        page_token = None
        
        while has_more:
            if page_token:
                params['page_token'] = page_token
            
            data = self._make_request('GET', endpoint, params=params)
            if not data:
                break
            
            records = data.get('items', [])
            all_records.extend(records)
            
            has_more = data.get('has_more', False)
            page_token = data.get('page_token')
        
        return all_records
    
    def add_record(self, app_token: str, table_id: str, fields: Dict) -> Optional[Dict]:
        """
        添加记录
        
        Args:
            app_token: 多维表格 Token
            table_id: 表格 ID
            fields: 字段数据
            
        Returns:
            新记录信息
        """
        endpoint = f"/bitable/v1/apps/{app_token}/tables/{table_id}/records"
        payload = {"fields": fields}
        
        return self._make_request('POST', endpoint, json=payload)
    
    def update_record(self, app_token: str, table_id: str, 
                     record_id: str, fields: Dict) -> Optional[Dict]:
        """
        更新记录
        
        Args:
            app_token: 多维表格 Token
            table_id: 表格 ID
            record_id: 记录 ID
            fields: 字段数据
            
        Returns:
            更新后的记录信息
        """
        endpoint = f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}"
        payload = {"fields": fields}
        
        return self._make_request('PUT', endpoint, json=payload)
    
    def batch_update_records(self, app_token: str, table_id: str, 
                           records: List[Dict]) -> Optional[Dict]:
        """
        批量更新记录
        
        Args:
            app_token: 多维表格 Token
            table_id: 表格 ID
            records: 记录列表，每个记录包含 record_id 和 fields
            
        Returns:
            更新结果
        """
        endpoint = f"/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update"
        payload = {"records": records}
        
        return self._make_request('POST', endpoint, json=payload)
    
    def search_records(self, app_token: str, table_id: str, 
                      field_name: str, field_value: str) -> List[Dict]:
        """
        搜索记录
        
        Args:
            app_token: 多维表格 Token
            table_id: 表格 ID
            field_name: 字段名
            field_value: 字段值
            
        Returns:
            匹配的记录列表
        """
        all_records = self.get_records(app_token, table_id)
        
        matching_records = []
        for record in all_records:
            fields = record.get('fields', {})
            if fields.get(field_name) == field_value:
                matching_records.append(record)
        
        return matching_records

class CustomerBitableSync:
    """客户信息与飞书表格同步"""
    
    def __init__(self, client: FeishuBitableClient):
        self.client = client
        self.app_token = os.getenv('FEISHU_BITABLE_TOKEN')
        self.table_id = os.getenv('FEISHU_TABLE_ID')
        
        if not self.app_token or not self.table_id:
            print("警告: 飞书多维表格 Token 或 Table ID 未配置")
    
    def sync_customers_from_feishu(self) -> List[Dict]:
        """
        从飞书同步客户信息
        
        Returns:
            客户信息列表
        """
        if not self.app_token or not self.table_id:
            print("飞书表格未配置，跳过同步")
            return []
        
        try:
            records = self.client.get_records(self.app_token, self.table_id)
            
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
            
            print(f"从飞书同步了 {len(customers)} 个客户")
            return customers
            
        except Exception as e:
            print(f"从飞书同步客户失败: {e}")
            return []
    
    def sync_customer_to_feishu(self, customer_data: Dict) -> bool:
        """
        同步客户信息到飞书
        
        Args:
            customer_data: 客户数据
            
        Returns:
            是否成功
        """
        if not self.app_token or not self.table_id:
            return False
        
        try:
            # 检查客户是否已存在
            existing_records = self.client.search_records(
                self.app_token, self.table_id,
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
                    self.app_token, self.table_id, record_id, fields
                )
                print(f"更新飞书记录: {customer_data.get('customer_id')}")
            else:
                # 添加新记录
                result = self.client.add_record(
                    self.app_token, self.table_id, fields
                )
                print(f"添加飞书记录: {customer_data.get('customer_id')}")
            
            return result is not None
            
        except Exception as e:
            print(f"同步客户到飞书失败: {e}")
            return False
    
    def batch_sync_to_feishu(self, customers: List[Dict]) -> Dict[str, int]:
        """
        批量同步客户到飞书
        
        Args:
            customers: 客户列表
            
        Returns:
            同步统计信息
        """
        stats = {'success': 0, 'failed': 0}
        
        for customer in customers:
            if self.sync_customer_to_feishu(customer):
                stats['success'] += 1
            else:
                stats['failed'] += 1
            
            # 避免API频率限制
            time.sleep(0.1)
        
        return stats

# 全局实例
feishu_client = FeishuBitableClient()
feishu_sync = CustomerBitableSync(feishu_client)

if __name__ == "__main__":
    # 测试飞书集成
    print("🧪 测试飞书多维表格集成...")
    
    # 测试连接
    token = feishu_client._get_access_token()
    if token:
        print(f"✅ 飞书访问令牌获取成功: {token[:20]}...")
        
        # 测试同步
        customers = feishu_sync.sync_customers_from_feishu()
        print(f"📊 同步了 {len(customers)} 个客户")
        
        for customer in customers[:3]:  # 显示前3个
            print(f"   {customer.get('customer_id')}: {customer.get('name')}")
    else:
        print("❌ 飞书访问令牌获取失败")