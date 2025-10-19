#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统集成器
统一初始化和管理所有模块，提供完整的系统功能
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

# 核心模块
from .config_loader import get_config, SystemConfig
from .conversation_tracker import ConversationTracker
from .customer_manager import customer_manager, init_default_groups

# 功能模块
from modules.storage.db import Database
from modules.ai_gateway.gateway import AIGateway
from modules.rag.retriever import Retriever
from modules.conversation_context import (
    ContextManager,
    SessionLifecycleManager,
    SessionConfig
)
from modules.conversation_context.dialogue_handler_example import SmartDialogueHandler

logger = logging.getLogger(__name__)


class WxAutoSystem:
    """
    微信客服中台系统
    集成所有模块，提供统一的系统接口
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化系统
        
        Args:
            config_path: 配置文件路径
        """
        self.config = get_config(config_path)
        
        # 核心组件
        self.db: Optional[Database] = None
        self.ai_gateway: Optional[AIGateway] = None
        self.retriever: Optional[Retriever] = None
        self.conv_tracker: Optional[ConversationTracker] = None
        
        # 上下文管理
        self.context_mgr: Optional[ContextManager] = None
        self.session_mgr: Optional[SessionLifecycleManager] = None
        self.dialogue_handler: Optional[SmartDialogueHandler] = None
        
        # ERP集成
        self.erp_client: Optional[Any] = None
        
        # 初始化状态
        self.initialized = False
        
        logger.info("系统实例创建完成")
    
    def initialize(self):
        """
        初始化所有组件
        
        按顺序初始化：
        1. 数据库
        2. AI网关
        3. 知识库
        4. 上下文管理
        5. 对话追踪
        6. ERP集成（可选）
        7. 多维表格（可选）
        """
        if self.initialized:
            logger.warning("系统已初始化，跳过")
            return
        
        logger.info("🚀 开始初始化系统...")
        
        try:
            # 1. 初始化数据库
            self._init_database()
            
            # 2. 初始化AI网关
            self._init_ai_gateway()
            
            # 3. 初始化知识库
            self._init_knowledge_base()
            
            # 4. 初始化上下文管理
            self._init_context_management()
            
            # 5. 初始化对话追踪
            self._init_conversation_tracker()
            
            # 6. 初始化ERP集成（可选）
            if self.config.erp.enabled:
                self._init_erp_integration()
            
            # 7. 初始化多维表格（可选）
            if self.config.multitable.enabled:
                self._init_multitable()
            
            # 8. 初始化客户管理器
            self._init_customer_manager()
            
            self.initialized = True
            logger.info("✅ 系统初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 系统初始化失败: {e}", exc_info=True)
            raise
    
    def _init_database(self):
        """初始化数据库"""
        logger.info("📊 初始化数据库...")
        
        # 确保数据目录存在
        db_path = Path(self.config.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.db = Database(str(db_path))
        logger.info(f"✅ 数据库初始化完成: {db_path}")
    
    def _init_ai_gateway(self):
        """初始化AI网关"""
        logger.info("🤖 初始化AI网关...")
        
        self.ai_gateway = AIGateway(
            primary_model=self.config.llm.primary,
            fallback_model=self.config.llm.fallback,
            default_temperature=self.config.llm.temperature,
            default_max_tokens=self.config.llm.max_tokens
        )
        
        logger.info(f"✅ AI网关初始化完成: {self.config.llm.primary}")
    
    def _init_knowledge_base(self):
        """初始化知识库"""
        if not self.config.knowledge_base.enabled:
            logger.info("⏭️  知识库未启用，跳过")
            return
        
        logger.info("📚 初始化知识库...")
        
        try:
            self.retriever = Retriever(
                db=self.db,
                vector_store_path=self.config.knowledge_base.vector_store_path,
                embedding_model=self.config.knowledge_base.embedding_model
            )
            logger.info("✅ 知识库初始化完成")
        except Exception as e:
            logger.warning(f"⚠️  知识库初始化失败: {e}")
            self.retriever = None
    
    def _init_context_management(self):
        """初始化上下文管理"""
        logger.info("🧠 初始化上下文管理...")
        
        # 1. 上下文管理器
        self.context_mgr = ContextManager(
            max_age_minutes=self.config.context.max_age_minutes,
            hard_limit=self.config.context.hard_limit
        )
        
        # 2. 会话生命周期管理器
        session_config = SessionConfig(
            idle_timeout=self.config.context.idle_timeout,
            dormant_timeout=self.config.context.dormant_timeout,
            expire_timeout=self.config.context.expire_timeout,
            send_idle_prompt=self.config.context.send_idle_prompt,
            custom_timeouts=self.config.context.custom_timeouts or {
                '闲聊类': {'idle': 2, 'dormant': 5, 'expire': 10},
                '咨询类': {'idle': 5, 'dormant': 15, 'expire': 30},
                '业务类': {'idle': 10, 'dormant': 20, 'expire': 60}
            }
        )
        
        self.session_mgr = SessionLifecycleManager(
            config=session_config,
            message_sender=self._send_wechat_message
        )
        
        # 启动会话监控
        self.session_mgr.start_monitoring()
        
        # 3. 智能对话处理器
        self.dialogue_handler = SmartDialogueHandler(
            kb_service=self.retriever,
            erp_client=self.erp_client,
            llm_client=self.ai_gateway
        )
        
        logger.info("✅ 上下文管理初始化完成")
    
    def _init_conversation_tracker(self):
        """初始化对话追踪器"""
        logger.info("📈 初始化对话追踪...")
        
        self.conv_tracker = ConversationTracker(self.db)
        
        logger.info("✅ 对话追踪初始化完成")
    
    def _init_erp_integration(self):
        """初始化ERP集成"""
        logger.info("🔧 初始化ERP集成...")
        
        try:
            from modules.erp_sync.zhibang_client_enhanced import ZhibangERPClient
            
            self.erp_client = ZhibangERPClient(
                base_url=self.config.erp.base_url,
                username=self.config.erp.username,
                password=self.config.erp.password,
                auto_login=True
            )
            
            logger.info("✅ ERP集成初始化完成")
        except Exception as e:
            logger.warning(f"⚠️  ERP集成初始化失败: {e}")
            self.erp_client = None
    
    def _init_multitable(self):
        """初始化多维表格"""
        logger.info("📊 初始化多维表格...")
        
        try:
            if self.config.multitable.platform == 'feishu':
                from modules.integrations.feishu_bitable import FeishuBitable
                # 初始化飞书
                logger.info("✅ 飞书多维表格初始化完成")
            elif self.config.multitable.platform == 'dingtalk':
                from modules.integrations.dingtalk_bitable import DingtalkBitable
                # 初始化钉钉
                logger.info("✅ 钉钉多维表格初始化完成")
        except Exception as e:
            logger.warning(f"⚠️  多维表格初始化失败: {e}")
    
    def _init_customer_manager(self):
        """初始化客户管理器"""
        logger.info("👥 初始化客户管理...")
        
        # 初始化默认分组
        init_default_groups(self.db)
        
        logger.info("✅ 客户管理初始化完成")
    
    def _send_wechat_message(self, contact_id: str, message: str):
        """
        发送微信消息（占位函数）
        
        实际使用时需要连接微信适配器
        """
        logger.debug(f"[{contact_id}] 发送消息: {message[:50]}...")
        # TODO: 实际发送逻辑
    
    def process_message(self, contact_id: str, message: str, 
                       metadata: Dict = None) -> Dict:
        """
        处理用户消息（系统主入口）
        
        Args:
            contact_id: 联系人ID
            message: 用户消息
            metadata: 附加元数据
        
        Returns:
            处理结果
        """
        if not self.initialized:
            raise RuntimeError("系统未初始化，请先调用 initialize()")
        
        # 使用智能对话处理器
        result = self.dialogue_handler.process_message(
            contact_id=contact_id,
            message=message,
            metadata=metadata
        )
        
        # 记录到对话追踪器
        # TODO: 补充对话追踪逻辑
        
        return result
    
    def get_statistics(self) -> Dict:
        """获取系统统计信息"""
        stats = {
            'system': {
                'initialized': self.initialized,
                'config_loaded': self.config is not None,
            },
            'database': {
                'connected': self.db is not None,
            },
            'ai_gateway': {
                'available': self.ai_gateway is not None,
                'primary_model': self.config.llm.primary if self.ai_gateway else None,
            },
            'erp': {
                'enabled': self.config.erp.enabled,
                'connected': self.erp_client is not None,
            }
        }
        
        # 添加对话统计
        if self.dialogue_handler:
            try:
                stats['dialogue'] = self.dialogue_handler.get_statistics() if hasattr(self.dialogue_handler, 'get_statistics') else {}
            except:
                pass
        
        return stats
    
    def shutdown(self):
        """关闭系统"""
        logger.info("🛑 关闭系统...")
        
        # 停止会话监控
        if self.session_mgr:
            self.session_mgr.stop_monitoring()
        
        # 清理资源
        if self.dialogue_handler and hasattr(self.dialogue_handler, 'cleanup_and_stop'):
            self.dialogue_handler.cleanup_and_stop()
        
        logger.info("✅ 系统已关闭")


# 使用示例
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # 创建系统实例
    system = WxAutoSystem()
    
    # 初始化
    system.initialize()
    
    # 获取统计
    stats = system.get_statistics()
    print(f"\n系统统计: {stats}")
    
    # 关闭
    system.shutdown()

