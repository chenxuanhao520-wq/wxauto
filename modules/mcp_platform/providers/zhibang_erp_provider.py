"""
智邦国际 ERP MCP 服务提供商
将智邦 ERP 封装为 MCP 标准接口
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class ZhibangERPClient:
    """智邦 ERP 轻量级客户端（用于 MCP）"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session_token = None
    
    def login(self) -> bool:
        """登录 ERP"""
        try:
            url = f"{self.base_url}/webapi/v3/ov1/login"
            datas = [
                {"id": "user", "val": f"txt:{self.username}"},
                {"id": "password", "val": f"txt:{self.password}"},
                {"id": "serialnum", "val": "txt:mcp_erp_client_001"}
            ]
            
            response = requests.post(
                url,
                json={"datas": datas},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            result = response.json()
            
            if result.get('header', {}).get('status') == 0:
                self.session_token = result['header']['session']
                logger.info(f"✅ ERP 登录成功")
                return True
            else:
                logger.error(f"❌ ERP 登录失败: {result.get('header', {}).get('message')}")
                return False
        except Exception as e:
            logger.error(f"❌ ERP 登录异常: {e}")
            return False
    
    def ensure_logged_in(self) -> bool:
        """确保已登录"""
        if not self.session_token:
            return self.login()
        return True
    
    def list_customers(self, page: int = 1, page_size: int = 20) -> List[Dict]:
        """获取客户列表"""
        if not self.ensure_logged_in():
            logger.error("ERP 未登录，无法获取客户列表")
            return []
        
        try:
            url = f"{self.base_url}/sysa/mobilephone/salesmanage/custom/list.asp"
            
            # 按照智邦 ERP API 文档格式构建完整的参数
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
                "pagesize": page_size,    # 每页记录数
                "pageindex": page,        # 数据页标
                "_rpt_sort": ""      # 排序字段
            }
            
            # 转换为 id-val 键值对数组格式
            datas = [{"id": key, "val": value} for key, value in dats.items()]
            
            json_data = {
                "session": self.session_token,
                "cmdkey": "refresh",
                "datas": datas
            }
            
            response = requests.post(
                url,
                json=json_data,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            result = response.json()
            
            if result.get('header', {}).get('status') == 0:
                # 解析表格数据 - 根据实际 API 响应结构
                body = result.get('body', {})
                source = body.get('source', {})
                table = source.get('table', {})
                rows_data = table.get('rows', [])
                cols = table.get('cols', [])
                
                # 将原始数组数据转换为字典格式
                customers = []
                for row in rows_data:
                    customer = {}
                    for i, col in enumerate(cols):
                        if i < len(row):
                            customer[col['id']] = row[i]
                    customers.append(customer)
                
                logger.info(f"✅ 获取到 {len(customers)} 个客户")
                return customers
            else:
                logger.error(f"❌ 获取客户列表失败: {result}")
                return []
        except Exception as e:
            logger.error(f"❌ 获取客户列表异常: {e}")
            return []
    
    def query_customer(self, customer_code: str = None, phone: str = None) -> Dict:
        """查询客户"""
        # 简化实现，返回示例数据
        return {
            "customer_code": customer_code or "C001",
            "name": "示例客户",
            "phone": phone or "13800138000",
            "type": "潜在客户"
        }
    
    def query_product(self, product_code: str) -> Dict:
        """查询产品"""
        return {
            "product_code": product_code,
            "name": "示例产品",
            "price": 1000.00,
            "stock": 100
        }
    
    def list_orders(self, page: int = 1, page_size: int = 20, customer_id: str = None) -> List[Dict]:
        """获取订单列表"""
        if not self.ensure_logged_in():
            logger.error("ERP 未登录，无法获取订单列表")
            return []
        
        try:
            url = f"{self.base_url}/sysa/mobilephone/salesmanage/order/list.asp"
            
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
                "telord": customer_id if customer_id else "",  # 客户ID
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
                "pagesize": page_size,    # 每页记录数
                "pageindex": page,        # 页码
                "_rpt_sort": ""      # 排序字段
            }
            
            # 转换为 id-val 键值对数组格式
            datas = [{"id": key, "val": value} for key, value in dats.items()]
            
            json_data = {
                "session": self.session_token,
                "cmdkey": "refresh",
                "datas": datas
            }
            
            response = requests.post(
                url,
                json=json_data,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            result = response.json()
            
            if result.get('header', {}).get('status') == 0:
                # 解析表格数据
                body = result.get('body', {})
                source = body.get('source', {})
                table = source.get('table', {})
                rows_data = table.get('rows', [])
                cols = table.get('cols', [])
                
                # 将原始数组数据转换为字典格式
                orders = []
                for row in rows_data:
                    order = {}
                    for i, col in enumerate(cols):
                        if i < len(row):
                            order[col['id']] = row[i]
                    orders.append(order)
                
                logger.info(f"✅ 获取到 {len(orders)} 个订单")
                return orders
            else:
                logger.error(f"❌ 获取订单列表失败: {result}")
                return []
        except Exception as e:
            logger.error(f"❌ 获取订单列表异常: {e}")
            return []
    
    def list_contracts(self, page: int = 1, page_size: int = 20, customer_id: str = None) -> List[Dict]:
        """获取合同列表"""
        if not self.ensure_logged_in():
            logger.error("ERP 未登录，无法获取合同列表")
            return []
        
        try:
            url = f"{self.base_url}/sysa/mobilephone/salesmanage/contract/blist.asp"
            
            # 构建合同查询参数 - 按照智邦 ERP 合同 API 文档
            dats = {
                "stype": 0,          # 列表模式，0=全部，1=待审核，2=即将到期
                "datatype": "",      # 数据模式
                "remind": "",        # 提醒类型，14=合同审核，17=员工合同到期
                "tdate1": "",        # 添加开始日期
                "tdate2": "",        # 添加结束日期
                "a_date_0": "",      # 签约开始日期
                "a_date_1": "",      # 签约结束日期
                "htbh": "",          # 合同编号（模糊查询）
                "khmc": customer_id if customer_id else "",  # 客户名称（模糊查询）
                "htmoney_0": 0,      # 合同金额下限
                "htmoney_1": 0,      # 合同金额上限
                "dateQD_0": "",      # 签约日期开始
                "dateQD_1": "",      # 签约日期结束
                "dateKS_0": "",      # 合同开始日期开始
                "dateKS_1": "",      # 合同开始日期结束
                "dateZZ_0": "",      # 合同结束日期开始
                "dateZZ_1": "",      # 合同结束日期结束
                "searchKey": "",     # 快速检索条件
                "pagesize": page_size,    # 每页记录数
                "pageindex": page,        # 页码
                "_rpt_sort": ""      # 排序字段
            }
            
            # 转换为 id-val 键值对数组格式
            datas = [{"id": key, "val": value} for key, value in dats.items()]
            
            json_data = {
                "session": self.session_token,
                "cmdkey": "refresh",
                "datas": datas
            }
            
            response = requests.post(
                url,
                json=json_data,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            result = response.json()
            
            if result.get('header', {}).get('status') == 0:
                # 解析表格数据
                body = result.get('body', {})
                source = body.get('source', {})
                table = source.get('table', {})
                rows_data = table.get('rows', [])
                cols = table.get('cols', [])
                
                # 将原始数组数据转换为字典格式
                contracts = []
                for row in rows_data:
                    contract = {}
                    for i, col in enumerate(cols):
                        if i < len(row):
                            contract[col['id']] = row[i]
                    contracts.append(contract)
                
                logger.info(f"✅ 获取到 {len(contracts)} 个合同")
                return contracts
            else:
                logger.error(f"❌ 获取合同列表失败: {result}")
                return []
        except Exception as e:
            logger.error(f"❌ 获取合同列表异常: {e}")
            return []


class ZhibangERPProvider:
    """智邦国际 ERP MCP 服务提供商"""
    
    def __init__(self, service, cache_manager=None):
        """
        初始化 ERP Provider
        
        Args:
            service: MCP 服务配置
            cache_manager: 缓存管理器
        """
        self.service = service
        self.cache_manager = cache_manager
        
        # 从配置获取 ERP 连接信息
        metadata = service.metadata if hasattr(service, 'metadata') else {}
        self.base_url = metadata.get('base_url', 'http://ls1.jmt.ink:46088')
        self.username = metadata.get('username', '')
        self.password = metadata.get('password', '')
        
        # 缓存配置
        self.cache_config = service.cache_config if hasattr(service, 'cache_config') else {}
        self.cache_enabled = self.cache_config.get('enabled', True)
        
        # 初始化 ERP 客户端
        self.erp_client = ZhibangERPClient(
            base_url=self.base_url,
            username=self.username,
            password=self.password
        )
        
        # 工具列表
        self.tools = [
            "erp_customer_create",
            "erp_customer_update",
            "erp_customer_query",
            "erp_customer_list",
            "erp_order_create",
            "erp_order_query",
            "erp_contract_query",
            "erp_product_query",
            "erp_sync_customers"
        ]
        
        logger.info(f"✅ 智邦 ERP Provider 初始化成功 (工具数: {len(self.tools)})")
    
    async def call(self, method: str, **kwargs) -> Any:
        """
        调用 ERP 方法
        
        Args:
            method: 方法名
            **kwargs: 方法参数
            
        Returns:
            调用结果
        """
        # 确保已登录
        if self.username and self.password:
            if not self.erp_client.ensure_logged_in():
                logger.warning("ERP 登录失败，返回模拟数据")
        
        # 根据方法名调用对应功能
        if method == "erp_customer_create":
            return await self._customer_create(**kwargs)
        elif method == "erp_customer_update":
            return await self._customer_update(**kwargs)
        elif method == "erp_customer_query":
            return await self._customer_query(**kwargs)
        elif method == "erp_customer_list":
            return await self._customer_list(**kwargs)
        elif method == "erp_order_create":
            return await self._order_create(**kwargs)
        elif method == "erp_order_query":
            return await self._order_query(**kwargs)
        elif method == "erp_contract_query":
            return await self._contract_query(**kwargs)
        elif method == "erp_product_query":
            return await self._product_query(**kwargs)
        elif method == "erp_sync_customers":
            return await self._sync_customers(**kwargs)
        else:
            raise ValueError(f"未知的 ERP 方法: {method}")
    
    async def _customer_query(self, customer_code: str = None, phone: str = None, use_cache: bool = True) -> Dict[str, Any]:
        """查询客户信息"""
        try:
            # 尝试从缓存获取
            if use_cache and self.cache_manager:
                cache_key = self.cache_manager._generate_cache_key(
                    "erp_zhibang", "customer_query",
                    customer_code=customer_code,
                    phone=phone
                )
                cached_result = self.cache_manager.get(cache_key)
                if cached_result is not None:
                    logger.info(f"📦 使用缓存的客户信息")
                    return cached_result
            
            logger.info(f"🔍 查询 ERP 客户: {customer_code or phone}")
            
            # 调用 ERP API
            result = self.erp_client.query_customer(customer_code=customer_code, phone=phone)
            
            response = {
                "success": True,
                "customer": result
            }
            
            # 存入缓存（30分钟）
            if use_cache and self.cache_manager:
                ttl = self.cache_config.get('rules', {}).get('customer_query', 1800)
                self.cache_manager.set(cache_key, response, ttl)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ 查询客户失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _customer_create(self, customer_data: Dict, **kwargs) -> Dict[str, Any]:
        """创建客户"""
        return {"success": True, "customer_code": "C_NEW", "message": "客户创建成功（模拟）"}
    
    async def _customer_update(self, customer_code: str, update_data: Dict, **kwargs) -> Dict[str, Any]:
        """更新客户"""
        return {"success": True, "message": "客户更新成功（模拟）"}
    
    async def _customer_list(self, page: int = 1, page_size: int = 20, use_cache: bool = True, **kwargs) -> Dict[str, Any]:
        """客户列表"""
        try:
            # 尝试从缓存获取
            if use_cache and self.cache_manager:
                cache_key = self.cache_manager._generate_cache_key(
                    "erp_zhibang", "customer_list",
                    page=page,
                    page_size=page_size
                )
                cached_result = self.cache_manager.get(cache_key)
                if cached_result is not None:
                    logger.info(f"📦 使用缓存的客户列表 (页码: {page})")
                    return cached_result
            
            logger.info(f"🔍 查询 ERP 客户列表 (页码: {page}, 每页: {page_size})")
            
            # 调用真实的 ERP API
            customers = self.erp_client.list_customers(page=page, page_size=page_size)
            
            response = {
                "success": True,
                "customers": customers,
                "page": page,
                "page_size": page_size,
                "total": len(customers)
            }
            
            # 存入缓存（10分钟）
            if use_cache and self.cache_manager:
                ttl = self.cache_config.get('rules', {}).get('customer_list', 600)
                self.cache_manager.set(cache_key, response, ttl)
                logger.debug(f"💾 客户列表已缓存 (TTL: {ttl}秒)")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ 查询客户列表失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _order_create(self, order_data: Dict, **kwargs) -> Dict[str, Any]:
        """创建订单"""
        return {"success": True, "order_code": "O_NEW", "message": "订单创建成功（模拟）"}
    
    async def _order_query(self, order_code: str = None, customer_id: str = None, use_cache: bool = False, **kwargs) -> Dict[str, Any]:
        """查询订单详情或订单列表"""
        logger.info(f"🔍 查询订单: order_code={order_code}, customer_id={customer_id}")
        
        # 调用真实的 ERP API 查询订单
        orders = self.erp_client.list_orders(
            page=kwargs.get('page', 1),
            page_size=kwargs.get('page_size', 20),
            customer_id=customer_id
        )
        
        if order_code:
            # 如果指定了订单号，查找特定订单
            target_order = None
            for order in orders:
                if order.get('ord') == order_code or order.get('name') == order_code:
                    target_order = order
                    break
            
            if target_order:
                response = {
                    "success": True,
                    "order": target_order,
                    "source": "erp_system"
                }
            else:
                response = {
                    "success": False,
                    "message": f"未找到订单: {order_code}",
                    "source": "erp_system"
                }
        else:
            # 返回订单列表
            response = {
                "success": True,
                "orders": orders,
                "total": len(orders),
                "page": kwargs.get('page', 1),
                "page_size": kwargs.get('page_size', 20),
                "source": "erp_system"
            }
        
        return response
    
    async def _contract_query(self, contract_code: str = None, customer_id: str = None, use_cache: bool = False, **kwargs) -> Dict[str, Any]:
        """查询合同详情或合同列表"""
        logger.info(f"🔍 查询合同: contract_code={contract_code}, customer_id={customer_id}")
        
        # 调用真实的 ERP API 查询合同
        contracts = self.erp_client.list_contracts(
            page=kwargs.get('page', 1),
            page_size=kwargs.get('page_size', 20),
            customer_id=customer_id
        )
        
        if contract_code:
            # 如果指定了合同号，查找特定合同
            target_contract = None
            for contract in contracts:
                if contract.get('ord') == contract_code or contract.get('name') == contract_code:
                    target_contract = contract
                    break
            
            if target_contract:
                response = {
                    "success": True,
                    "contract": target_contract,
                    "source": "erp_system"
                }
            else:
                response = {
                    "success": False,
                    "message": f"未找到合同: {contract_code}",
                    "source": "erp_system"
                }
        else:
            # 返回合同列表
            response = {
                "success": True,
                "contracts": contracts,
                "total": len(contracts),
                "page": kwargs.get('page', 1),
                "page_size": kwargs.get('page_size', 20),
                "source": "erp_system"
            }
        
        return response
    
    async def _product_query(self, product_code: str = None, use_cache: bool = True, **kwargs) -> Dict[str, Any]:
        """查询产品"""
        try:
            # 尝试从缓存获取
            if use_cache and self.cache_manager:
                cache_key = self.cache_manager._generate_cache_key(
                    "erp_zhibang", "product_query",
                    product_code=product_code
                )
                cached_result = self.cache_manager.get(cache_key)
                if cached_result is not None:
                    logger.info(f"📦 使用缓存的产品信息")
                    return cached_result
            
            logger.info(f"🔍 查询 ERP 产品: {product_code}")
            
            # 调用 ERP API
            result = self.erp_client.query_product(product_code=product_code)
            
            response = {
                "success": True,
                "product": result
            }
            
            # 存入缓存（1小时）
            if use_cache and self.cache_manager:
                ttl = self.cache_config.get('rules', {}).get('product_query', 3600)
                self.cache_manager.set(cache_key, response, ttl)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ 查询产品失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _sync_customers(self, customer_ids: List[str] = None, **kwargs) -> Dict[str, Any]:
        """批量同步客户"""
        return {"success": True, "synced_count": len(customer_ids) if customer_ids else 0, "message": "批量同步（模拟）"}
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 如果没有凭据，返回配置正常
            if not self.username or not self.password:
                return {
                    "status": "configured",
                    "message": "ERP 服务已配置（需要设置凭据）",
                    "erp_url": self.base_url,
                    "tools_count": len(self.tools)
                }
            
            # 检查是否能登录
            if self.erp_client.ensure_logged_in():
                return {
                    "status": "healthy",
                    "message": "ERP 连接正常",
                    "erp_url": self.base_url,
                    "tools_count": len(self.tools)
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "ERP 登录失败"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_capabilities(self) -> List[str]:
        """获取服务能力"""
        return self.tools
    
    def __repr__(self) -> str:
        return f"<ZhibangERPProvider(url={self.base_url}, tools={len(self.tools)})>"
