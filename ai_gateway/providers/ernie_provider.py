"""
百度文心一言提供商
支持：ernie-4.0, ernie-3.5, ernie-speed
"""
import time
import logging
from typing import List, Dict

from ..base import BaseLLMProvider
from ..types import LLMRequest, LLMResponse, ProviderConfig

logger = logging.getLogger(__name__)


class ErnieProvider(BaseLLMProvider):
    """百度文心一言提供商"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        
        try:
            import requests
            self.session = requests.Session()
            self.api_key = config.api_key
            # 文心一言需要先获取 access_token
            self.access_token = None
            self._get_access_token()
            logger.info("文心一言客户端初始化成功")
        except Exception as e:
            logger.error(f"文心一言客户端初始化失败: {e}")
            raise
    
    def _get_access_token(self):
        """获取访问令牌"""
        try:
            import requests
            # API Key 格式: {client_id}:{client_secret}
            if ':' in self.api_key:
                client_id, client_secret = self.api_key.split(':', 1)
            else:
                logger.warning("文心一言 API Key 格式应为 client_id:client_secret")
                return
            
            url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}"
            response = requests.post(url)
            result = response.json()
            
            if 'access_token' in result:
                self.access_token = result['access_token']
                logger.info("文心一言 access_token 获取成功")
            else:
                logger.error(f"文心一言 access_token 获取失败: {result}")
        except Exception as e:
            logger.error(f"获取文心一言 access_token 失败: {e}")
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """调用文心一言 API"""
        start_time = time.time()
        
        if not self.access_token:
            return LLMResponse(
                content="",
                provider="ernie",
                model=self.config.model,
                token_in=0,
                token_out=0,
                token_total=0,
                latency_ms=0,
                error="未获取到 access_token"
            )
        
        try:
            import requests
            
            # 根据模型选择 endpoint
            model_endpoints = {
                'ernie-4.0': 'completions_pro',
                'ernie-3.5': 'completions',
                'ernie-speed': 'ernie_speed'
            }
            endpoint = model_endpoints.get(self.config.model, 'completions')
            
            url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{endpoint}?access_token={self.access_token}"
            
            messages = self._build_messages(request)
            
            payload = {
                "messages": messages,
                "max_output_tokens": request.max_tokens,
                "temperature": request.temperature
            }
            
            response = requests.post(url, json=payload, timeout=self.config.timeout)
            result = response.json()
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            if 'result' in result:
                content = result['result']
                token_in = result.get('usage', {}).get('prompt_tokens', 0)
                token_out = result.get('usage', {}).get('completion_tokens', 0)
                token_total = result.get('usage', {}).get('total_tokens', 0)
                
                logger.info(f"文心一言成功: latency={latency_ms}ms, tokens={token_in}/{token_out}/{token_total}")
                
                return LLMResponse(
                    content=content,
                    provider="ernie",
                    model=self.config.model,
                    token_in=token_in,
                    token_out=token_out,
                    token_total=token_total,
                    latency_ms=latency_ms
                )
            else:
                error_msg = result.get('error_msg', str(result))
                logger.error(f"文心一言调用失败: {error_msg}")
                
                return LLMResponse(
                    content="",
                    provider="ernie",
                    model=self.config.model,
                    token_in=0,
                    token_out=0,
                    token_total=0,
                    latency_ms=latency_ms,
                    error=error_msg
                )
            
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(f"文心一言调用失败: {e}")
            
            return LLMResponse(
                content="",
                provider="ernie",
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
        
        # 文心一言的 system 需要特殊处理
        if request.session_history:
            messages.extend(request.session_history)
        
        user_content = request.user_message
        if request.evidence_context:
            user_content = f"参考资料：\n{request.evidence_context}\n\n用户问题：{user_content}"
        
        messages.append({"role": "user", "content": user_content})
        
        return messages

