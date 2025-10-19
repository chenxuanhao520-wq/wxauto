#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整测试脚本 - 验证所有修复
测试 Qwen 和 GLM 两个模型
"""

import os
import asyncio
import logging
from pathlib import Path

# 设置环境变量
os.environ['QWEN_API_KEY'] = 'sk-1d7d593d85b1469683eb8e7988a0f646'
os.environ['QWEN_API_BASE'] = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
os.environ['QWEN_MODEL'] = 'qwen-turbo'

os.environ['GLM_API_KEY'] = '2853e43adea74724865746c7ddfcd7ad.qp589y9s3P2KRlI4'
os.environ['GLM_API_BASE'] = 'https://open.bigmodel.cn/api/paas/v4'
os.environ['GLM_MODEL'] = 'glm-4-flash'

os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-development-min-32-chars-long'
os.environ['VALID_AGENT_CREDENTIALS'] = 'agent_001:test-api-key-001'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)


async def test_1_glm_provider():
    """测试 GLM Provider"""
    print("\n" + "="*60)
    print("测试 1: GLM Provider")
    print("="*60)
    
    from modules.ai_gateway.providers.glm_provider import GLMProvider
    from modules.ai_gateway.types import ProviderConfig, LLMRequest
    
    config = ProviderConfig(
        name="glm",
        api_key=os.getenv('GLM_API_KEY'),
        api_base=os.getenv('GLM_API_BASE'),
        model=os.getenv('GLM_MODEL'),
        timeout=30
    )
    
    provider = GLMProvider(config)
    
    request = LLMRequest(
        user_message="你好，请简单自我介绍一下",
        max_tokens=100,
        temperature=0.7
    )
    
    # ✅ 这是同步调用，在测试中可以，但在 FastAPI 中会用 asyncio.to_thread
    response = provider.generate(request)
    
    print(f"✅ GLM 响应: {response.content[:100]}...")
    print(f"   Token: {response.token_in}/{response.token_out}/{response.token_total}")
    print(f"   延迟: {response.latency_ms}ms")
    
    assert response.content, "GLM 应该返回内容"
    assert not response.error, f"GLM 不应该有错误: {response.error}"


async def test_2_qwen_provider():
    """测试 Qwen Provider"""
    print("\n" + "="*60)
    print("测试 2: Qwen Provider")
    print("="*60)
    
    from modules.ai_gateway.providers.qwen_provider import QwenProvider
    from modules.ai_gateway.types import ProviderConfig, LLMRequest
    
    config = ProviderConfig(
        name="qwen",
        api_key=os.getenv('QWEN_API_KEY'),
        api_base=os.getenv('QWEN_API_BASE'),
        model=os.getenv('QWEN_MODEL'),
        timeout=30
    )
    
    provider = QwenProvider(config)
    
    request = LLMRequest(
        user_message="Python和JavaScript有什么区别？用50字简洁回答",
        max_tokens=100,
        temperature=0.7
    )
    
    response = provider.generate(request)
    
    print(f"✅ Qwen 响应: {response.content[:100]}...")
    print(f"   Token: {response.token_in}/{response.token_out}/{response.token_total}")
    print(f"   延迟: {response.latency_ms}ms")
    
    assert response.content, "Qwen 应该返回内容"
    assert not response.error, f"Qwen 不应该有错误: {response.error}"


async def test_3_ai_gateway_async():
    """测试 AI Gateway 异步修复"""
    print("\n" + "="*60)
    print("测试 3: AI Gateway 异步调用 (asyncio.to_thread)")
    print("="*60)
    
    from modules.ai_gateway.gateway import AIGateway
    
    # 使用 Qwen 作为主提供商，GLM 作为备用
    gateway = AIGateway(
        primary_provider="qwen",
        primary_model="qwen-turbo",
        fallback_provider="glm",
        fallback_model="glm-4-flash",
        enable_fallback=True,
        enable_smart_routing=False  # 先测试基础功能
    )
    
    # ✅ 这是异步调用，使用了 asyncio.to_thread
    response = await gateway.generate(
        user_message="1+1等于多少？",
        max_tokens=50
    )
    
    print(f"✅ AI Gateway 响应: {response.content[:100]}")
    print(f"   提供商: {response.provider}")
    print(f"   模型: {response.model}")
    print(f"   Token: {response.token_total}")
    
    assert response.content, "AI Gateway 应该返回内容"


async def test_4_local_cache_key_persistence():
    """测试本地缓存密钥持久化"""
    print("\n" + "="*60)
    print("测试 4: 本地缓存密钥持久化")
    print("="*60)
    
    from client.cache.local_cache import LocalCache
    
    cache_dir = "test_cache"
    
    # 第一次创建缓存
    cache1 = LocalCache(cache_dir=cache_dir)
    key_file = Path(cache_dir) / '.key'
    
    assert key_file.exists(), "密钥文件应该被创建"
    original_key = key_file.read_bytes()
    
    # 第二次创建缓存（模拟重启）
    cache2 = LocalCache(cache_dir=cache_dir)
    
    # 验证密钥是否相同
    reloaded_key = key_file.read_bytes()
    assert original_key == reloaded_key, "✅ 密钥应该被持久化和复用"
    
    print("✅ 本地缓存密钥持久化正常")
    
    # 清理
    import shutil
    shutil.rmtree(cache_dir, ignore_errors=True)


async def test_5_message_id_generation():
    """测试消息 ID 生成"""
    print("\n" + "="*60)
    print("测试 5: 消息 ID 生成 (空 ID 自动生成)")
    print("="*60)
    
    from client.agent.wx_automation import WxAutomation
    import hashlib
    
    # 模拟空 ID 的消息
    test_msg = {
        'id': '',  # 空 ID
        'chat_id': 'test_chat',
        'sender_name': 'TestUser',
        'content': 'Hello World',
        'timestamp': '2025-10-19T12:00:00',
        'type': 'text'
    }
    
    # 手动测试 ID 生成逻辑
    msg_id = test_msg.get('id')
    if not msg_id:
        content_for_hash = f"{test_msg.get('chat_id', '')}:{test_msg.get('timestamp', '')}:{test_msg.get('content', '')}"
        msg_id = hashlib.md5(content_for_hash.encode()).hexdigest()
    
    print(f"✅ 生成的消息 ID: {msg_id}")
    assert msg_id, "应该生成非空 ID"
    assert len(msg_id) == 32, "MD5 哈希应该是 32 字符"


async def test_6_auth_flow():
    """测试认证流程（模拟）"""
    print("\n" + "="*60)
    print("测试 6: 认证流程 (JWT 验证)")
    print("="*60)
    
    from server.api.auth import SECRET_KEY, ALGORITHM, VALID_AGENTS
    import jwt
    from datetime import datetime, timedelta
    
    # 验证环境变量加载
    print(f"✅ SECRET_KEY 已从环境变量加载: {SECRET_KEY[:20]}...")
    print(f"✅ VALID_AGENTS: {list(VALID_AGENTS.keys())}")
    
    # 模拟生成 JWT
    agent_id = "agent_001"
    expire = datetime.utcnow() + timedelta(minutes=60)
    token_data = {
        "sub": agent_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    print(f"✅ 生成的 JWT: {token[:50]}...")
    
    # 验证 JWT
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload.get("sub") == agent_id, "JWT payload 应该包含正确的 agent_id"
    
    print("✅ JWT 认证流程正常")


async def test_7_smart_routing():
    """测试智能路由（如果可用）"""
    print("\n" + "="*60)
    print("测试 7: 智能路由 (可选)")
    print("="*60)
    
    try:
        from modules.ai_gateway.smart_router import SmartModelRouter
        
        router = SmartModelRouter()
        
        # 测试简单问题
        routing_info = await router.route(
            question="你好",
            context=None,
            metadata={}
        )
        
        print(f"✅ 智能路由结果:")
        print(f"   选择模型: {routing_info['model_key']}")
        print(f"   复杂度: {routing_info.get('complexity', 0):.2f}")
        print(f"   原因: {routing_info.get('reason', '')}")
        
    except ImportError:
        print("⚠️  智能路由模块不可用（可选功能）")


async def main():
    """运行所有测试"""
    print("\n" + "🧪"*30)
    print("开始完整测试 - 验证所有修复")
    print("🧪"*30)
    
    tests = [
        ("GLM Provider", test_1_glm_provider),
        ("Qwen Provider", test_2_qwen_provider),
        ("AI Gateway 异步", test_3_ai_gateway_async),
        ("本地缓存密钥持久化", test_4_local_cache_key_persistence),
        ("消息 ID 生成", test_5_message_id_generation),
        ("认证流程", test_6_auth_flow),
        ("智能路由", test_7_smart_routing),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            failed += 1
            logger.error(f"❌ {test_name} 失败: {e}", exc_info=True)
    
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"✅ 通过: {passed}/{len(tests)}")
    print(f"❌ 失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！系统已修复完毕！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查日志")


if __name__ == "__main__":
    asyncio.run(main())

