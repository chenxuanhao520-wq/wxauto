#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信UI自动化模块 - 客户端核心
只负责抓取和发送消息，不做任何业务处理
"""

import logging
import uuid
import hashlib
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WxAutomation:
    """微信UI自动化 - 轻量级封装"""
    
    def __init__(self, whitelisted_groups: list = None):
        """
        初始化微信自动化
        
        Args:
            whitelisted_groups: 白名单群聊列表，如果为 None 则使用测试模式
        """
        self.wx = None
        
        try:
            if whitelisted_groups:
                # ✅ 修复：传递必需的 whitelisted_groups 参数
                from modules.adapters.wxauto_adapter import WxAutoAdapter
                self.wx = WxAutoAdapter(whitelisted_groups=whitelisted_groups)
                logger.info("✅ 微信自动化初始化成功")
            else:
                # 测试模式：使用假适配器
                from modules.adapters.wxauto_adapter import FakeWxAdapter
                self.wx = FakeWxAdapter(whitelisted_groups=["测试群"])
                logger.info("✅ 微信自动化初始化成功（测试模式）")
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
            # ✅ 修复：调用底层适配器的 iter_new_messages()
            formatted_messages = []
            
            for msg in self.wx.iter_new_messages():
                # msg 是 Message 对象（来自 wxauto_adapter）
                # 生成消息 ID
                content_for_hash = f"{msg.group_id}:{msg.timestamp.isoformat()}:{msg.content}"
                msg_id = hashlib.md5(content_for_hash.encode()).hexdigest()
                
                formatted_messages.append({
                    'id': msg_id,
                    'chat_id': msg.group_id,
                    'sender': msg.sender_name,
                    'content': msg.content,
                    'type': 'text',
                    'timestamp': msg.timestamp.isoformat(),
                    'is_group': True,
                    'is_at_me': msg.is_at_me
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
            # ✅ 修复：调用适配器的 send_text 方法
            success = self.wx.send_text(group_name=chat_id, text=content)
            if success:
                logger.info(f"✅ 消息已发送: {chat_id[:10]}...")
            return success
        
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

