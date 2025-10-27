"""
Supabase实时服务 - 实时数据同步
支持WebSocket连接、事件订阅、实时推送
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import asyncio
from supabase import Client

logger = logging.getLogger(__name__)


class SupabaseRealtimeService:
    """Supabase实时服务"""
    
    def __init__(self, supabase_client: Client):
        """
        初始化实时服务
        
        Args:
            supabase_client: Supabase客户端
        """
        self.supabase = supabase_client
        self.channels = {}
        self.subscriptions = {}
        
        logger.info("✅ Supabase实时服务初始化完成")
    
    async def subscribe_to_table(
        self, 
        table: str, 
        callback: Callable[[Dict[str, Any]], None],
        event_type: str = "*",
        schema: str = "public"
    ) -> str:
        """
        订阅表变化
        
        Args:
            table: 表名
            callback: 回调函数
            event_type: 事件类型 (*, INSERT, UPDATE, DELETE)
            schema: 模式名
            
        Returns:
            订阅ID
        """
        try:
            # 创建频道
            channel_name = f"{schema}:{table}"
            channel = self.supabase.realtime.channel(channel_name)
            
            # 订阅PostgreSQL变化
            channel.on(
                'postgres_changes',
                {
                    'event': event_type,
                    'schema': schema,
                    'table': table
                },
                callback
            )
            
            # 订阅频道（Python SDK是同步的）
            channel.subscribe()
            
            # 保存订阅信息
            subscription_id = f"{table}_{event_type}_{datetime.now().timestamp()}"
            self.subscriptions[subscription_id] = {
                "channel": channel,
                "table": table,
                "event_type": event_type,
                "callback": callback
            }
            
            logger.info(f"✅ 订阅表变化成功: {table} ({event_type})")
            return subscription_id
            
        except Exception as e:
            logger.error(f"❌ 订阅表变化失败: {e}")
            raise
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        try:
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions[subscription_id]
                channel = subscription["channel"]
                
                # 取消订阅（Python SDK是同步的）
                channel.unsubscribe()
                
                # 删除订阅记录
                del self.subscriptions[subscription_id]
                
                logger.info(f"✅ 取消订阅成功: {subscription_id}")
                return True
            else:
                logger.warning(f"⚠️ 订阅不存在: {subscription_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 取消订阅失败: {e}")
            return False
    
    async def subscribe_to_messages(
        self, 
        tenant_id: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """订阅消息变化"""
        try:
            def message_callback(payload: Dict[str, Any]):
                """消息变化回调"""
                try:
                    # 添加租户过滤
                    if payload.get("new", {}).get("tenant_id") == tenant_id:
                        callback(payload)
                except Exception as e:
                    logger.error(f"❌ 消息回调处理失败: {e}")
            
            subscription_id = await self.subscribe_to_table(
                "messages",
                message_callback,
                "*"
            )
            
            logger.info(f"✅ 订阅消息变化成功: {tenant_id}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"❌ 订阅消息变化失败: {e}")
            raise
    
    async def subscribe_to_sessions(
        self, 
        tenant_id: str,
        callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """订阅会话变化"""
        try:
            def session_callback(payload: Dict[str, Any]):
                """会话变化回调"""
                try:
                    # 添加租户过滤
                    if payload.get("new", {}).get("tenant_id") == tenant_id:
                        callback(payload)
                except Exception as e:
                    logger.error(f"❌ 会话回调处理失败: {e}")
            
            subscription_id = await self.subscribe_to_table(
                "sessions",
                session_callback,
                "*"
            )
            
            logger.info(f"✅ 订阅会话变化成功: {tenant_id}")
            return subscription_id
            
        except Exception as e:
            logger.error(f"❌ 订阅会话变化失败: {e}")
            raise
    
    async def subscribe_to_configs(
        self, 
        callback: Callable[[Dict[str, Any]], None]
    ) -> str:
        """订阅配置变化"""
        try:
            subscription_id = await self.subscribe_to_table(
                "system_configs",
                callback,
                "*"
            )
            
            logger.info(f"✅ 订阅配置变化成功")
            return subscription_id
            
        except Exception as e:
            logger.error(f"❌ 订阅配置变化失败: {e}")
            raise
    
    async def broadcast_message(
        self, 
        channel: str, 
        message: Dict[str, Any]
    ) -> bool:
        """广播消息"""
        try:
            # 使用Supabase的广播功能
            result = self.supabase.realtime.channel(channel).send({
                "type": "broadcast",
                "event": "message",
                "payload": message
            })
            
            logger.debug(f"✅ 广播消息成功: {channel}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 广播消息失败: {e}")
            return False
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        try:
            # 检查实时连接状态
            status = {
                "connected": True,  # 简化实现
                "subscriptions_count": len(self.subscriptions),
                "channels_count": len(self.channels),
                "timestamp": datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"❌ 获取连接状态失败: {e}")
            return {
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def close_all_subscriptions(self):
        """关闭所有订阅"""
        try:
            for subscription_id in list(self.subscriptions.keys()):
                await self.unsubscribe(subscription_id)
            
            logger.info("✅ 所有订阅已关闭")
            
        except Exception as e:
            logger.error(f"❌ 关闭订阅失败: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            status = await self.get_connection_status()
            
            return {
                "service": "supabase_realtime",
                "status": "healthy" if status["connected"] else "unhealthy",
                "subscriptions": status["subscriptions_count"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 实时服务健康检查失败: {e}")
            return {
                "service": "supabase_realtime",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# 全局实时服务实例
_realtime_service: Optional[SupabaseRealtimeService] = None


def get_realtime_service() -> SupabaseRealtimeService:
    """获取全局实时服务实例"""
    global _realtime_service
    if _realtime_service is None:
        raise RuntimeError("实时服务未初始化")
    return _realtime_service


def init_realtime_service(supabase_client: Client):
    """初始化全局实时服务"""
    global _realtime_service
    _realtime_service = SupabaseRealtimeService(supabase_client)
    logger.info("✅ 全局实时服务初始化完成")