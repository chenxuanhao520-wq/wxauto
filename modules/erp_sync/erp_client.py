"""
ERP API客户端
封装智邦国际ERP的API调用
"""

import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from modules.storage.db import Database

logger = logging.getLogger(__name__)


class ERPClient:
    """智邦国际ERP API客户端"""
    
    def __init__(self, base_url: str, username: str = None, password: str = None):
        """
        初始化ERP客户端
        
        Args:
            base_url: ERP基础URL，如 http://ls1.jmt.ink:46088
            username: 用户名
            password: 密码
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session_token = None
        self.session_expires_at = None
        
    def login(self) -> bool:
        """
        登录ERP系统获取session token
        
        Returns:
            bool: 登录是否成功
        """
        try:
            url = f"{self.base_url}/webapi/v3/ov1/login"
            
            datas = [
                {"id": "user", "val": f"txt:{self.username}"},
                {"id": "password", "val": f"txt:{self.password}"},
                {"id": "serialnum", "val": "wxauto_erp_sync_001"}
            ]
            
            response = requests.post(
                url,
                json={"datas": datas},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            self._log_api_call(
                endpoint='/webapi/v3/ov1/login',
                method='POST',
                params={"user": self.username},
                response=response
            )
            
            result = response.json()
            
            if result.get('header', {}).get('status') == 0:
                self.session_token = result['header']['session']
                logger.info(f"[ERP] 登录成功，session: {self.session_token[:20]}...")
                return True
            else:
                logger.error(f"[ERP] 登录失败: {result.get('header', {}).get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"[ERP] 登录异常: {e}")
            return False
    
    def logout(self) -> bool:
        """退出ERP系统"""
        try:
            url = f"{self.base_url}/sysa/mobilephone/logout.asp"
            response = requests.post(
                url,
                json={"session": self.session_token, "datas": []},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            self._log_api_call('/sysa/mobilephone/logout.asp', 'POST', {}, response)
            
            self.session_token = None
            logger.info("[ERP] 已退出登录")
            return True
            
        except Exception as e:
            logger.error(f"[ERP] 退出登录异常: {e}")
            return False
    
    def ensure_logged_in(self) -> bool:
        """确保已登录，如果未登录则自动登录"""
        if self.session_token:
            return True
        return self.login()
    
    def get_customers(self, updated_after: datetime = None, page_size: int = 100, 
                     page_index: int = 1) -> List[Dict]:
        """
        获取ERP客户列表
        
        Args:
            updated_after: 获取此时间之后更新的客户（增量同步）
            page_size: 每页数量
            page_index: 页码（从1开始）
            
        Returns:
            List[Dict]: 客户列表
        """
        if not self.ensure_logged_in():
            raise Exception("ERP未登录")
        
        try:
            url = f"{self.base_url}/sysa/mobilephone/salesmanage/custom/list.asp"
            
            datas = [
                {"id": "pagesize", "val": page_size},
                {"id": "pageindex", "val": page_index}
            ]
            
            # 如果指定了更新时间，添加筛选条件
            if updated_after:
                datas.append({
                    "id": "date1_0", 
                    "val": updated_after.strftime("%Y-%m-%d")
                })
            
            response = requests.post(
                url,
                json={
                    "session": self.session_token,
                    "cmdkey": "refresh",
                    "datas": datas
                },
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            self._log_api_call(
                '/sysa/mobilephone/salesmanage/custom/list.asp',
                'POST',
                {"page_size": page_size, "page_index": page_index},
                response
            )
            
            result = response.json()
            
            if result.get('header', {}).get('status') == 0:
                # 解析表格数据
                table_data = result.get('data', {}).get('table', {})
                rows = table_data.get('rows', [])
                
                logger.info(f"[ERP] 获取到 {len(rows)} 个客户")
                return rows
            else:
                logger.error(f"[ERP] 获取客户列表失败: {result}")
                return []
                
        except Exception as e:
            logger.error(f"[ERP] 获取客户列表异常: {e}")
            return []
    
    def get_customer_detail(self, customer_id: int) -> Optional[Dict]:
        """
        获取客户详情
        
        Args:
            customer_id: ERP客户ID (ord)
            
        Returns:
            Dict: 客户详细信息
        """
        if not self.ensure_logged_in():
            raise Exception("ERP未登录")
        
        try:
            url = f"{self.base_url}/sysa/mobilephone/salesmanage/custom/add.asp?edit=1"
            
            datas = [
                {"id": "edit", "val": ""},
                {"id": "ord", "val": customer_id}
            ]
            
            response = requests.post(
                url,
                json={"session": self.session_token, "datas": datas},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            self._log_api_call(
                '/sysa/mobilephone/salesmanage/custom/add.asp?edit=1',
                'POST',
                {"customer_id": customer_id},
                response
            )
            
            result = response.json()
            
            if result.get('header', {}).get('status') == 0:
                return result.get('data', {})
            else:
                logger.error(f"[ERP] 获取客户详情失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"[ERP] 获取客户详情异常: {e}")
            return None
    
    def allocate_customer_id(self, customer_type: int = 1) -> Optional[int]:
        """
        分配新客户ID
        
        Args:
            customer_type: 客户类型 1=单位客户 2=个人客户
            
        Returns:
            int: 新分配的客户ID
        """
        if not self.ensure_logged_in():
            raise Exception("ERP未登录")
        
        try:
            url = f"{self.base_url}/sysa/mobilephone/salesmanage/custom/add.asp"
            
            datas = [
                {"id": "edit", "val": ""},
                {"id": "intsort", "val": str(customer_type)}
            ]
            
            response = requests.post(
                url,
                json={"session": self.session_token, "datas": datas},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            self._log_api_call(
                '/sysa/mobilephone/salesmanage/custom/add.asp',
                'POST',
                {"customer_type": customer_type},
                response
            )
            
            result = response.json()
            
            if result.get('header', {}).get('status') == 0:
                new_id = result.get('data', {}).get('value')
                logger.info(f"[ERP] 分配新客户ID: {new_id}")
                return int(new_id) if new_id else None
            else:
                logger.error(f"[ERP] 分配客户ID失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"[ERP] 分配客户ID异常: {e}")
            return None
    
    def create_customer(self, customer_data: Dict) -> Optional[int]:
        """
        在ERP中创建新客户
        
        Args:
            customer_data: 客户数据字典
            
        Returns:
            int: ERP客户ID
        """
        if not self.ensure_logged_in():
            raise Exception("ERP未登录")
        
        try:
            # 1. 分配新客户ID
            customer_type = customer_data.get('intsort', 1)
            new_id = self.allocate_customer_id(customer_type)
            
            if not new_id:
                logger.error("[ERP] 无法分配新客户ID")
                return None
            
            # 2. 保存客户信息
            url = f"{self.base_url}/sysa/mobilephone/salesmanage/custom/add.asp?intsort={customer_type}"
            
            # 准备数据
            customer_data['ord'] = new_id
            
            datas = [
                {"id": key, "val": value}
                for key, value in customer_data.items()
            ]
            
            response = requests.post(
                url,
                json={
                    "session": self.session_token,
                    "cmdkey": "__sys_dosave",
                    "datas": datas
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            self._log_api_call(
                f'/sysa/mobilephone/salesmanage/custom/add.asp?intsort={customer_type}',
                'POST',
                {"name": customer_data.get('name')},
                response
            )
            
            result = response.json()
            
            if result.get('header', {}).get('status') == 0:
                logger.info(f"[ERP] 创建客户成功: ID={new_id}, 名称={customer_data.get('name')}")
                return new_id
            else:
                logger.error(f"[ERP] 创建客户失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"[ERP] 创建客户异常: {e}")
            return None
    
    def update_customer(self, customer_id: int, updates: Dict) -> bool:
        """
        更新ERP客户信息
        
        Args:
            customer_id: ERP客户ID
            updates: 要更新的字段字典
            
        Returns:
            bool: 更新是否成功
        """
        if not self.ensure_logged_in():
            raise Exception("ERP未登录")
        
        try:
            # 先获取客户详情以确定客户类型
            detail = self.get_customer_detail(customer_id)
            if not detail:
                logger.error(f"[ERP] 找不到客户 ID={customer_id}")
                return False
            
            customer_type = detail.get('intsort', 1)
            
            url = f"{self.base_url}/sysa/mobilephone/salesmanage/custom/add.asp?intsort={customer_type}"
            
            updates['ord'] = customer_id
            
            datas = [
                {"id": key, "val": value}
                for key, value in updates.items()
            ]
            
            response = requests.post(
                url,
                json={
                    "session": self.session_token,
                    "cmdkey": "__sys_dosave",
                    "datas": datas
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            self._log_api_call(
                f'/sysa/mobilephone/salesmanage/custom/add.asp?intsort={customer_type}',
                'POST',
                {"customer_id": customer_id, "updates": list(updates.keys())},
                response
            )
            
            result = response.json()
            
            if result.get('header', {}).get('status') == 0:
                logger.info(f"[ERP] 更新客户成功: ID={customer_id}")
                return True
            else:
                logger.error(f"[ERP] 更新客户失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"[ERP] 更新客户异常: {e}")
            return False
    
    def create_followup(self, customer_id: int, followup_data: Dict) -> bool:
        """
        创建客户跟进记录
        
        Args:
            customer_id: ERP客户ID
            followup_data: 跟进记录数据
            
        Returns:
            bool: 创建是否成功
        """
        if not self.ensure_logged_in():
            raise Exception("ERP未登录")
        
        try:
            url = f"{self.base_url}/sysa/mobilephone/systemmanage/reply.asp?datatype=tel"
            
            followup_data['ord'] = customer_id
            
            datas = [
                {"id": key, "val": value}
                for key, value in followup_data.items()
            ]
            
            response = requests.post(
                url,
                json={
                    "session": self.session_token,
                    "cmdkey": "__sys_dosave",
                    "datas": datas
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            self._log_api_call(
                '/sysa/mobilephone/systemmanage/reply.asp?datatype=tel',
                'POST',
                {"customer_id": customer_id},
                response
            )
            
            result = response.json()
            
            if result.get('header', {}).get('status') == 0:
                logger.info(f"[ERP] 创建跟进记录成功: 客户ID={customer_id}")
                return True
            else:
                logger.error(f"[ERP] 创建跟进记录失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"[ERP] 创建跟进记录异常: {e}")
            return False
    
    def _log_api_call(self, endpoint: str, method: str, params: Dict, 
                     response: requests.Response):
        """记录API调用日志到数据库"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            response_time = response.elapsed.total_seconds() * 1000  # 毫秒
            
            cursor.execute('''
                INSERT INTO erp_api_logs
                (api_endpoint, http_method, request_params, response_status,
                 response_body, response_time_ms, is_success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                endpoint,
                method,
                json.dumps(params, ensure_ascii=False),
                response.status_code,
                response.text[:5000],  # 限制长度
                int(response_time),
                response.status_code == 200,
                None if response.status_code == 200 else response.text[:500]
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.warning(f"[ERP] 记录API日志失败: {e}")
    
    def __enter__(self):
        """上下文管理器：进入"""
        self.login()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器：退出"""
        self.logout()

