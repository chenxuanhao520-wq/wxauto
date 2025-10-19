#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息处理服务 - 核心业务逻辑
集成AI网关、知识库检索、规则引擎等
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'modules'))
sys.path.insert(0, str(project_root / 'core'))

logger = logging.getLogger(__name__)


class MessageService:
    """消息处理服务"""
    
    def __init__(self):
        """初始化服务"""
        logger.info("初始化消息处理服务...")
        
        # 初始化AI网关
        try:
            from modules.ai_gateway.gateway import AIGateway
            self.ai_gateway = AIGateway()
            logger.info("✅ AI网关初始化成功")
        except Exception as e:
            logger.warning(f"⚠️  AI网关初始化失败: {e}")
            self.ai_gateway = None
        
        # 初始化知识库检索
        try:
            from modules.rag.retriever import Retriever
            self.rag = Retriever()
            logger.info("✅ 知识库检索初始化成功")
        except Exception as e:
            logger.warning(f"⚠️  知识库检索初始化失败: {e}")
            self.rag = None
        
        # 初始化客户管理
        try:
            from core.customer_manager import customer_manager
            self.customer_manager = customer_manager
            logger.info("✅ 客户管理初始化成功")
        except Exception as e:
            logger.warning(f"⚠️  客户管理初始化失败: {e}")
            self.customer_manager = None
        
        # 初始化数据库
        try:
            from modules.storage.db import Database
            self.db = Database()
            logger.info("✅ 数据库初始化成功")
        except Exception as e:
            logger.warning(f"⚠️  数据库初始化失败: {e}")
            self.db = None
        
        # 回复缓存（内存缓存，生产环境应使用Redis）
        self.reply_cache = {}
    
    async def process_message(self, agent_id: str, message: Dict) -> Dict:
        """
        处理消息 - 主入口
        
        Args:
            agent_id: 客户端ID
            message: 消息数据
        
        Returns:
            处理结果
        """
        message_id = message.get('id', '')
        content = message.get('content', '')
        
        logger.info(f"处理消息: agent={agent_id}, content={content[:30]}...")
        
        try:
            # 1. 去重检查
            if await self._is_duplicate(message_id):
                logger.debug("重复消息，忽略")
                return {'action': 'ignore'}
            
            # 2. 客户识别（如果可用）
            customer = None
            if self.customer_manager:
                customer = await self._identify_customer(message)
            
            # 3. 规则判断
            rule_result = await self._check_rules(customer, message)
            if rule_result:
                return rule_result
            
            # 4. 知识库检索
            context = ""
            if self.rag:
                context = await self._retrieve_knowledge(content)
            
            # 5. AI生成回复
            if self.ai_gateway:
                reply = await self._generate_reply(content, context)
                
                # 6. 保存到数据库
                await self._save_to_database(agent_id, message, reply)
                
                # 7. 缓存回复
                self.reply_cache[message_id] = reply
                
                return {
                    'action': 'reply',
                    'content': reply['content'],
                    'confidence': reply.get('confidence', 0.0)
                }
            else:
                # AI不可用，使用简单回复
                return {
                    'action': 'reply',
                    'content': '您好，我是AI客服助手，很高兴为您服务！',
                    'confidence': 0.5
                }
        
        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)
            
            # 返回错误提示
            return {
                'action': 'reply',
                'content': '抱歉，系统暂时无法处理您的消息，请稍后再试。',
                'confidence': 0.0
            }
    
    async def _is_duplicate(self, message_id: str) -> bool:
        """检查是否重复消息"""
        # TODO: 实现真正的去重逻辑（从数据库或Redis）
        return False
    
    async def _identify_customer(self, message: Dict) -> Optional[Dict]:
        """识别客户"""
        try:
            sender = message.get('sender', '')
            chat_id = message.get('chat_id', '')
            
            # TODO: 实现客户识别逻辑
            
            return {
                'id': chat_id,
                'name': sender,
                'level': 'normal'
            }
        except Exception as e:
            logger.error(f"客户识别失败: {e}")
            return None
    
    async def _check_rules(self, customer: Optional[Dict], message: Dict) -> Optional[Dict]:
        """检查规则引擎"""
        # TODO: 实现规则引擎
        # 例如：
        # - VIP客户优先处理
        # - 特定关键词转人工
        # - 敏感词过滤
        
        content = message.get('content', '')
        
        # 简单规则示例
        if '人工' in content or '转接' in content:
            return {
                'action': 'transfer_human',
                'content': '正在为您转接人工客服...'
            }
        
        return None
    
    async def _retrieve_knowledge(self, query: str) -> str:
        """知识库检索"""
        try:
            if not self.rag:
                return ""
            
            # 调用知识库检索
            evidences = self.rag.retrieve(query, k=3)
            
            if not evidences:
                return ""
            
            # 组装上下文
            context_parts = []
            for evidence in evidences:
                context_parts.append(f"参考资料: {evidence.content}")
            
            return "\n".join(context_parts)
        
        except Exception as e:
            logger.error(f"知识库检索失败: {e}")
            return ""
    
    async def _generate_reply(self, query: str, context: str) -> Dict:
        """AI生成回复"""
        try:
            if not self.ai_gateway:
                raise Exception("AI网关不可用")
            
            # 构建提示词
            prompt = f"""你是一个专业的客服助手。

{context if context else ''}

用户问题：{query}

请用友好、专业的语气回复用户。"""
            
            # 调用AI网关
            response = self.ai_gateway.chat([
                {'role': 'user', 'content': prompt}
            ])
            
            return {
                'content': response.get('content', ''),
                'confidence': response.get('confidence', 0.0),
                'model': response.get('model', 'unknown')
            }
        
        except Exception as e:
            logger.error(f"AI生成失败: {e}")
            raise
    
    async def _save_to_database(self, agent_id: str, message: Dict, reply: Dict):
        """保存到数据库"""
        if not self.db:
            return
        
        try:
            # TODO: 保存消息和回复到数据库
            pass
        except Exception as e:
            logger.error(f"保存数据库失败: {e}")
    
    async def get_cached_reply(self, message_id: str) -> Optional[Dict]:
        """获取缓存的回复"""
        return self.reply_cache.get(message_id)

