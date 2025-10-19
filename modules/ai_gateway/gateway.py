"""
AI 网关：主调用 + 备用降级
支持多个大模型提供商
"""
import os
import logging
from typing import Optional, List

from .types import LLMRequest, LLMResponse, ProviderConfig
from .providers import (
    OpenAIProvider,
    DeepSeekProvider,
    ClaudeProvider,
    QwenProvider,
    ErnieProvider,
    GeminiProvider,
    MoonshotProvider
)
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class AIGateway:
    """
    AI 网关
    支持主备切换、自动降级
    """
    
    def __init__(
        self,
        primary_provider: str = "openai",
        fallback_provider: Optional[str] = "deepseek",
        enable_fallback: bool = True
    ):
        """
        Args:
            primary_provider: 主要提供商 (openai | deepseek)
            fallback_provider: 备用提供商
            enable_fallback: 是否启用备用降级
        """
        self.enable_fallback = enable_fallback
        self.providers: List[BaseLLMProvider] = []
        
        # 初始化主提供商
        primary = self._create_provider(primary_provider)
        if primary and primary.is_available():
            self.providers.append(primary)
            logger.info(f"主提供商已加载: {primary_provider}")
        else:
            logger.warning(f"主提供商不可用: {primary_provider}")
        
        # 初始化备用提供商
        if enable_fallback and fallback_provider:
            fallback = self._create_provider(fallback_provider)
            if fallback and fallback.is_available():
                self.providers.append(fallback)
                logger.info(f"备用提供商已加载: {fallback_provider}")
            else:
                logger.warning(f"备用提供商不可用: {fallback_provider}")
        
        if not self.providers:
            logger.error("没有可用的 LLM 提供商，将使用桩实现")
    
    def generate(
        self,
        user_message: str,
        evidence_context: Optional[str] = None,
        session_history: Optional[List] = None,
        max_tokens: int = 512,
        temperature: float = 0.3
    ) -> LLMResponse:
        """
        生成响应（支持自动降级）
        Args:
            user_message: 用户消息
            evidence_context: 证据上下文
            session_history: 会话历史
            max_tokens: 最大 token 数
            temperature: 温度参数
        Returns:
            LLMResponse: 响应结果
        """
        request = LLMRequest(
            user_message=user_message,
            evidence_context=evidence_context,
            session_history=session_history,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # 依次尝试提供商
        for i, provider in enumerate(self.providers):
            is_fallback = i > 0
            
            try:
                logger.info(
                    f"调用 {'备用' if is_fallback else '主'} 提供商: {provider.name}"
                )
                
                response = provider.generate(request)
                
                # 检查是否成功
                if response.content and not response.error:
                    if is_fallback:
                        logger.warning(f"备用提供商成功: {provider.name}")
                    return response
                else:
                    logger.warning(
                        f"提供商返回错误: {provider.name}, error={response.error}"
                    )
                    continue
                    
            except Exception as e:
                logger.error(f"提供商调用异常: {provider.name}, {e}")
                continue
        
        # 所有提供商都失败，返回桩响应
        logger.error("所有 LLM 提供商都失败，使用桩响应")
        return self._stub_response(user_message)
    
    def _create_provider(self, provider_name: str) -> Optional[BaseLLMProvider]:
        """创建提供商实例"""
        try:
            provider_configs = {
                "openai": {
                    "class": OpenAIProvider,
                    "config": ProviderConfig(
                        name="openai",
                        api_key=os.getenv("OPENAI_API_KEY", ""),
                        api_base=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
                        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                        timeout=int(os.getenv("OPENAI_TIMEOUT", "30"))
                    )
                },
                "deepseek": {
                    "class": DeepSeekProvider,
                    "config": ProviderConfig(
                        name="deepseek",
                        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
                        api_base=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"),
                        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                        timeout=int(os.getenv("DEEPSEEK_TIMEOUT", "30"))
                    )
                },
                "claude": {
                    "class": ClaudeProvider,
                    "config": ProviderConfig(
                        name="claude",
                        api_key=os.getenv("CLAUDE_API_KEY", ""),
                        api_base=os.getenv("CLAUDE_API_BASE", ""),
                        model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
                        timeout=int(os.getenv("CLAUDE_TIMEOUT", "60"))
                    )
                },
                "qwen": {
                    "class": QwenProvider,
                    "config": ProviderConfig(
                        name="qwen",
                        api_key=os.getenv("QWEN_API_KEY", ""),
                        api_base=os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
                        model=os.getenv("QWEN_MODEL", "qwen-max"),
                        timeout=int(os.getenv("QWEN_TIMEOUT", "30"))
                    )
                },
                "ernie": {
                    "class": ErnieProvider,
                    "config": ProviderConfig(
                        name="ernie",
                        api_key=os.getenv("ERNIE_API_KEY", ""),  # 格式: client_id:client_secret
                        api_base=os.getenv("ERNIE_API_BASE", ""),
                        model=os.getenv("ERNIE_MODEL", "ernie-4.0"),
                        timeout=int(os.getenv("ERNIE_TIMEOUT", "30"))
                    )
                },
                "gemini": {
                    "class": GeminiProvider,
                    "config": ProviderConfig(
                        name="gemini",
                        api_key=os.getenv("GEMINI_API_KEY", ""),
                        api_base=os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta/openai/"),
                        model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
                        timeout=int(os.getenv("GEMINI_TIMEOUT", "30"))
                    )
                },
                "moonshot": {
                    "class": MoonshotProvider,
                    "config": ProviderConfig(
                        name="moonshot",
                        api_key=os.getenv("MOONSHOT_API_KEY", ""),
                        api_base=os.getenv("MOONSHOT_API_BASE", "https://api.moonshot.cn/v1"),
                        model=os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k"),
                        timeout=int(os.getenv("MOONSHOT_TIMEOUT", "30"))
                    )
                }
            }
            
            if provider_name not in provider_configs:
                logger.error(f"未知的提供商: {provider_name}")
                return None
            
            provider_info = provider_configs[provider_name]
            return provider_info["class"](provider_info["config"])
                
        except Exception as e:
            logger.error(f"创建提供商失败: {provider_name}, {e}")
            return None
    
    def _stub_response(self, user_message: str) -> LLMResponse:
        """桩响应（兜底）"""
        return LLMResponse(
            content="抱歉，AI服务暂时不可用，已为您转接人工客服。",
            provider="stub",
            model="stub",
            token_in=len(user_message) * 2,
            token_out=50,
            token_total=len(user_message) * 2 + 50,
            latency_ms=0,
            error="All providers failed"
        )
    
    def health_check(self) -> dict:
        """健康检查"""
        status = {
            "providers": [],
            "available": len(self.providers) > 0
        }
        
        for provider in self.providers:
            status["providers"].append({
                "name": provider.name,
                "available": provider.is_available()
            })
        
        return status

