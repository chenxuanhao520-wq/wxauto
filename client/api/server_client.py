#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器API客户端
负责与服务器的所有通信
"""

import logging
import httpx
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class ServerClient:
    """服务器API客户端"""
    
    def __init__(self, base_url: str, agent_id: str, api_key: str):
        """
        初始化服务器客户端
        
        Args:
            base_url: 服务器地址，如 http://localhost:8000
            agent_id: 客户端ID
            api_key: API密钥
        """
        self.base_url = base_url.rstrip('/')
        self.agent_id = agent_id
        self.api_key = api_key
        
        # 创建HTTP客户端
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                'X-Agent-ID': agent_id,
                'X-API-Key': api_key,
                'Content-Type': 'application/json'
            },
            timeout=30.0
        )
        
        logger.info(f"服务器客户端初始化: {base_url}")
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            服务器是否健康
        """
        try:
            response = await self.client.get('/api/v1/health')
            return response.status_code == 200
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return False
    
    async def authenticate(self) -> Optional[str]:
        """
        认证并获取访问令牌
        
        Returns:
            访问令牌
        """
        try:
            response = await self.client.post('/api/v1/auth/login', json={
                'agent_id': self.agent_id,
                'api_key': self.api_key
            })
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                logger.info("✅ 认证成功")
                return token
            else:
                logger.error(f"认证失败: {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"认证请求失败: {e}")
            return None
    
    async def report_message(self, message: Dict) -> Optional[Dict]:
        """
        上报消息到服务器
        
        Args:
            message: 消息数据
        
        Returns:
            服务器返回的处理结果
        """
        try:
            response = await self.client.post('/api/v1/messages', json={
                'agent_id': self.agent_id,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"消息已上报: {message.get('id', '')[:10]}...")
                return result
            else:
                logger.error(f"上报失败: {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"上报消息失败: {e}")
            return None
    
    async def get_reply(self, message_id: str) -> Optional[Dict]:
        """
        获取服务器生成的回复
        
        Args:
            message_id: 消息ID
        
        Returns:
            回复内容
        """
        try:
            response = await self.client.get(f'/api/v1/messages/{message_id}/reply')
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
        
        except Exception as e:
            logger.error(f"获取回复失败: {e}")
            return None
    
    async def send_heartbeat(self, status: Dict) -> bool:
        """
        发送心跳
        
        Args:
            status: 客户端状态
        
        Returns:
            是否成功
        """
        try:
            response = await self.client.post('/api/v1/heartbeat', json={
                'agent_id': self.agent_id,
                'status': status,
                'timestamp': datetime.now().isoformat()
            })
            
            return response.status_code == 200
        
        except Exception as e:
            logger.error(f"心跳发送失败: {e}")
            return False
    
    async def report_error(self, error: Dict) -> bool:
        """
        上报错误
        
        Args:
            error: 错误信息
        
        Returns:
            是否成功
        """
        try:
            response = await self.client.post('/api/v1/errors', json={
                'agent_id': self.agent_id,
                'error': error,
                'timestamp': datetime.now().isoformat()
            })
            
            return response.status_code == 200
        
        except Exception as e:
            logger.error(f"错误上报失败: {e}")
            return False
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
        logger.info("服务器客户端已关闭")

