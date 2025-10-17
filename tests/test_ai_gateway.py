"""
AI 网关测试
测试 OpenAI/DeepSeek 提供商和网关降级逻辑
"""
import pytest
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_gateway.types import LLMRequest, LLMResponse, ProviderConfig
from ai_gateway.llm_provider import OpenAIProvider, DeepSeekProvider
from ai_gateway.gateway import AIGateway


def test_llm_request_creation():
    """测试 LLM 请求创建"""
    request = LLMRequest(
        user_message="测试消息",
        evidence_context="证据内容",
        max_tokens=512,
        temperature=0.3
    )
    
    assert request.user_message == "测试消息"
    assert request.evidence_context == "证据内容"
    assert request.max_tokens == 512
    assert request.temperature == 0.3


def test_llm_response_creation():
    """测试 LLM 响应创建"""
    response = LLMResponse(
        content="测试回复",
        provider="openai",
        model="gpt-4o-mini",
        token_in=10,
        token_out=20,
        token_total=30,
        latency_ms=500
    )
    
    assert response.content == "测试回复"
    assert response.provider == "openai"
    assert response.token_total == 30


def test_provider_config():
    """测试提供商配置"""
    config = ProviderConfig(
        name="test",
        api_key="sk-test",
        api_base="https://api.test.com",
        model="test-model"
    )
    
    assert config.name == "test"
    assert config.enabled is True


def test_gateway_initialization():
    """测试网关初始化"""
    # 不依赖真实 API Key
    gateway = AIGateway(
        primary_provider="openai",
        fallback_provider="deepseek",
        enable_fallback=True
    )
    
    # 即使没有 API Key，网关也应该能初始化
    assert gateway is not None
    assert gateway.enable_fallback is True


def test_gateway_health_check():
    """测试网关健康检查"""
    gateway = AIGateway(
        primary_provider="openai",
        enable_fallback=False
    )
    
    status = gateway.health_check()
    
    assert 'providers' in status
    assert 'available' in status
    assert isinstance(status['providers'], list)


def test_gateway_stub_response():
    """测试网关桩响应"""
    gateway = AIGateway(primary_provider="openai")
    
    # 调用桩响应方法
    response = gateway._stub_response("测试消息")
    
    assert response.provider == "stub"
    assert response.model == "stub"
    assert "AI服务暂时不可用" in response.content or response.error


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="需要 OPENAI_API_KEY 环境变量"
)
def test_openai_provider_real():
    """测试真实 OpenAI 调用（需要 API Key）"""
    config = ProviderConfig(
        name="openai",
        api_key=os.getenv("OPENAI_API_KEY"),
        api_base="https://api.openai.com/v1",
        model="gpt-4o-mini"
    )
    
    provider = OpenAIProvider(config)
    
    request = LLMRequest(
        user_message="你好，请简单回复",
        max_tokens=50
    )
    
    response = provider.generate(request)
    
    assert response.content
    assert response.token_total > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

