#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智邦国际ERP API Python客户端 (增强版)
提供完整的客户管理、联系人管理、跟进记录等功能
"""

import requests
import random
import string
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from functools import wraps
import time

logger = logging.getLogger(__name__)


class ERPAPIException(Exception):
    """ERP API异常基类"""
    pass


class AuthenticationError(ERPAPIException):
    """认证失败异常"""
    pass


class BusinessError(ERPAPIException):
    """业务逻辑异常"""
    pass


class ZhibangERPClient:
    """智邦ERP API客户端 (增强版)"""
    
    def __init__(self, base_url: str, username: str = None, password: str = None, 
                 auto_login: bool = True, max_retries: int = 3):
        """
        初始化ERP客户端
        
        Args:
            base_url: ERP系统地址，如 http://ls1.jmt.ink:46088
            username: 用户名
            password: 密码
            auto_login: 是否自动登录
            max_retries: 最大重试次数
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = None
        self.session_expire = None
        self.max_retries = max_retries
        
        if auto_login and username and password:
            self.login()
    
    def _ensure_session(func):
        """装饰器：确保session有效"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.session or (self.session_expire and datetime.now() >= self.session_expire):
                logger.info("Session已过期或不存在，重新登录...")
                self.login()
            return func(self, *args, **kwargs)
        return wrapper
    
    def _retry_on_auth_error(func):
        """装饰器：认证错误时自动重试"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            for attempt in range(self.max_retries):
                try:
                    return func(self, *args, **kwargs)
                except AuthenticationError:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"认证失败，重新登录... (尝试 {attempt + 1}/{self.max_retries})")
                        self.login()
                    else:
                        raise
        return wrapper
    
    def login(self, username: str = None, password: str = None) -> Dict[str, Any]:
        """
        系统登录
        
        Args:
            username: 用户名（可选，使用初始化时的用户名）
            password: 密码（可选，使用初始化时的密码）
        
        Returns:
            登录响应结果
        
        Raises:
            AuthenticationError: 登录失败
        """
        username = username or self.username
        password = password or self.password
        
        if not username or not password:
            raise AuthenticationError("用户名和密码不能为空")
        
        # 生成随机串号
        serialnum = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        
        url = f"{self.base_url}/webapi/v3/ov1/login"
        payload = {
            "datas": [
                {"id": "user", "val": f"txt:{username}"},
                {"id": "password", "val": f"txt:{password}"},
                {"id": "serialnum", "val": f"txt:{serialnum}"}
            ]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            
            if result.get("header", {}).get("status") == 0:
                self.session = result["header"]["session"]
                self.session_expire = datetime.now() + timedelta(hours=2)
                logger.info(f"登录成功，Session: {self.session[:20]}...")
                return result
            else:
                error_msg = result.get("header", {}).get("message", "未知错误")
                raise AuthenticationError(f"登录失败: {error_msg}")
        
        except requests.RequestException as e:
            raise ERPAPIException(f"网络请求失败: {str(e)}")
    
    def _request(self, url: str, data: Dict[str, Any] = None, 
                 cmdkey: str = None, use_full_url: bool = False) -> Dict[str, Any]:
        """
        内部请求方法
        
        Args:
            url: 接口URL（相对路径或完整URL）
            data: 请求数据字典
            cmdkey: 命令键（如 __sys_dosave, refresh）
            use_full_url: 是否使用完整URL
        
        Returns:
            响应结果
        
        Raises:
            AuthenticationError: 认证失败
            BusinessError: 业务错误
            ERPAPIException: 其他错误
        """
        if not use_full_url:
            url = f"{self.base_url}{url}" if url.startswith('/') else url
        
        # 构建请求payload
        payload = {"session": self.session}
        
        if cmdkey:
            payload["cmdkey"] = cmdkey
        
        if data:
            payload["datas"] = [{"id": k, "val": v} for k, v in data.items()]
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            result = response.json()
            
            # 检查认证错误
            if result.get('Code') == 400:
                raise AuthenticationError("Token验证失败")
            
            # 检查业务错误
            if result.get('Code') == 300:
                error_msg = result.get('Msg', '未知错误')
                raise BusinessError(f"业务错误: {error_msg}")
            
            return result
        
        except requests.RequestException as e:
            raise ERPAPIException(f"网络请求失败: {str(e)}")
    
    # ==================== 客户管理 API ====================
    
    @_ensure_session
    @_retry_on_auth_error
    def get_new_customer_id(self, customer_type: str = '1') -> str:
        """
        分配新客户ID
        
        Args:
            customer_type: 客户类型，'1'=单位客户，'2'=个人客户
        
        Returns:
            新客户的ID (ord值)
        """
        url = "/sysa/mobilephone/salesmanage/custom/add.asp"
        data = {"intsort": customer_type}
        
        result = self._request(url, data)
        return result.get('value', '')
    
    @_ensure_session
    @_retry_on_auth_error
    def add_company_customer(self, **kwargs) -> Dict[str, Any]:
        """
        添加单位客户
        
        必填参数:
            ord: 客户ID（通过get_new_customer_id获取）
            name: 客户名称
            sort1: 客户分类
            person_name: 联系人姓名
        
        可选参数:
            khid: 客户编号
            ly: 客户来源 (171=网站注册，可代表微信)
            mobile: 手机
            weixinAcc: 微信号
            address: 地址
            jz: 价值评估 (175=很高,289=较高,176=一般,177=较低,290=很低)
            intro: 备注
            product: 客户简介
            ... (详见API文档)
        
        Returns:
            操作结果
        """
        url = "/sysa/mobilephone/salesmanage/custom/add.asp?intsort=1"
        return self._request(url, kwargs, cmdkey="__sys_dosave")
    
    @_ensure_session
    @_retry_on_auth_error
    def add_personal_customer(self, **kwargs) -> Dict[str, Any]:
        """
        添加个人客户
        
        必填参数:
            ord: 客户ID（通过get_new_customer_id获取）
            name: 客户名称
            sort1: 客户分类
        
        可选参数:
            khid: 客户编号
            ly: 客户来源
            mobile: 手机
            weixinAcc: 微信号
            address: 地址
            jz: 价值评估
            intro: 备注
            ... (详见API文档)
        
        Returns:
            操作结果
        """
        url = "/sysa/mobilephone/salesmanage/custom/add.asp?intsort=2"
        return self._request(url, kwargs, cmdkey="__sys_dosave")
    
    @_ensure_session
    @_retry_on_auth_error
    def get_customer_list(self, page_size: int = 20, page_index: int = 1, 
                         filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        获取客户列表
        
        Args:
            page_size: 每页记录数
            page_index: 页码（从1开始）
            filters: 筛选条件，如：
                - name: 客户名称（模糊查询）
                - khid: 客户编号
                - ly: 客户来源
                - mobile: 手机号
                - ... (详见API文档)
        
        Returns:
            客户列表
        """
        url = "/sysa/mobilephone/salesmanage/custom/list.asp"
        
        data = {
            "pagesize": page_size,
            "pageindex": page_index
        }
        
        if filters:
            data.update(filters)
        
        result = self._request(url, data, cmdkey="refresh")
        
        # 解析返回结果
        rows = result.get('source', {}).get('table', {}).get('rows', [])
        return rows
    
    @_ensure_session
    @_retry_on_auth_error
    def get_customer_detail(self, customer_id: int, customer_type: str = '1') -> Dict[str, Any]:
        """
        获取客户详情
        
        Args:
            customer_id: 客户ID (ord)
            customer_type: 客户类型，'1'=单位，'2'=个人
        
        Returns:
            客户详细信息
        """
        url = "/sysa/mobilephone/salesmanage/custom/add.asp?edit=1"
        data = {
            "ord": customer_id,
            "intsort": customer_type,
            "edit": "1"
        }
        
        return self._request(url, data)
    
    @_ensure_session
    @_retry_on_auth_error
    def update_customer(self, **kwargs) -> Dict[str, Any]:
        """
        修改客户信息
        
        必填参数:
            ord: 客户ID
            name: 客户名称
            khid: 客户编号
        
        可选参数:
            与add_company_customer相同
        
        Returns:
            操作结果
        """
        url = "/webapi/v3/sales/customer/edit"
        return self._request(url, kwargs)
    
    @_ensure_session
    @_retry_on_auth_error
    def assign_customer(self, customer_id: int, assign_type: int = 1, 
                       user_ids: str = "") -> Dict[str, Any]:
        """
        指派客户
        
        Args:
            customer_id: 客户ID
            assign_type: 指派方式，1=对所有用户公开，0=指派给特定用户
            user_ids: 指派用户ID（多个用逗号分隔）
        
        Returns:
            操作结果
        """
        url = "/sysa/mobilephone/systemmanage/order.asp?datatype=tel"
        data = {
            "ord": customer_id,
            "member1": assign_type,
            "member2": user_ids
        }
        
        return self._request(url, data, cmdkey="__sys_dosave")
    
    @_ensure_session
    @_retry_on_auth_error
    def add_followup_record(self, customer_id: int, template_id: int = 120, 
                           content: str = "") -> Dict[str, Any]:
        """
        添加跟进记录（洽谈进展）
        
        Args:
            customer_id: 客户ID
            template_id: 模板ID
                - 106: 谈的很好，让发合同
                - 107: 电话无人接听
                - 108: 现在还没考虑
                - 109: 今天谈的不错，让明天面谈
                - 120: 正在考虑中
            content: 详细内容
        
        Returns:
            操作结果
        """
        url = "/sysa/mobilephone/systemmanage/reply.asp?datatype=tel"
        data = {
            "ord": customer_id,
            "intro": template_id,
            "c1": content,
            "date1": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return self._request(url, data, cmdkey="__sys_dosave")
    
    # ==================== 联系人管理 API ====================
    
    @_ensure_session
    @_retry_on_auth_error
    def add_contact_person(self, customer_id: int, **kwargs) -> Dict[str, Any]:
        """
        添加联系人
        
        必填参数:
            person_name: 联系人姓名
        
        可选参数:
            mobile: 手机
            email: 电子邮件
            phone: 办公电话
            weixinAcc: 微信
            qq: QQ
            job: 职务
            part1: 部门
            intro: 备注
            ... (详见API文档)
        
        Returns:
            操作结果
        """
        url = "/sysa/mobilephone/salesmanage/person/add.asp"
        data = {"ord": customer_id}
        data.update(kwargs)
        
        return self._request(url, data, cmdkey="__sys_dosave")
    
    @_ensure_session
    @_retry_on_auth_error
    def get_contact_list(self, customer_id: int = None, 
                        filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        获取联系人列表
        
        Args:
            customer_id: 客户ID（可选，为空时获取所有联系人）
            filters: 筛选条件
        
        Returns:
            联系人列表
        """
        url = "/sysa/mobilephone/salesmanage/person/list.asp"
        
        data = {}
        if customer_id:
            data["telord"] = customer_id
        
        if filters:
            data.update(filters)
        
        result = self._request(url, data, cmdkey="refresh")
        rows = result.get('source', {}).get('table', {}).get('rows', [])
        return rows
    
    # ==================== 高级方法 ====================
    
    def sync_customer_from_wechat(self, contact: Dict[str, Any], 
                                  thread: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        从微信中台同步客户到ERP
        
        Args:
            contact: 微信中台客户数据
                - id: 中台客户ID
                - name: 客户名称
                - company: 公司名称（企业客户）
                - type: 客户类型 ('company'/'personal')
                - phone: 手机号
                - wechat_id: 微信号
                - address: 地址
                - email: 邮箱
                - ...
            
            thread: 对话线程数据（可选）
                - score: 评分
                - summary: 摘要
                - ...
        
        Returns:
            同步结果
        """
        # 1. 检查客户是否已存在
        existing = self.find_customer_by_khid(f"WX{contact['id']}")
        if existing:
            logger.info(f"客户已存在 (khid=WX{contact['id']}), 跳过同步")
            return {'status': 'skipped', 'reason': 'already_exists', 'customer': existing}
        
        # 2. 分配新客户ID
        customer_type = '1' if contact.get('type') == 'company' else '2'
        ord = self.get_new_customer_id(customer_type)
        
        # 3. 映射字段
        customer_data = {
            "ord": ord,
            "name": contact.get('company') or contact.get('name'),
            "khid": f"WX{contact['id']}",
            "ly": 171,  # 网站注册（代表微信）
            "mobile": contact.get('phone', ''),
            "weixinAcc": contact.get('wechat_id', ''),
            "address": contact.get('address', ''),
            "sort1": "微信客户",  # 客户分类，需要根据实际情况调整
        }
        
        # 添加价值评估
        if thread and 'score' in thread:
            customer_data['jz'] = self._map_score_to_value(thread['score'])
        
        # 添加备注
        notes = []
        if thread and 'score' in thread:
            notes.append(f"评分: {thread['score']}")
        notes.append(f"来自微信中台，同步时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        customer_data['intro'] = '\n'.join(notes)
        
        # 添加客户简介
        if thread and 'summary' in thread:
            customer_data['product'] = thread['summary']
        
        # 企业客户添加联系人信息
        if customer_type == '1':
            customer_data['person_name'] = contact.get('contact_person') or contact.get('name')
            customer_data['email'] = contact.get('email', '')
        
        # 4. 调用API添加客户
        if customer_type == '1':
            result = self.add_company_customer(**customer_data)
        else:
            result = self.add_personal_customer(**customer_data)
        
        logger.info(f"客户同步成功: {customer_data['name']} (khid={customer_data['khid']})")
        
        return {
            'status': 'success',
            'customer_id': ord,
            'khid': customer_data['khid'],
            'result': result
        }
    
    def find_customer_by_khid(self, khid: str) -> Optional[Dict[str, Any]]:
        """
        根据客户编号查找客户
        
        Args:
            khid: 客户编号
        
        Returns:
            客户信息，不存在时返回None
        """
        customers = self.get_customer_list(page_size=1, filters={"khid": khid})
        return customers[0] if customers else None
    
    def find_customer_by_mobile(self, mobile: str) -> Optional[Dict[str, Any]]:
        """
        根据手机号查找客户
        
        Args:
            mobile: 手机号
        
        Returns:
            客户信息，不存在时返回None
        """
        customers = self.get_customer_list(page_size=1, filters={"phone": mobile})
        return customers[0] if customers else None
    
    @staticmethod
    def _map_score_to_value(score: float) -> int:
        """映射评分到价值评估"""
        if score >= 90:
            return 175  # 很高
        elif score >= 75:
            return 289  # 较高
        elif score >= 60:
            return 176  # 一般
        elif score >= 45:
            return 177  # 较低
        else:
            return 290  # 很低


# ==================== 便捷函数 ====================

def create_client_from_config(config: Dict[str, Any]) -> ZhibangERPClient:
    """
    从配置创建客户端
    
    Args:
        config: 配置字典，包含：
            - base_url: ERP地址
            - username: 用户名
            - password: 密码
    
    Returns:
        ERP客户端实例
    """
    return ZhibangERPClient(
        base_url=config['base_url'],
        username=config['username'],
        password=config['password'],
        auto_login=True
    )


# ==================== 测试代码 ====================

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 测试连接
    try:
        client = ZhibangERPClient(
            base_url='http://ls1.jmt.ink:46088',
            username='your_username',
            password='your_password'
        )
        
        print("✅ 连接成功!")
        print(f"Session: {client.session[:30]}...")
        
        # 测试获取客户列表
        customers = client.get_customer_list(page_size=5)
        print(f"\n📋 客户数量: {len(customers)}")
        
        if customers:
            print(f"第一个客户: {customers[0].get('name')}")
    
    except Exception as e:
        print(f"❌ 错误: {e}")

