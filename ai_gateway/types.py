"""
AI 网关数据类型定义
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class LLMRequest:
    """LLM 请求"""
    user_message: str
    session_history: Optional[List[Dict[str, str]]] = None
    evidence_context: Optional[str] = None
    system_prompt: Optional[str] = None
    max_tokens: int = 512
    temperature: float = 0.3
    stream: bool = False


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    provider: str
    model: str
    token_in: int
    token_out: int
    token_total: int
    latency_ms: int
    finish_reason: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class ProviderConfig:
    """提供商配置"""
    name: str
    api_key: str
    api_base: str
    model: str
    timeout: int = 30
    max_retries: int = 3
    enabled: bool = True

