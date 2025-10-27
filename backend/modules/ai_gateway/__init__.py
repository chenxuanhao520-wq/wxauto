"""
AI Gateway模块
支持智能路由、多提供商、自动降级、首轮判断
"""
from .gateway import AIGateway
from .types import LLMRequest, LLMResponse, ProviderConfig

# 智能路由器（可选）
try:
    from .smart_router import SmartModelRouter
    from .first_turn_router import FirstTurnRouter, FirstTurnDecision
    __all__ = [
        'AIGateway',
        'SmartModelRouter',
        'FirstTurnRouter',
        'FirstTurnDecision',
        'LLMRequest',
        'LLMResponse',
        'ProviderConfig'
    ]
except ImportError:
    __all__ = ['AIGateway', 'LLMRequest', 'LLMResponse', 'ProviderConfig']

__version__ = '2.1.0'