"""
统一数据库管理器 - 纯Supabase架构
专为企业级云原生应用设计
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """数据库类型"""
    SUPABASE = "supabase"


class DatabaseAdapter(ABC):
    """数据库适配器抽象基类"""
    
    @abstractmethod
    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建会话"""
        pass
    
    @abstractmethod
    async def get_session(self, session_key: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        pass
    
    @abstractmethod
    async def update_session(self, session_key: str, updates: Dict[str, Any]) -> bool:
        """更新会话"""
        pass
    
    @abstractmethod
    async def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建消息"""
        pass
    
    @abstractmethod
    async def get_messages(self, session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取消息列表"""
        pass
    
    @abstractmethod
    async def update_message(self, request_id: str, updates: Dict[str, Any]) -> bool:
        """更新消息"""
        pass
    
    @abstractmethod
    async def check_rate_limit(self, entity_type: str, entity_id: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """检查速率限制"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass


class SupabaseAdapter(DatabaseAdapter):
    """Supabase数据库适配器 - 官方接入方案"""
    
    def __init__(self, url: str, key: str, service_role_key: Optional[str] = None):
        self.url = url
        self.key = key
        self.service_role_key = service_role_key
        
        try:
            from supabase import create_client, Client
            from supabase.lib.client_options import ClientOptions
            
            # 创建Supabase客户端
            self.client: Client = create_client(
                supabase_url=url,
                supabase_key=key,
                options=ClientOptions(
                    auto_refresh_token=True,
                    persist_session=True
                )
            )
            
            # 创建管理员客户端（用于需要更高权限的操作）
            if service_role_key:
                self.admin_client: Client = create_client(
                    supabase_url=url,
                    supabase_key=service_role_key
                )
            else:
                self.admin_client = self.client
            
            logger.info(f"✅ Supabase客户端初始化成功: {url}")
            
            # 验证连接
            self._verify_connection()
            
        except ImportError:
            raise ImportError("Supabase库未安装: pip install supabase")
        except Exception as e:
            logger.error(f"❌ Supabase初始化失败: {e}")
            raise
    
    def _verify_connection(self):
        """验证Supabase连接"""
        try:
            # 尝试查询系统表来验证连接
            result = self.client.table('sessions').select('id').limit(1).execute()
            logger.info("✅ Supabase连接验证成功")
        except Exception as e:
            logger.warning(f"⚠️ Supabase连接验证失败: {e}")
            logger.info("💡 请检查:")
            logger.info("   1. SUPABASE_URL是否正确")
            logger.info("   2. SUPABASE_ANON_KEY是否有效")
            logger.info("   3. 网络连接是否正常")
            logger.info("   4. Supabase项目是否已创建")
    
    def create_session_sync(self, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建会话（同步版本）"""
        try:
            # 在新的事件循环中运行异步方法
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果已经在事件循环中，使用线程池
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.create_session(session_data))
                        return future.result()
                else:
                    return loop.run_until_complete(self.create_session(session_data))
            except RuntimeError:
                # 没有事件循环，创建新的
                return asyncio.run(self.create_session(session_data))
                
        except Exception as e:
            logger.error(f"❌ 同步创建会话失败: {e}")
            return None

    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建会话"""
        try:
            result = self.client.table('sessions').insert(session_data).execute()
            if result.data:
                logger.debug(f"✅ Supabase会话创建成功: {session_data.get('session_key')}")
                return result.data[0]
            else:
                logger.error(f"❌ Supabase会话创建失败: 无返回数据")
                return {}
        except Exception as e:
            logger.error(f"❌ Supabase创建会话失败: {e}")
            raise
    
    async def get_session(self, session_key: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        try:
            result = self.client.table('sessions')\
                .select('*')\
                .eq('session_key', session_key)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"❌ Supabase获取会话失败: {e}")
            return None
    
    async def update_session(self, session_key: str, updates: Dict[str, Any]) -> bool:
        """更新会话"""
        try:
            result = self.client.table('sessions')\
                .update(updates)\
                .eq('session_key', session_key)\
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Supabase更新会话失败: {e}")
            return False
    
    async def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建消息"""
        try:
            result = self.client.table('messages').insert(message_data).execute()
            if result.data:
                logger.debug(f"✅ Supabase消息创建成功: {message_data.get('request_id')}")
                return result.data[0]
            else:
                logger.error(f"❌ Supabase消息创建失败: 无返回数据")
                return {}
        except Exception as e:
            logger.error(f"❌ Supabase创建消息失败: {e}")
            raise
    
    async def get_messages(self, session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """获取消息列表"""
        try:
            query = self.client.table('messages').select('*')
            
            if session_id:
                query = query.eq('session_id', session_id)
            
            result = query.order('received_at', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            logger.error(f"❌ Supabase获取消息失败: {e}")
            return []
    
    async def update_message(self, request_id: str, updates: Dict[str, Any]) -> bool:
        """更新消息"""
        try:
            result = self.client.table('messages')\
                .update(updates)\
                .eq('request_id', request_id)\
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Supabase更新消息失败: {e}")
            return False
    
    async def check_rate_limit(self, entity_type: str, entity_id: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """检查速率限制"""
        try:
            from datetime import datetime, timedelta
            
            now = datetime.now()
            window_start = now - timedelta(seconds=window_seconds)
            
            # 查询当前窗口内的请求数
            result = self.client.table('rate_limits')\
                .select('request_count')\
                .eq('entity_type', entity_type)\
                .eq('entity_id', entity_id)\
                .gte('window_start', window_start.isoformat())\
                .execute()
            
            current_count = sum(row['request_count'] for row in result.data)
            is_allowed = current_count < limit
            
            if is_allowed:
                # 插入新的速率记录
                self.client.table('rate_limits').insert({
                    'entity_type': entity_type,
                    'entity_id': entity_id,
                    'window_start': now.isoformat(),
                    'request_count': 1,
                    'last_request_at': now.isoformat()
                }).execute()
                current_count += 1
            
            return is_allowed, current_count
        except Exception as e:
            logger.error(f"❌ Supabase速率限制检查失败: {e}")
            return False, 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            # 并行查询统计信息
            import asyncio
            
            async def get_count(table: str) -> int:
                result = self.client.table(table).select('id', count='exact').execute()
                return result.count or 0
            
            tasks = [
                get_count('sessions'),
                get_count('messages')
            ]
            
            results = await asyncio.gather(*tasks)
            
            return {
                "database_type": "supabase",
                "session_count": results[0],
                "message_count": results[1],
                "supabase_url": self.url
            }
        except Exception as e:
            logger.error(f"❌ Supabase获取统计失败: {e}")
            return {"database_type": "supabase", "error": str(e)}


class UnifiedDatabaseManager:
    """
    统一数据库管理器 - 纯Supabase架构
    专为企业级云原生应用设计
    """
    
    def __init__(self):
        self.db_type = DatabaseType.SUPABASE
        self.adapter = self._create_adapter()
        
        logger.info(f"✅ 统一数据库管理器初始化: {self.db_type.value}")
    
    def _create_adapter(self) -> DatabaseAdapter:
        """创建Supabase适配器"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # 如果没有配置，使用默认值（开发模式）
        if not url or not key:
            logger.warning("⚠️ Supabase配置不完整，使用默认配置（开发模式）")
            url = url or "https://your-project.supabase.co"
            key = key or "your_supabase_anon_key"
            service_role_key = service_role_key or "your_supabase_service_role_key"
        
        return SupabaseAdapter(url, key, service_role_key)
    
    # 代理方法到适配器
    def create_session_sync(self, tenant_id: str, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建会话（同步版本）"""
        return self.adapter.create_session_sync(session_data)
    
    async def create_session(self, tenant_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.adapter.create_session(session_data)
    
    async def get_session(self, session_key: str) -> Optional[Dict[str, Any]]:
        return await self.adapter.get_session(session_key)
    
    async def update_session(self, session_key: str, updates: Dict[str, Any]) -> bool:
        return await self.adapter.update_session(session_key, updates)
    
    async def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.adapter.create_message(message_data)
    
    async def get_messages(self, session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        return await self.adapter.get_messages(session_id, limit)
    
    async def update_message(self, request_id: str, updates: Dict[str, Any]) -> bool:
        return await self.adapter.update_message(request_id, updates)
    
    async def check_rate_limit(self, entity_type: str, entity_id: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        return await self.adapter.check_rate_limit(entity_type, entity_id, limit, window_seconds)
    
    async def get_stats(self) -> Dict[str, Any]:
        return await self.adapter.get_stats()
    
    def get_database_type(self) -> DatabaseType:
        """获取当前数据库类型"""
        return self.db_type


# 全局数据库管理器实例
_db_manager: Optional[UnifiedDatabaseManager] = None


def get_database_manager() -> UnifiedDatabaseManager:
    """获取全局数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = UnifiedDatabaseManager()
    return _db_manager


def init_database_manager():
    """初始化全局数据库管理器"""
    global _db_manager
    _db_manager = UnifiedDatabaseManager()
    logger.info("✅ 全局数据库管理器初始化完成")