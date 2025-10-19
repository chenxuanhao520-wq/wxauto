"""
OpenAI 提供商
支持：gpt-4o, gpt-4o-mini, gpt-4-turbo 等
"""
import time
import logging
from typing import List, Dict

from ..base import BaseLLMProvider
from ..types import LLMRequest, LLMResponse, ProviderConfig

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI 提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=config.api_key,
                base_url=config.api_base,
                timeout=config.timeout
            )
            logger.info("OpenAI 客户端初始化成功")
        except ImportError:
            logger.error("openai 库未安装，请运行: pip install openai")
            raise
        except Exception as e:
            logger.error(f"OpenAI 客户端初始化失败: {e}")
            raise
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """调用 OpenAI API"""
        start_time = time.time()
        
        try:
            messages = self._build_messages(request)
            
            logger.debug(f"OpenAI 请求: model={self.config.model}, messages={len(messages)}")
            
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
            
            logger.info(f"OpenAI 成功: latency={latency_ms}ms, tokens={token_in}/{token_out}/{token_total}")
            
            return LLMResponse(
                content=content,
                provider="openai",
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
            logger.error(f"OpenAI 调用失败: {e}")
            
            return LLMResponse(
                content="",
                provider="openai",
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
        
        system_prompt = request.system_prompt or self._get_default_system_prompt()
        messages.append({"role": "system", "content": system_prompt})
        
        if request.session_history:
            messages.extend(request.session_history)
        
        user_content = request.user_message
        if request.evidence_context:
            user_content = f"参考资料：\n{request.evidence_context}\n\n用户问题：{user_content}"
        
        messages.append({"role": "user", "content": user_content})
        
        return messages
    
    def _get_default_system_prompt(self) -> str:
        """默认系统指令"""
        return """你是一位专业的技术客服，负责解答产品相关问题。

要求：
1. 回答简洁准确，控制在 400 字以内
2. 使用 ① ② ③ 分步骤说明
3. 引用证据时标注文档名和版本
4. 不确定时主动澄清，不可编造信息
5. 语气友好专业，避免过度营销"""

