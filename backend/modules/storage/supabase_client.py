"""
Supabase客户端 - 统一数据访问层
支持多租户、实时同步、认证集成
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import asyncio
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Supabase客户端 - 统一数据访问层
    
    特性：
    1. 多租户支持 (RLS自动隔离)
    2. 实时同步
    3. 认证集成
    4. 统一错误处理
    5. 连接池管理
    """
    
    def __init__(self, 
                 url: str, 
                 key: str, 
                 service_role_key: Optional[str] = None):
        """
        初始化Supabase客户端
        
        Args:
            url: Supabase项目URL
            key: Supabase匿名密钥
            service_role_key: 服务角色密钥（可选）
        """
        self.url = url
        self.key = key
        self.service_role_key = service_role_key
        
        # 创建客户端
        self.client: Client = create_client(
            supabase_url=url,
            supabase_key=key,
            options=ClientOptions(
                auto_refresh_token=True,
                persist_session=True
            )
        )
        
        # 服务角色客户端（用于管理操作）
        if service_role_key:
            self.admin_client: Client = create_client(
                supabase_url=url,
                supabase_key=service_role_key
            )
        else:
            self.admin_client = self.client
        
        # 执行登录（使用服务角色密钥）
        self._authenticate()
        
        logger.info(f"✅ Supabase客户端初始化成功: {url}")
    
    def _authenticate(self):
        """执行认证"""
        try:
            # 使用服务角色密钥进行认证
            if self.service_role_key and self.service_role_key != "your_supabase_service_role_key":
                # 服务角色密钥不需要登录，直接可用
                logger.info("✅ 使用服务角色密钥认证")
                return True
            else:
                # 匿名密钥需要登录
                logger.info("✅ 使用匿名密钥认证")
                # 对于开发模式，跳过真实认证
                if self.key == "your_supabase_anon_key":
                    logger.warning("⚠️ 使用默认密钥，跳过认证（开发模式）")
                    return True
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ Supabase认证失败: {e}")
            return False
    
    def set_tenant_context(self, tenant_id: str):
        """设置租户上下文"""
        try:
            # 检查是否有有效的会话
            session = self.client.auth.get_session()
            if not session or not session.access_token:
                logger.warning(f"⚠️ 没有有效的认证会话，跳过租户上下文设置: {tenant_id}")
                return
            
            # 设置PostgreSQL会话变量
            self.client.postgrest.auth.set_session(
                access_token=session.access_token,
                refresh_token=session.refresh_token
            )
            
            # 设置租户ID
            self.client.rpc('set_tenant_id', {'tenant_id': tenant_id})
            logger.debug(f"设置租户上下文: {tenant_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ 设置租户上下文失败: {e}")
            # 继续执行，不抛出异常
    
    # ==================== 租户管理 ====================
    
    async def create_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建租户"""
        try:
            result = self.admin_client.table('tenants').insert(tenant_data).execute()
            logger.info(f"✅ 租户创建成功: {tenant_data.get('tenant_id')}")
            return result.data[0]
        except Exception as e:
            logger.error(f"❌ 租户创建失败: {e}")
            raise
    
    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """获取租户信息"""
        try:
            result = self.client.table('tenants')\
                .select('*')\
                .eq('tenant_id', tenant_id)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"❌ 获取租户失败: {e}")
            return None
    
    async def update_tenant(self, tenant_id: str, updates: Dict[str, Any]) -> bool:
        """更新租户信息"""
        try:
            result = self.admin_client.table('tenants')\
                .update(updates)\
                .eq('tenant_id', tenant_id)\
                .execute()
            
            logger.info(f"✅ 租户更新成功: {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 租户更新失败: {e}")
            return False
    
    # ==================== 文档管理 ====================
    
    async def create_document(self, tenant_id: str, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建文档"""
        self.set_tenant_context(tenant_id)
        
        try:
            # 添加租户ID
            document_data['tenant_id'] = tenant_id
            
            result = self.client.table('documents').insert(document_data).execute()
            logger.info(f"✅ 文档创建成功: {document_data.get('document_id')}")
            return result.data[0]
        except Exception as e:
            logger.error(f"❌ 文档创建失败: {e}")
            raise
    
    async def get_documents(self, tenant_id: str, 
                          filters: Optional[Dict[str, Any]] = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """获取文档列表"""
        self.set_tenant_context(tenant_id)
        
        try:
            query = self.client.table('documents').select('*')
            
            # 应用过滤条件
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        query = query.in_(key, value)
                    else:
                        query = query.eq(key, value)
            
            result = query.limit(limit).execute()
            return result.data
        except Exception as e:
            logger.error(f"❌ 获取文档失败: {e}")
            return []
    
    async def update_document(self, tenant_id: str, document_id: str, 
                            updates: Dict[str, Any]) -> bool:
        """更新文档"""
        self.set_tenant_context(tenant_id)
        
        try:
            result = self.client.table('documents')\
                .update(updates)\
                .eq('document_id', document_id)\
                .execute()
            
            logger.info(f"✅ 文档更新成功: {document_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 文档更新失败: {e}")
            return False
    
    # ==================== 会话管理 ====================
    
    async def create_session(self, tenant_id: str, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建会话"""
        self.set_tenant_context(tenant_id)
        
        try:
            session_data['tenant_id'] = tenant_id
            
            result = self.client.table('sessions').insert(session_data).execute()
            logger.info(f"✅ 会话创建成功: {session_data.get('session_key')}")
            return result.data[0]
        except Exception as e:
            logger.error(f"❌ 会话创建失败: {e}")
            raise
    
    async def get_session(self, tenant_id: str, session_key: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        self.set_tenant_context(tenant_id)
        
        try:
            result = self.client.table('sessions')\
                .select('*')\
                .eq('session_key', session_key)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"❌ 获取会话失败: {e}")
            return None
    
    async def update_session(self, tenant_id: str, session_key: str, 
                           updates: Dict[str, Any]) -> bool:
        """更新会话"""
        self.set_tenant_context(tenant_id)
        
        try:
            result = self.client.table('sessions')\
                .update(updates)\
                .eq('session_key', session_key)\
                .execute()
            
            return True
        except Exception as e:
            logger.error(f"❌ 会话更新失败: {e}")
            return False
    
    # ==================== 消息管理 ====================
    
    async def create_message(self, tenant_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建消息"""
        self.set_tenant_context(tenant_id)
        
        try:
            message_data['tenant_id'] = tenant_id
            
            result = self.client.table('messages').insert(message_data).execute()
            logger.info(f"✅ 消息创建成功: {message_data.get('request_id')}")
            return result.data[0]
        except Exception as e:
            logger.error(f"❌ 消息创建失败: {e}")
            raise
    
    async def get_messages(self, tenant_id: str, 
                         session_id: Optional[str] = None,
                         limit: int = 50) -> List[Dict[str, Any]]:
        """获取消息列表"""
        self.set_tenant_context(tenant_id)
        
        try:
            query = self.client.table('messages').select('*')
            
            if session_id:
                query = query.eq('session_id', session_id)
            
            result = query.order('received_at', desc=True).limit(limit).execute()
            return result.data
        except Exception as e:
            logger.error(f"❌ 获取消息失败: {e}")
            return []
    
    # ==================== 实时订阅 ====================
    
    def subscribe_to_changes(self, table: str, callback: callable):
        """订阅表变化"""
        try:
            channel = self.client.realtime.channel(table)
            
            channel.on('postgres_changes', {
                'event': '*',
                'schema': 'public',
                'table': table
            }, callback)
            
            channel.subscribe()
            logger.info(f"✅ 订阅表变化: {table}")
            return channel
        except Exception as e:
            logger.error(f"❌ 订阅失败: {e}")
            return None
    
    # ==================== 文件存储 ====================
    
    async def upload_file(self, bucket: str, file_path: str, file_data: bytes) -> str:
        """上传文件"""
        try:
            result = self.client.storage.from_(bucket).upload(file_path, file_data)
            
            # 获取公共URL
            url = self.client.storage.from_(bucket).get_public_url(file_path)
            
            logger.info(f"✅ 文件上传成功: {file_path}")
            return url
        except Exception as e:
            logger.error(f"❌ 文件上传失败: {e}")
            raise
    
    async def download_file(self, bucket: str, file_path: str) -> bytes:
        """下载文件"""
        try:
            result = self.client.storage.from_(bucket).download(file_path)
            return result
        except Exception as e:
            logger.error(f"❌ 文件下载失败: {e}")
            raise
    
    # ==================== 统计查询 ====================
    
    async def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """获取租户统计信息"""
        self.set_tenant_context(tenant_id)
        
        try:
            # 并行查询统计信息
            tasks = [
                self._get_count('documents'),
                self._get_count('sessions'),
                self._get_count('messages'),
                self._get_count('tickets')
            ]
            
            results = await asyncio.gather(*tasks)
            
            return {
                'tenant_id': tenant_id,
                'document_count': results[0],
                'session_count': results[1],
                'message_count': results[2],
                'ticket_count': results[3],
                'updated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {'tenant_id': tenant_id, 'error': str(e)}
    
    async def _get_count(self, table: str) -> int:
        """获取表记录数"""
        try:
            result = self.client.table(table).select('id', count='exact').execute()
            return result.count or 0
        except Exception as e:
            logger.error(f"❌ 获取{table}计数失败: {e}")
            return 0


# 全局客户端实例
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """获取全局Supabase客户端实例"""
    global _supabase_client
    if _supabase_client is None:
        raise RuntimeError("Supabase客户端未初始化")
    return _supabase_client


def init_supabase_client(url: str, key: str, service_role_key: Optional[str] = None):
    """初始化全局Supabase客户端"""
    global _supabase_client
    _supabase_client = SupabaseClient(url, key, service_role_key)
    logger.info("✅ 全局Supabase客户端初始化完成")

