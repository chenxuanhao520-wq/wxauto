#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智邦国际ERP API Python客户端
自动生成于: 2025-10-19 12:43:10
"""

import requests
from typing import Dict, List, Optional, Any

class ZhibangERPClient:
    """智邦ERP API客户端"""

    def __init__(self, base_url: str, session: str = None):
        self.base_url = base_url
        self.session = session

    def login(self, username: str, password: str, serialnum: str) -> Dict[str, Any]:
        """系统登录"""
        url = f"{self.base_url}/webapi/v3/ov1/login"
        payload = {
            "datas": [
                {"id": "user", "val": f"txt:{username}"},
                {"id": "password", "val": f"txt:{password}"},
                {"id": "serialnum", "val": f"txt:{serialnum}"}
            ]
        }
        response = requests.post(url, json=payload)
        result = response.json()
        if result.get("header", {}).get("status") == 0:
            self.session = result["header"]["session"]
        return result

    def 分配新客户id(self, **kwargs) -> Dict[str, Any]:
        """分配新客户ID"""
        url = "http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/add.asp"
        payload = {
            "session": self.session,
            "datas": [
                {"id": key, "val": value} for key, value in kwargs.items()
            ]
        }
        response = requests.post(url, json=payload)
        return response.json()

    def add_company_customer(self, **kwargs) -> Dict[str, Any]:
        """单位客户添加"""
        url = "http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/add.asp?intsort=1"
        payload = {
            "session": self.session,
            "datas": [
                {"id": key, "val": value} for key, value in kwargs.items()
            ]
        }
        response = requests.post(url, json=payload)
        return response.json()

    def add_company_customer(self, **kwargs) -> Dict[str, Any]:
        """单位客户添加"""
        url = "http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/add.asp?intsort=1"
        payload = {
            "session": self.session,
            "datas": [
                {"id": key, "val": value} for key, value in kwargs.items()
            ]
        }
        response = requests.post(url, json=payload)
        return response.json()

    def add_personal_customer(self, **kwargs) -> Dict[str, Any]:
        """个人客户添加"""
        url = "http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/add.asp?intsort=2"
        payload = {
            "session": self.session,
            "datas": [
                {"id": key, "val": value} for key, value in kwargs.items()
            ]
        }
        response = requests.post(url, json=payload)
        return response.json()

    def get_customer_detail(self, **kwargs) -> Dict[str, Any]:
        """客户详情"""
        url = "http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/add.asp?edit=1"
        payload = {
            "session": self.session,
            "datas": [
                {"id": key, "val": value} for key, value in kwargs.items()
            ]
        }
        response = requests.post(url, json=payload)
        return response.json()

    def get_customer_list(self, **kwargs) -> Dict[str, Any]:
        """客户列表"""
        url = "http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/list.asp"
        payload = {
            "session": self.session,
            "datas": [
                {"id": key, "val": value} for key, value in kwargs.items()
            ]
        }
        response = requests.post(url, json=payload)
        return response.json()

    def assign_customer(self, **kwargs) -> Dict[str, Any]:
        """客户指派"""
        url = "http://ls1.jmt.ink:46088/sysa/mobilephone/systemmanage/order.asp?datatype=tel"
        payload = {
            "session": self.session,
            "datas": [
                {"id": key, "val": value} for key, value in kwargs.items()
            ]
        }
        response = requests.post(url, json=payload)
        return response.json()

    def recall_customer(self, **kwargs) -> Dict[str, Any]:
        """客户收回"""
        url = "http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/takeback.asp"
        payload = {
            "session": self.session,
            "datas": [
                {"id": key, "val": value} for key, value in kwargs.items()
            ]
        }
        response = requests.post(url, json=payload)
        return response.json()

    def 客户申请(self, **kwargs) -> Dict[str, Any]:
        """客户申请"""
        url = "http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/apply.asp"
        payload = {
            "session": self.session,
            "datas": [
                {"id": key, "val": value} for key, value in kwargs.items()
            ]
        }
        response = requests.post(url, json=payload)
        return response.json()

    def 客户审批(self, **kwargs) -> Dict[str, Any]:
        """客户审批"""
        url = "http://ls1.jmt.ink:46088/sysa/mobilephone/salesmanage/custom/approve.asp?__msgid=onsave"
        payload = {
            "session": self.session,
            "datas": [
                {"id": key, "val": value} for key, value in kwargs.items()
            ]
        }
        response = requests.post(url, json=payload)
        return response.json()

