#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 GLM 和 Qwen 模型的自我介绍
"""
import os
import asyncio
import logging

# 设置环境变量
os.environ['QWEN_API_KEY'] = 'sk-1d7d593d85b1469683eb8e7988a0f646'
os.environ['QWEN_API_BASE'] = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
os.environ['QWEN_MODEL'] = 'qwen-turbo'

os.environ['GLM_API_KEY'] = '2853e43adea74724865746c7ddfcd7ad.qp589y9s3P2KRlI4'
os.environ['GLM_API_BASE'] = 'https://open.bigmodel.cn/api/paas/v4'
os.environ['GLM_MODEL'] = 'glm-4-flash'

logging.basicConfig(
    level=logging.WARNING,  # 减少日志输出
    format='%(message)s'
)

logger = logging.getLogger(__name__)


async def test_glm_identity():
    """测试 GLM 的自我认知"""
    print("\n" + "="*70)
    print("测试 1: GLM (智谱AI) - 你是什么模型？")
    print("="*70)
    
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
        user_message="你是什么模型？请详细介绍一下你自己。",
        max_tokens=300,
        temperature=0.7
    )
    
    response = await asyncio.to_thread(provider.generate, request)
    
    print(f"\n📍 模型: {response.model}")
    print(f"⏱️  延迟: {response.latency_ms}ms")
    print(f"🎫 Token: {response.token_in} (输入) / {response.token_out} (输出) / {response.token_total} (总计)")
    print(f"\n💬 GLM 回复:\n")
    print("-" * 70)
    print(response.content)
    print("-" * 70)


async def test_qwen_identity():
    """测试 Qwen 的自我认知"""
    print("\n" + "="*70)
    print("测试 2: Qwen (通义千问) - 你是什么模型？")
    print("="*70)
    
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
        user_message="你是什么模型？请详细介绍一下你自己。",
        max_tokens=300,
        temperature=0.7
    )
    
    response = await asyncio.to_thread(provider.generate, request)
    
    print(f"\n📍 模型: {response.model}")
    print(f"⏱️  延迟: {response.latency_ms}ms")
    print(f"🎫 Token: {response.token_in} (输入) / {response.token_out} (输出) / {response.token_total} (总计)")
    print(f"\n💬 Qwen 回复:\n")
    print("-" * 70)
    print(response.content)
    print("-" * 70)


async def compare_models():
    """对比两个模型"""
    print("\n" + "="*70)
    print("测试 3: 模型对比")
    print("="*70)
    
    print("\n📊 性能对比:")
    print("-" * 70)
    print(f"{'指标':<15} {'GLM-4-flash':<25} {'Qwen-turbo':<25}")
    print("-" * 70)
    print(f"{'提供商':<15} {'智谱AI':<25} {'阿里云':<25}")
    print(f"{'定位':<15} {'免费快速模型':<25} {'免费通用模型':<25}")
    print(f"{'价格':<15} {'免费':<25} {'有免费额度':<25}")
    print(f"{'速度':<15} {'⚡⚡⚡ 极快':<25} {'⚡⚡ 快':<25}")
    print(f"{'适用场景':<15} {'简单对话、快速问答':<25} {'通用对话、技术支持':<25}")


async def main():
    """主测试流程"""
    print("\n" + "🤖"*35)
    print("模型身份测试 - 你是什么模型？")
    print("🤖"*35)
    
    # 测试 GLM
    await test_glm_identity()
    
    # 等待一下
    await asyncio.sleep(1)
    
    # 测试 Qwen
    await test_qwen_identity()
    
    # 对比
    await compare_models()
    
    print("\n" + "="*70)
    print("🎉 测试完成！")
    print("="*70)
    print("\n两个模型都可以正常使用！")
    print("现在您可以根据场景选择合适的模型：")
    print("  • GLM-4-flash: 速度快、免费、适合简单对话")
    print("  • Qwen-turbo: 通用性强、免费额度、适合技术支持")
    print("")


if __name__ == "__main__":
    asyncio.run(main())

