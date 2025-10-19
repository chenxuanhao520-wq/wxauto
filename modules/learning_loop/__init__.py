#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能对话闭环学习模块
自动从对话中学习，持续改进系统
"""

from .knowledge_learner import KnowledgeLearner, KnowledgePoint

__all__ = [
    'KnowledgeLearner',
    'KnowledgePoint',
]

__version__ = '1.0.0'
