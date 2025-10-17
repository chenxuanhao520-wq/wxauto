"""
DeepSeek 提供商
支持：deepseek-chat, deepseek-coder
"""
import time
import logging
from typing import List, Dict

from ..base import BaseLLMProvider
from ..types import LLMRequest, LLMResponse, ProviderConfig

logger = logging.getLogger(__name__)


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek 提供商（兼容 OpenAI API）"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=config.api_key,
                base_url=config.api_base,
                timeout=config.timeout
            )
            logger.info("DeepSeek 客户端初始化成功")
        except ImportError:
            logger.error("openai 库未安装")
            raise
        except Exception as e:
            logger.error(f"DeepSeek 客户端初始化失败: {e}")
            raise
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """调用 DeepSeek API"""
        start_time = time.time()
        
        try:
            messages = self._build_messages(request)
            
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stream=request.stream
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            
            token_in = response.usage.prompt_tokens if response.usage else 0
            token_out = response.usage.completion_tokens if response.usage else 0
            token_total = response.usage.total_tokens if response.usage else 0
            
            logger.info(f"DeepSeek 成功: latency={latency_ms}ms, tokens={token_in}/{token_out}/{token_total}")
            
            return LLMResponse(
                content=content,
                provider="deepseek",
                model=self.config.model,
                token_in=token_in,
                token_out=token_out,
                token_total=token_total,
                latency_ms=latency_ms,
                finish_reason=finish_reason,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"DeepSeek 调用失败: {e}")
            
            return LLMResponse(
                content="",
                provider="deepseek",
                model=self.config.model,
                token_in=0,
                token_out=0,
                token_total=0,
                latency_ms=latency_ms,
                error=str(e)
            )
    
    def _build_messages(self, request: LLMRequest) -> List[Dict[str, str]]:
        """构建消息列表"""
        messages = []
        
        system_prompt = request.system_prompt or "你是专业的技术客服，简洁准确回答问题。"
        messages.append({"role": "system", "content": system_prompt})
        
        if request.session_history:
            messages.extend(request.session_history)
        
        user_content = request.user_message
        if request.evidence_context:
            user_content = f"参考资料：\n{request.evidence_context}\n\n用户问题：{user_content}"
        
        messages.append({"role": "user", "content": user_content})
        
        return messages

