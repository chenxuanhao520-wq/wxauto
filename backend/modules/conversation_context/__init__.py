#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能对话上下文管理模块
提供高效的上下文管理，降低token消耗
"""

from .context_manager import (
    ContextManager,
    IntentClassifier,
    TopicChangeDetector,
    ContextCompressor,
    DialogueType,
    CONTEXT_WINDOW_SIZE
)

from .session_lifecycle import (
    SessionLifecycleManager,
    SessionConfig,
    SessionState
)

__all__ = [
    # 上下文管理
    'ContextManager',
    'IntentClassifier',
    'TopicChangeDetector',
    'ContextCompressor',
    'DialogueType',
    'CONTEXT_WINDOW_SIZE',
    
    # 会话生命周期
    'SessionLifecycleManager',
    'SessionConfig',
    'SessionState'
]

__version__ = '1.1.0'

