#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信UI自动化模块 - 客户端核心
只负责抓取和发送消息，不做任何业务处理
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WxAutomation:
    """微信UI自动化 - 轻量级封装"""
    
    def __init__(self):
        """初始化微信自动化"""
        try:
            from modules.adapters.wxauto_adapter import WxAutoAdapter
            self.wx = WxAutoAdapter()
            logger.info("✅ 微信自动化初始化成功")
        except Exception as e:
            logger.error(f"❌ 微信自动化初始化失败: {e}")
            self.wx = None
    
    def get_new_messages(self) -> List[Dict]:
        """
        获取新消息
        
        Returns:
            消息列表，每条消息包含: id, chat_id, sender, content, timestamp
        """
        if not self.wx:
            return []
        
        try:
            # 调用底层适配器
            messages = self.wx.GetAllMessage()
            
            # 转换为统一格式
            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    'id': msg.get('id', ''),
                    'chat_id': msg.get('group_id') or msg.get('sender_id', ''),
                    'sender': msg.get('sender_name', ''),
                    'content': msg.get('content', ''),
                    'type': msg.get('type', 'text'),
                    'timestamp': msg.get('timestamp', datetime.now().isoformat()),
                    'is_group': bool(msg.get('group_id')),
                    'is_at_me': msg.get('is_at_me', False)
                })
            
            return formatted_messages
        
        except Exception as e:
            logger.error(f"获取消息失败: {e}")
            return []
    
    def send_message(self, chat_id: str, content: str) -> bool:
        """
        发送消息
        
        Args:
            chat_id: 聊天ID（群ID或好友ID）
            content: 消息内容
        
        Returns:
            是否发送成功
        """
        if not self.wx:
            logger.error("微信自动化未初始化")
            return False
        
        try:
            self.wx.SendMsg(content, chat_id)
            logger.info(f"✅ 消息已发送: {chat_id[:10]}...")
            return True
        
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False
    
    def get_screenshot(self, chat_id: str) -> Optional[bytes]:
        """
        截图功能（用于OCR触发）
        
        Args:
            chat_id: 聊天窗口ID
        
        Returns:
            截图的二进制数据
        """
        try:
            # TODO: 实现截图功能
            logger.warning("截图功能待实现")
            return None
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
    
    def get_status(self) -> Dict:
        """
        获取微信状态
        
        Returns:
            状态信息: online, version等
        """
        if not self.wx:
            return {'online': False, 'error': '微信未初始化'}
        
        return {
            'online': True,
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat()
        }

