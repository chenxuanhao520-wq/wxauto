"""
AI 网关：智能路由 + 主备切换 + 自动降级
支持多个大模型提供商，根据任务复杂度智能选择最优模型
"""
import os
import logging
import asyncio
from typing import Optional, List, Dict, Any

from .types import LLMRequest, LLMResponse, ProviderConfig
from .providers import (
    OpenAIProvider,
    DeepSeekProvider,
    ClaudeProvider,
    QwenProvider,
    GLMProvider,
    ErnieProvider,
    GeminiProvider,
    MoonshotProvider
)
from .base import BaseLLMProvider

logger = logging.getLogger(__name__)

# 尝试导入智能路由器
try:
    from .smart_router import SmartModelRouter
    SMART_ROUTER_AVAILABLE = True
except ImportError:
    SMART_ROUTER_AVAILABLE = False
    SmartModelRouter = None


class AIGateway:
    """
    AI 网关
    
    功能：
    1. 智能路由：根据问题复杂度自动选择最优模型
    2. 主备切换：主模型失败自动降级备用模型
    3. 成本优化：简单问题用便宜模型，复杂问题用强模型
    4. 多提供商：支持7个大模型提供商
    """
    
    def __init__(
        self,
        primary_provider: str = "qwen",
        primary_model: str = "qwen-turbo",
        fallback_provider: Optional[str] = "deepseek",
        fallback_model: str = "deepseek-chat",
        enable_fallback: bool = True,
        enable_smart_routing: bool = True
    ):
        """
        初始化AI网关
        
        Args:
            primary_provider: 主要提供商 (qwen | deepseek | openai等)
            primary_model: 主要模型
            fallback_provider: 备用提供商
            fallback_model: 备用模型
            enable_fallback: 是否启用备用降级
            enable_smart_routing: 是否启用智能路由
        """
        self.enable_fallback = enable_fallback
        self.enable_smart_routing = enable_smart_routing
        
        # 初始化智能路由器
        if enable_smart_routing and SMART_ROUTER_AVAILABLE:
            self.router = SmartModelRouter()
            logger.info("✅ 智能路由器已启用")
        else:
            self.router = None
            if enable_smart_routing and not SMART_ROUTER_AVAILABLE:
                logger.warning("⚠️ 智能路由器不可用，使用传统主备模式")
        
        # 初始化所有可用的提供商实例（用于智能路由）
        self.all_providers: Dict[str, BaseLLMProvider] = {}
        if enable_smart_routing:
            self._init_all_providers()
        
        # 初始化传统主备提供商列表
        self.providers: List[BaseLLMProvider] = []
        
        # 初始化主提供商
        primary = self._create_provider(primary_provider, primary_model)
        if primary and primary.is_available():
            self.providers.append(primary)
            logger.info(f"主提供商已加载: {primary_provider}/{primary_model}")
        else:
            logger.warning(f"主提供商不可用: {primary_provider}")
        
        # 初始化备用提供商
        if enable_fallback and fallback_provider:
            fallback = self._create_provider(fallback_provider, fallback_model)
            if fallback and fallback.is_available():
                self.providers.append(fallback)
                logger.info(f"备用提供商已加载: {fallback_provider}/{fallback_model}")
            else:
                logger.warning(f"备用提供商不可用: {fallback_provider}")
        
        if not self.providers:
            logger.error("没有可用的 LLM 提供商，将使用桩实现")
    
    def _init_all_providers(self):
        """初始化所有可用的提供商（用于智能路由）"""
        provider_configs = {
            'qwen-turbo': ('qwen', 'qwen-turbo'),
            'qwen-plus': ('qwen', 'qwen-plus'),
            'qwen-max': ('qwen', 'qwen-max'),
            'deepseek': ('deepseek', 'deepseek-chat')
        }
        
        for key, (provider, model) in provider_configs.items():
            try:
                provider_instance = self._create_provider(provider, model)
                if provider_instance and provider_instance.is_available():
                    self.all_providers[key] = provider_instance
                    logger.debug(f"提供商已注册: {key}")
            except Exception as e:
                logger.warning(f"提供商注册失败 {key}: {e}")
    
    async def generate(
        self,
        user_message: str,
        evidence_context: Optional[str] = None,
        session_history: Optional[List] = None,
        max_tokens: int = 512,
        temperature: float = 0.3,
        prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        生成响应（支持智能路由和自动降级）
        
        Args:
            user_message: 用户消息
            evidence_context: 证据上下文
            session_history: 会话历史
            max_tokens: 最大 token 数
            temperature: 温度参数
            prompt: 完整提示词（如果提供，优先使用）
            metadata: 元数据（用于智能路由决策）
        
        Returns:
            LLMResponse: 响应结果
        """
        metadata = metadata or {}
        
        # 如果启用智能路由，先选择最优模型
        selected_provider = None
        routing_info = None
        
        if self.enable_smart_routing and self.router:
            try:
                routing_info = await self.router.route(
                    question=user_message,
                    context=evidence_context,
                    metadata=metadata
                )
                
                model_key = routing_info['model_key']
                
                if model_key in self.all_providers:
                    selected_provider = self.all_providers[model_key]
                    logger.info(
                        f"🎯 智能路由选择: {model_key} "
                        f"(复杂度={routing_info.get('complexity', 0):.2f}, "
                        f"原因={routing_info.get('reason', '')})"
                    )
                else:
                    logger.warning(f"路由选择的模型不可用: {model_key}，使用默认")
                
            except Exception as e:
                logger.error(f"智能路由失败: {e}，使用默认提供商")
        
        # 构建请求
        request = LLMRequest(
            user_message=user_message,
            evidence_context=evidence_context,
            session_history=session_history,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # 如果智能路由选择了模型，优先尝试
        if selected_provider:
            try:
                # ✅ 修复异步阻塞：使用 asyncio.to_thread 包装同步调用
                response = await asyncio.to_thread(selected_provider.generate, request)
                
                if response.content and not response.error:
                    # 添加路由信息到响应
                    if routing_info:
                        response.routing_info = routing_info
                    return response
                else:
                    logger.warning(
                        f"智能路由选择的模型失败: {selected_provider.name}, "
                        f"error={response.error}，尝试降级"
                    )
            
            except Exception as e:
                logger.error(f"智能路由模型调用异常: {selected_provider.name}, {e}，尝试降级")
        
        # 降级：依次尝试主备提供商
        for i, provider in enumerate(self.providers):
            is_fallback = i > 0
            
            try:
                logger.info(
                    f"调用 {'备用' if is_fallback else '主'} 提供商: {provider.name}"
                )
                
                # ✅ 修复异步阻塞：使用 asyncio.to_thread 包装同步调用
                response = await asyncio.to_thread(provider.generate, request)
                
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
    
    def _create_provider(
        self,
        provider_name: str,
        model_name: Optional[str] = None
    ) -> Optional[BaseLLMProvider]:
        """
        创建提供商实例
        
        Args:
            provider_name: 提供商名称
            model_name: 模型名称（如果指定，覆盖环境变量）
        """
        try:
            # 模型映射（支持智能路由的多模型）
            model_overrides = {
                'qwen-turbo': 'qwen-turbo',
                'qwen-plus': 'qwen-plus',
                'qwen-max': 'qwen-max',
                'deepseek-chat': 'deepseek-chat'
            }
            
            provider_configs = {
                "openai": {
                    "class": OpenAIProvider,
                    "config": ProviderConfig(
                        name="openai",
                        api_key=os.getenv("OPENAI_API_KEY", ""),
                        api_base=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
                        model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                        timeout=int(os.getenv("OPENAI_TIMEOUT", "30"))
                    )
                },
                "deepseek": {
                    "class": DeepSeekProvider,
                    "config": ProviderConfig(
                        name="deepseek",
                        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
                        api_base=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"),
                        model=model_name or os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                        timeout=int(os.getenv("DEEPSEEK_TIMEOUT", "30"))
                    )
                },
                "claude": {
                    "class": ClaudeProvider,
                    "config": ProviderConfig(
                        name="claude",
                        api_key=os.getenv("CLAUDE_API_KEY", ""),
                        api_base=os.getenv("CLAUDE_API_BASE", ""),
                        model=model_name or os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
                        timeout=int(os.getenv("CLAUDE_TIMEOUT", "60"))
                    )
                },
                "qwen": {
                    "class": QwenProvider,
                    "config": ProviderConfig(
                        name="qwen",
                        api_key=os.getenv("QWEN_API_KEY", ""),
                        api_base=os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
                        model=model_name or os.getenv("QWEN_MODEL", "qwen-turbo"),
                        timeout=int(os.getenv("QWEN_TIMEOUT", "30"))
                    )
                },
                "ernie": {
                    "class": ErnieProvider,
                    "config": ProviderConfig(
                        name="ernie",
                        api_key=os.getenv("ERNIE_API_KEY", ""),  # 格式: client_id:client_secret
                        api_base=os.getenv("ERNIE_API_BASE", ""),
                        model=model_name or os.getenv("ERNIE_MODEL", "ernie-4.0"),
                        timeout=int(os.getenv("ERNIE_TIMEOUT", "30"))
                    )
                },
                "gemini": {
                    "class": GeminiProvider,
                    "config": ProviderConfig(
                        name="gemini",
                        api_key=os.getenv("GEMINI_API_KEY", ""),
                        api_base=os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta/openai/"),
                        model=model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
                        timeout=int(os.getenv("GEMINI_TIMEOUT", "30"))
                    )
                },
                "moonshot": {
                    "class": MoonshotProvider,
                    "config": ProviderConfig(
                        name="moonshot",
                        api_key=os.getenv("MOONSHOT_API_KEY", ""),
                        api_base=os.getenv("MOONSHOT_API_BASE", "https://api.moonshot.cn/v1"),
                        model=model_name or os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k"),
                        timeout=int(os.getenv("MOONSHOT_TIMEOUT", "30"))
                    )
                },
                "glm": {
                    "class": GLMProvider,
                    "config": ProviderConfig(
                        name="glm",
                        api_key=os.getenv("GLM_API_KEY", ""),
                        api_base=os.getenv("GLM_API_BASE", "https://open.bigmodel.cn/api/paas/v4"),
                        model=model_name or os.getenv("GLM_MODEL", "glm-4-flash"),
                        timeout=int(os.getenv("GLM_TIMEOUT", "30"))
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
            "available": len(self.providers) > 0,
            "smart_routing_enabled": self.enable_smart_routing and self.router is not None,
            "total_providers": len(self.all_providers) if self.all_providers else len(self.providers)
        }
        
        # 主备提供商状态
        for provider in self.providers:
            status["providers"].append({
                "name": provider.name,
                "available": provider.is_available(),
                "type": "primary" if provider == self.providers[0] else "fallback"
            })
        
        # 智能路由提供商状态
        if self.all_providers:
            status["routing_providers"] = [
                {
                    "key": key,
                    "name": provider.name,
                    "available": provider.is_available()
                }
                for key, provider in self.all_providers.items()
            ]
        
        return status
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        if not self.router:
            return {"smart_routing_enabled": False}
        
        return {
            "smart_routing_enabled": True,
            "router_stats": self.router.get_model_stats()
        }

