"""
AI 网关基类
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional
from .types import LLMRequest, LLMResponse, ProviderConfig

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """LLM 提供商基类"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.name = config.name
        logger.info(f"LLM Provider 初始化: {self.name}")
    
    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """
        生成响应
        Args:
            request: LLM 请求
        Returns:
            LLMResponse: 响应结果
        """
        pass
    
    def is_available(self) -> bool:
        """检查提供商是否可用"""
        return self.config.enabled and bool(self.config.api_key)

