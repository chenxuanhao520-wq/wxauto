#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置加载器
负责加载和管理系统配置，提供类型安全的配置访问
"""

import yaml
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """大模型配置"""
    primary: str = "deepseek:chat"
    fallback: str = "openai:gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30


@dataclass
class ContextConfig:
    """对话上下文配置"""
    max_age_minutes: int = 30
    hard_limit: int = 20
    idle_timeout: int = 5
    dormant_timeout: int = 15
    expire_timeout: int = 30
    send_idle_prompt: bool = True
    custom_timeouts: Dict[str, Dict[str, int]] = field(default_factory=dict)


@dataclass
class ERPConfig:
    """ERP集成配置"""
    enabled: bool = False
    base_url: str = ""
    username: str = ""
    password: str = ""
    customer_source_id: int = 171
    customer_category: str = "微信客户"
    sync_enabled: bool = False
    pull_interval_minutes: int = 60
    push_interval_minutes: int = 30


@dataclass
class KnowledgeBaseConfig:
    """知识库配置"""
    enabled: bool = True
    vector_store_path: str = "data/vector_store"
    embedding_model: str = "bge-m3"
    top_k: int = 3
    score_threshold: float = 0.6


@dataclass
class MultitableConfig:
    """多维表格配置"""
    enabled: bool = False
    platform: str = "feishu"  # feishu | dingtalk
    sync_conversations: bool = True
    sync_messages: bool = False
    sync_interval_hours: int = 1


@dataclass
class SystemConfig:
    """系统配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    context: ContextConfig = field(default_factory=ContextConfig)
    erp: ERPConfig = field(default_factory=ERPConfig)
    knowledge_base: KnowledgeBaseConfig = field(default_factory=KnowledgeBaseConfig)
    multitable: MultitableConfig = field(default_factory=MultitableConfig)
    
    # 系统基础配置
    debug_mode: bool = False
    log_level: str = "INFO"
    database_path: str = "data/data.db"
    
    # 微信适配器配置
    use_wework: bool = False
    humanize_behavior: bool = True
    
    # 安全配置
    max_requests_per_minute: int = 20
    max_messages_per_session: int = 100


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self._raw_config = {}
        self.config = SystemConfig()
        
        if self.config_path.exists():
            self.load()
        else:
            logger.warning(f"配置文件不存在: {config_path}, 使用默认配置")
    
    def load(self) -> SystemConfig:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._raw_config = yaml.safe_load(f) or {}
            
            logger.info(f"配置文件加载成功: {self.config_path}")
            
            # 解析配置
            self.config = self._parse_config(self._raw_config)
            
            # 覆盖环境变量
            self._apply_env_overrides()
            
            return self.config
        
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            return self.config
    
    def _parse_config(self, raw: Dict[str, Any]) -> SystemConfig:
        """解析配置"""
        config = SystemConfig()
        
        # LLM配置
        if 'llm' in raw:
            llm_cfg = raw['llm']
            config.llm = LLMConfig(
                primary=llm_cfg.get('primary', 'deepseek:chat'),
                fallback=llm_cfg.get('fallback', 'openai:gpt-4o-mini'),
                temperature=llm_cfg.get('temperature', 0.7),
                max_tokens=llm_cfg.get('max_tokens', 1000),
                timeout=llm_cfg.get('timeout', 30)
            )
        
        # 上下文配置
        if 'context' in raw:
            ctx_cfg = raw['context']
            config.context = ContextConfig(
                max_age_minutes=ctx_cfg.get('max_age_minutes', 30),
                hard_limit=ctx_cfg.get('hard_limit', 20),
                idle_timeout=ctx_cfg.get('idle_timeout', 5),
                dormant_timeout=ctx_cfg.get('dormant_timeout', 15),
                expire_timeout=ctx_cfg.get('expire_timeout', 30),
                send_idle_prompt=ctx_cfg.get('send_idle_prompt', True),
                custom_timeouts=ctx_cfg.get('custom_timeouts', {})
            )
        
        # ERP配置
        if 'erp_integration' in raw:
            erp_cfg = raw['erp_integration']
            config.erp = ERPConfig(
                enabled=erp_cfg.get('enabled', False),
                base_url=erp_cfg.get('base_url', ''),
                username=erp_cfg.get('username', ''),
                password=erp_cfg.get('password', ''),
                customer_source_id=erp_cfg.get('customer_source_id', 171),
                customer_category=erp_cfg.get('customer_category', '微信客户'),
                sync_enabled=erp_cfg.get('sync', {}).get('enabled', False),
                pull_interval_minutes=erp_cfg.get('sync', {}).get('pull_interval_minutes', 60),
                push_interval_minutes=erp_cfg.get('sync', {}).get('push_interval_minutes', 30)
            )
        
        # 知识库配置
        if 'knowledge_base' in raw:
            kb_cfg = raw['knowledge_base']
            config.knowledge_base = KnowledgeBaseConfig(
                enabled=kb_cfg.get('enabled', True),
                vector_store_path=kb_cfg.get('vector_store_path', 'data/vector_store'),
                embedding_model=kb_cfg.get('embedding_model', 'bge-m3'),
                top_k=kb_cfg.get('top_k', 3),
                score_threshold=kb_cfg.get('score_threshold', 0.6)
            )
        
        # 多维表格配置
        if 'multitable' in raw:
            mt_cfg = raw['multitable']
            config.multitable = MultitableConfig(
                enabled=mt_cfg.get('enabled', False),
                platform=mt_cfg.get('platform', 'feishu'),
                sync_conversations=mt_cfg.get('sync_conversations', True),
                sync_messages=mt_cfg.get('sync_messages', False),
                sync_interval_hours=mt_cfg.get('sync_interval_hours', 1)
            )
        
        # 系统配置
        config.debug_mode = raw.get('debug_mode', False)
        config.log_level = raw.get('log_level', 'INFO')
        config.database_path = raw.get('database_path', 'data/data.db')
        config.use_wework = raw.get('use_wework', False)
        config.humanize_behavior = raw.get('humanize_behavior', True)
        
        return config
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖"""
        # ERP配置
        if os.getenv('ERP_BASE_URL'):
            self.config.erp.base_url = os.getenv('ERP_BASE_URL')
        if os.getenv('ERP_USERNAME'):
            self.config.erp.username = os.getenv('ERP_USERNAME')
        if os.getenv('ERP_PASSWORD'):
            self.config.erp.password = os.getenv('ERP_PASSWORD')
        
        # 调试模式
        if os.getenv('DEBUG'):
            self.config.debug_mode = os.getenv('DEBUG').lower() == 'true'
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号路径）"""
        keys = key.split('.')
        value = self._raw_config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def reload(self):
        """重新加载配置"""
        self.load()
        logger.info("配置已重新加载")


# 全局配置实例
_config_loader = None


def get_config(config_path: str = "config.yaml") -> SystemConfig:
    """
    获取全局配置实例
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        系统配置对象
    """
    global _config_loader
    
    if _config_loader is None:
        _config_loader = ConfigLoader(config_path)
    
    return _config_loader.config


def reload_config():
    """重新加载配置"""
    global _config_loader
    
    if _config_loader is not None:
        _config_loader.reload()


# 使用示例
if __name__ == '__main__':
    # 加载配置
    config = get_config()
    
    print("📊 配置加载测试")
    print("=" * 60)
    print(f"LLM主模型: {config.llm.primary}")
    print(f"LLM备用: {config.llm.fallback}")
    print(f"上下文超时: {config.context.idle_timeout}分钟")
    print(f"ERP启用: {config.erp.enabled}")
    print(f"知识库启用: {config.knowledge_base.enabled}")
    print(f"多维表格: {config.multitable.enabled}")
    print("=" * 60)
    print("✅ 配置加载成功")

