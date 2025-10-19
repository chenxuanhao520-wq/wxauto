#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心业务模块
提供系统的核心功能：对话追踪、客户管理、智能分析等
"""

from .conversation_tracker import ConversationTracker, ConversationOutcome
from .customer_manager import customer_manager, init_default_groups
from .sync_manager import sync_manager
from .config_loader import get_config, reload_config, SystemConfig
from .system_integrator import WxAutoSystem
from .system_monitor import SystemMonitor, get_system_monitor
from .error_handler import ErrorHandler, get_error_handler, ErrorCategory
from .performance_optimizer import CacheManager, DatabaseOptimizer, get_cache

# 可选模块（需要额外依赖）
try:
    from .smart_analyzer import smart_analyzer
except ImportError:
    smart_analyzer = None

__all__ = [
    # 对话追踪
    'ConversationTracker',
    'ConversationOutcome',
    
    # 客户管理
    'customer_manager',
    'init_default_groups',
    
    # 同步管理
    'sync_manager',
    
    # 配置管理
    'get_config',
    'reload_config',
    'SystemConfig',
    
    # 系统集成器
    'WxAutoSystem',
    
    # 系统监控
    'SystemMonitor',
    'get_system_monitor',
    
    # 错误处理
    'ErrorHandler',
    'get_error_handler',
    'ErrorCategory',
    
    # 性能优化
    'CacheManager',
    'DatabaseOptimizer',
    'get_cache',
    
    # 智能分析（可选）
    'smart_analyzer',
]

__version__ = '2.0.0'
__author__ = 'WxAuto Team'

