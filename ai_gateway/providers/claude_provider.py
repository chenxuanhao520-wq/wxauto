"""
Anthropic Claude 提供商
支持：claude-3-5-sonnet, claude-3-opus, claude-3-haiku
"""
import time
import logging
from typing import List, Dict

from ..base import BaseLLMProvider
from ..types import LLMRequest, LLMResponse, ProviderConfig

logger = logging.getLogger(__name__)


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude 提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=config.api_key,
                timeout=config.timeout
            )
            logger.info("Claude 客户端初始化成功")
        except ImportError:
            logger.error("anthropic 库未安装，请运行: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"Claude 客户端初始化失败: {e}")
            raise
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """调用 Claude API"""
        start_time = time.time()
        
        try:
            # Claude API 使用不同的消息格式
            system_prompt = request.system_prompt or "你是专业的技术客服。"
            messages = self._build_messages(request)
            
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                system=system_prompt,
                messages=messages
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            content = response.content[0].text
            finish_reason = response.stop_reason
            
            token_in = response.usage.input_tokens
            token_out = response.usage.output_tokens
            token_total = token_in + token_out
            
            logger.info(f"Claude 成功: latency={latency_ms}ms, tokens={token_in}/{token_out}/{token_total}")
            
            return LLMResponse(
                content=content,
                provider="claude",
                model=self.config.model,
                token_in=token_in,
                token_out=token_out,
                token_total=token_total,
                latency_ms=latency_ms,
                finish_reason=finish_reason
            )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Claude 调用失败: {e}")
            
            return LLMResponse(
                content="",
                provider="claude",
                model=self.config.model,
                token_in=0,
                token_out=0,
                token_total=0,
                latency_ms=latency_ms,
                error=str(e)
            )
    
    def _build_messages(self, request: LLMRequest) -> List[Dict[str, str]]:
        """构建消息列表（Claude 格式）"""
        messages = []
        
        # 添加历史
        if request.session_history:
            messages.extend(request.session_history)
        
        # 用户消息
        user_content = request.user_message
        if request.evidence_context:
            user_content = f"参考资料：\n{request.evidence_context}\n\n用户问题：{user_content}"
        
        messages.append({"role": "user", "content": user_content})
        
        return messages

