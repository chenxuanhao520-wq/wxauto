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
    
    def query_customer(self, customer_code: str = None, phone: str = None) -> Dict:
        """查询客户"""
        # 这里是简化的实现，实际应该调用真实的 ERP API
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
    
    async def _customer_create(self, customer_data: Dict) -> Dict[str, Any]:
        """创建客户"""
        return {"success": True, "customer_code": "C_NEW", "message": "客户创建成功（模拟）"}
    
    async def _customer_update(self, customer_code: str, update_data: Dict) -> Dict[str, Any]:
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
            
            # 调用 ERP API（这里是模拟数据，实际应该调用真实 API）
            # 未来可以替换为: self.erp_client.list_customers(page, page_size)
            customers = [
                {"code": f"C{i:03d}", "name": f"客户{i}", "phone": f"138{i:08d}"} 
                for i in range(1, page_size + 1)
            ]
            
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
    
    async def _order_create(self, order_data: Dict) -> Dict[str, Any]:
        """创建订单"""
        return {"success": True, "order_code": "O_NEW", "message": "订单创建成功（模拟）"}
    
    async def _order_query(self, order_code: str) -> Dict[str, Any]:
        """查询订单"""
        return {"success": True, "order": {"order_code": order_code, "status": "待处理"}}
    
    async def _product_query(self, product_code: str = None, use_cache: bool = True) -> Dict[str, Any]:
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
    
    async def _sync_customers(self, customer_ids: List[str] = None) -> Dict[str, Any]:
        """批量同步客户"""
        return {"success": True, "synced_count": 0, "message": "批量同步（模拟）"}
    
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
